from mlb_rankings import *
import numpy as np
import pandas as pd
from typing import Iterable, Tuple, Literal, Dict, List, Union
from functools import reduce
from statsmodels.tsa.stattools import grangercausalitytests
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.cluster import KMeans
from hmmlearn.hmm import GaussianHMM


Mode = Literal["power", "mlb", "diff", "both"]

def build_plot_table(
    power: pd.DataFrame,
    standings: pd.DataFrame,
    team_names: Dict[str, str],
    team_codes: Dict[str, str],
    selected_codes: List[str],
    mode: Mode = "power",
) -> pd.DataFrame:
    """
    Build a wide table for plotting lines per team according to `mode`.

    Parameters
    ----------
    power : DataFrame with ['date','team','rank']  # 'team' = display name
    standings : DataFrame with ['date','team_name','mlb_rank']  # 'team_name' = team id
    teams : {team_id -> display_name}
    team_names : list of team codes to include
    mode : 'power' | 'mlb' | 'diff' | 'both'
        - 'power': one column per team "<Team> — Power Rank"
        - 'mlb'  : one column per team "<Team> — MLB Rank"
        - 'diff' : one column per team "<Team> — Δ"
        - 'both' : two columns per team:
                   "<Team> — Power Rank" and "<Team> — MLB Rank"
    team_codes : {team_id -> code} list of team codes because team names will be passed as codes

    Returns
    -------
    DataFrame: ['date', series...], sorted by date.
    """
    if mode not in {"power", "mlb", "diff", "both"}:
        raise ValueError("mode must be 'power', 'mlb', 'diff', or 'both'")

    req_p = {"date", "team", "rank"}
    req_s = {"date", "team_name", "mlb_rank"}
    if not req_p.issubset(power.columns):
        raise ValueError(f"'power' missing: {req_p - set(power.columns)}")
    if not req_s.issubset(standings.columns):
        raise ValueError(f"'standings' missing: {req_s - set(standings.columns)}")

    name_to_id = {v: k for k, v in team_names.items()}

    pwr = power.copy()
    std = standings.copy()
    pwr["date"] = pd.to_datetime(pwr["date"])
    std["date"] = pd.to_datetime(std["date"])

    series_frames = []
    date_base = None

    for team_code in selected_codes:
        # convert from code to display name
        team_id = None
        for k, v in team_codes.items():
            if v == team_code:
                team_id = k
                break
        team_display = team_names.get(team_id)
        if team_display not in name_to_id:
            raise KeyError(f"Unknown team display name: {team_display}")
        team_id = name_to_id[team_display]

        p = (pwr.loc[pwr["team"] == team_display, ["date", "rank"]]
                .sort_values("date")
                .rename(columns={"rank": "power"}))
        s = (std.loc[std["team_name"] == team_id, ["date", "mlb_rank"]]
                .sort_values("date"))

        if mode == "power":
            col = f"{team_display} — Power Rank"
            sf = p.rename(columns={"power": col})[["date", col]]

        elif mode == "mlb":
            col = f"{team_display} — MLB Rank"
            sf = s.rename(columns={"mlb_rank": col})[["date", col]]

        elif mode == "diff":
            m = p.merge(s, on="date", how="left").dropna(subset=["mlb_rank"])
            col = f"{team_display} — Δ"
            sf = m.assign(**{col: m["power"] - m["mlb_rank"]})[["date", col]]

        else:  # mode == "both"
            m = p.merge(s, on="date", how="outer").sort_values("date")
            col_power = f"{team_display} — Power Rank"
            col_mlb   = f"{team_display} — MLB Rank"
            sf = m.rename(columns={"power": col_power, "mlb_rank": col_mlb})[["date", col_power, col_mlb]]

        if date_base is None:
            date_base = sf[["date"]].drop_duplicates()
        series_frames.append(sf)

    if not series_frames:
        return pd.DataFrame(columns=["date"]).astype({"date": "datetime64[ns]"})

    wide = reduce(lambda a, b: a.merge(b, on="date", how="outer"), [date_base] + series_frames)
    return wide.sort_values("date").reset_index(drop=True)


Source = Literal["power", "mlb"]

# -------------------------------------------------------------------
# KDE core (compute only, no pandas)
# -------------------------------------------------------------------
def kde_gaussian_1d(samples: np.ndarray, grid: np.ndarray, bandwidth: float | None = None) -> np.ndarray:
    samples = np.asarray(samples, dtype=float)
    n = len(samples)
    if n == 0:
        return np.zeros_like(grid)

    std = np.std(samples, ddof=1) if n > 1 else 0.0
    if bandwidth is None:
        bandwidth = 1.06 * max(std, 1e-8) * n ** (-1/5)  # Silverman
    bandwidth = max(float(bandwidth), 0.3)               # floor

    u = (grid[:, None] - samples[None, :]) / bandwidth
    kernel_vals = np.exp(-0.5 * u**2) / np.sqrt(2 * np.pi)
    return kernel_vals.mean(axis=1) / bandwidth


# -------------------------------------------------------------------
# Helpers to pull the rank time series by source, keyed by team_id
# -------------------------------------------------------------------
def _rank_series_for_team(
    power: pd.DataFrame,
    standings: pd.DataFrame,
    team_id: str,
    team_names: Dict[str, str],
    source: Source,                # "power" or "mlb"
) -> pd.Series:
    """
    Returns a time-ordered rank series (pd.Series) for a given team_id, using source:
      - 'power' -> from power['rank'] filtered by display name
      - 'mlb'   -> from standings['mlb_rank'] filtered by team_id
    Index is datetime (date), name is 'rank'.
    """
    if source == "power":
        team_name = team_names.get(team_id)
        if team_name is None:
            raise KeyError(f"team_id '{team_id}' not found in team_names")
        df = power.loc[power["team"] == team_name, ["date", "rank"]].copy()
        val_col = "rank"
    elif source == "mlb":
        df = standings.loc[standings["team_name"] == team_id, ["date", "mlb_rank"]].copy()
        val_col = "mlb_rank"
    else:
        raise ValueError(f"Unknown source '{source}', expected 'power' or 'mlb'.")

    if df.empty:
        s = pd.Series(dtype=float, name="rank")
        s.index.name = "date"
        return s

    df["date"] = pd.to_datetime(df["date"])
    df.sort_values("date", inplace=True)
    s = df.set_index("date")[val_col].astype(float)
    s.name = "rank"
    return s


def _rank_deltas_from_series(rank_series: pd.Series) -> np.ndarray:
    """1-step diffs of a rank time series (drop leading NaN)."""
    if rank_series.empty:
        return np.array([], dtype=float)
    return pd.Series(rank_series).diff().dropna().to_numpy()


# -------------------------------------------------------------------
# Main data builder for Δrank KDE + histogram
# -------------------------------------------------------------------
def build_delta_kde_and_hist(
    power: pd.DataFrame,
    standings: pd.DataFrame,
    team_names: Dict[str, str],   # team_id -> display name
    team_codes: Dict[str, str],   # team_id -> code  (e.g., 'TOR', 'NYY', etc.)
    selected_codes: Iterable[str],
    grid: np.ndarray,
    bin_edges: np.ndarray,
    source: Source = "power",     # 'power' or 'mlb' for which rank to diff
    auto_bandwidth: bool = True,
    bandwidth: float = 0.6,
    color_map: dict[str, str] | None = None,  # keyed by team_code if provided
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Produce tidy KDE + histogram of Δrank for the chosen source ('power' or 'mlb'),
    keyed by team codes for selection, but with labels from team_names for legends.

    Returns
    -------
    kde_df : columns ['x','team_code','team_id','label','density','color','bandwidth']
    hist_df: columns ['x','team_code','team_id','label','pdf','color']
    peaks  : pd.Series indexed by team_code with peak-x (argmax of scaled KDE)
    bws    : pd.Series indexed by team_code with bandwidth used
    """
    # Invert code mapping to get code -> id
    code_to_id = {code: tid for tid, code in team_codes.items()}

    rows_kde, rows_hist = [], []
    peak_vals: Dict[str, float] = {}
    bw_vals: Dict[str, float] = {}

    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    for code in selected_codes:
        team_id = code_to_id.get(code)
        if team_id is None:
            raise KeyError(f"Unknown team code: {code}")

        label = team_names.get(team_id, code)

        # 1) Pull series from the requested source and compute deltas
        series = _rank_series_for_team(power, standings, team_id, team_names, source)
        deltas = _rank_deltas_from_series(series)

        if deltas.size == 0:
            peak_vals[code] = np.nan
            bw_vals[code] = np.nan
            continue

        # 2) Bandwidth
        bw_use = None if auto_bandwidth else float(bandwidth)

        # 3) KDE (scaled to peak=1)
        density = kde_gaussian_1d(deltas, grid, bandwidth=bw_use)
        max_density = density.max() if density.size > 0 else 1.0
        density_scaled = density / (max_density if max_density > 0 else 1.0)

        peak_x = grid[np.argmax(density_scaled)] if density_scaled.size > 0 else np.nan
        peak_vals[code] = float(peak_x)

        if bw_use is None:
            n = len(deltas)
            std = np.std(deltas, ddof=1) if n > 1 else 0.0
            bw_calc = 1.06 * max(std, 1e-8) * n ** (-1/5)
            bw_vals[code] = float(max(bw_calc, 0.3))
        else:
            bw_vals[code] = float(bw_use)

        color = (color_map or {}).get(code)

        # 4) Fill KDE rows
        for x, y in zip(grid, density_scaled):
            rows_kde.append({
                "x": float(x),
                "team_code": code,
                "team_id": team_id,
                "label": label,
                "density": float(y),
                "color": color,
                "bandwidth": bw_vals[code],
            })

        # 5) Histogram (density=True then scale to peak=1)
        counts, _ = np.histogram(deltas, bins=bin_edges, density=True)
        peak_hist = counts.max() if counts.size > 0 else 1.0
        counts_scaled = counts / (peak_hist if peak_hist > 0 else 1.0)

        for x, y in zip(bin_centers, counts_scaled):
            rows_hist.append({
                "x": float(x),
                "team_code": code,
                "team_id": team_id,
                "label": label,
                "pdf": float(y),
                "color": color,
            })

    kde_df  = pd.DataFrame(rows_kde,  columns=["x","team_code","team_id","label","density","color","bandwidth"])
    hist_df = pd.DataFrame(rows_hist, columns=["x","team_code","team_id","label","pdf","color"])
    peaks   = pd.Series(peak_vals, name="peak_x")
    bws     = pd.Series(bw_vals,   name="bandwidth")

    if not kde_df.empty:
        kde_df = kde_df.sort_values(["team_code", "x"]).reset_index(drop=True)
    if not hist_df.empty:
        hist_df = hist_df.sort_values(["team_code", "x"]).reset_index(drop=True)

    return kde_df, hist_df, peaks, bws


def build_rank_volatility(
    power: pd.DataFrame,
    standings: pd.DataFrame,
    team_names: Dict[str, str],   # team_id -> display name
    team_codes: Dict[str, str],   # team_id -> code (e.g., 'TOR')
    selected_codes: Iterable[str],
    source: Source = "power",     # 'power' or 'mlb' for which rank to use
    ddof: int = 0,                # ddof=0 so the first value is 0.0 (matches your notebook)
    min_periods: int = 1,         # expanding min periods
) -> pd.DataFrame:
    """
    Build a tidy DataFrame with expanding std dev (volatility) of rank for each selected team.

    Parameters
    ----------
    power        : DataFrame with ['date','team','rank']   # 'team' is display name
    standings    : DataFrame with ['date','team_name','mlb_rank']  # 'team_name' is team_id
    team_names   : dict mapping team_id -> display name
    team_codes   : dict mapping team_id -> short code ('TOR', 'NYY', ...)
    selected_codes : iterable of codes to include (values from team_codes)
    use_mlb      : True => use MLB ranks; False => use Power ranks
    ddof         : degrees of freedom for std (default 0)
    min_periods  : minimum periods for expanding std (default 1)

    Returns
    -------
    DataFrame with columns:
      ['date','team_code','team_id','label','sigma','source']
    where sigma is the expanding std dev of the chosen rank series.
    """
    # code -> id
    code_to_id = {code: tid for tid, code in team_codes.items()}

    rows = []

    for code in selected_codes:
        team_id = code_to_id.get(code)
        if team_id is None:
            raise KeyError(f"Unknown team code: {code}")
        label = team_names.get(team_id, code)

        series = _rank_series_for_team(power, standings, team_id, team_names, source)
        if series.empty:
            continue

        # Expanding volatility (std dev); ddof=0 makes the very first value 0.0
        sigma = pd.Series(series).expanding(min_periods=min_periods).std(ddof=ddof).fillna(0.0)

        # Emit rows
        for dt, val in zip(sigma.index, sigma.values):
            rows.append({
                "date": pd.to_datetime(dt),
                "team_code": code,
                "team_id": team_id,
                "label": label,
                "sigma": float(val),
                "source": source,
            })

    out = pd.DataFrame(rows, columns=["date","team_code","team_id","label","sigma","source"])
    if not out.empty:
        out = out.sort_values(["team_code", "date"]).reset_index(drop=True)
    return out


# ---------- internal helpers ----------

def _rolling_acf(series: pd.Series, max_lag: int = 3) -> pd.DataFrame:
    """
    Expanding-window autocorrelation up to max_lag.
    Returns a DataFrame indexed by date with columns {1..max_lag}.
    """
    if series.empty:
        return pd.DataFrame(columns=list(range(1, max_lag + 1)))

    out = {lag: [] for lag in range(1, max_lag + 1)}
    dates = []
    # need at least max_lag+1 points for acf(lag)
    for t in range(max_lag + 1, len(series) + 1):
        window = series.iloc[:t]
        dates.append(series.index[t - 1])
        for lag in out:
            out[lag].append(window.autocorr(lag=lag))
    acf_df = pd.DataFrame(out, index=pd.to_datetime(dates))
    acf_df.index.name = "date"
    return acf_df


def _acf_to_stability(acf_df: pd.DataFrame, alpha: float = 0.25) -> pd.DataFrame:
    """
    Stability = Δ Fisher-z(ACF).
    Clips ACF into (-1, 1), applies atanh, diffs by 1 step, optional EWMA smooth.
    Returns DataFrame indexed by date with same columns as acf_df.
    """
    if acf_df.empty or len(acf_df) < 2:
        return pd.DataFrame(index=acf_df.index, columns=acf_df.columns)

    acf_clipped = acf_df.clip(-0.999, 0.999)
    z = np.arctanh(acf_clipped)
    dz = z.diff()

    if alpha and alpha > 0:
        dz = dz.ewm(alpha=alpha, adjust=False).mean()

    dz.index.name = "date"
    return dz

# ---------- public data-prep ----------

def build_acf_stability_timeseries(
    power: pd.DataFrame,
    standings: pd.DataFrame,
    team_names: Dict[str, str],   # team_id -> display name
    team_codes: Dict[str, str],   # team_id -> code (e.g., 'TOR')
    team_code: str,               # single team code
    source: Source = "power",     # 'power' or 'mlb' for which rank to use
    max_lag: int = 3,
    alpha: float = 0.25,          # EWMA smoothing for Δz (set 0 to disable)
    return_acf: bool = False      # if True, also return the raw ACF tidy df
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Produce a tidy Stability (Δ Fisher-z of ACF) time series for one team.

    Returns
    -------
    stability_df (tidy):
      columns = ['date','lag','value','team_code','team_id','label','source','metric']
      where metric='stability' and value is Δz for that lag at that date.

    If return_acf=True, also returns acf_df (same schema) with metric='acf' and value=ρ.
    """
    # code -> id
    code_to_id = {code: tid for tid, code in team_codes.items()}
    if team_code not in code_to_id:
        raise KeyError(f"Unknown team code: {team_code}")

    team_id = code_to_id[team_code]
    label = team_names.get(team_id, team_code)

    s = _rank_series_for_team(power, standings, team_id, team_names, source).dropna()
    if s.empty:
        cols = ["date","lag","value","team_code","team_id","label","source","metric"]
        empty = pd.DataFrame(columns=cols)
        return (empty, empty.copy()) if return_acf else empty

    # compute wide tables
    acf_wide  = _rolling_acf(s, max_lag=max_lag)         # index=date, columns=1..max_lag
    stab_wide = _acf_to_stability(acf_wide, alpha=alpha) # same shape, Δ Fisher-z

    # helper: wide -> tidy
    def _wide_to_tidy(df_wide: pd.DataFrame, metric_name: str) -> pd.DataFrame:
        if df_wide.empty:
            return pd.DataFrame(columns=["date","lag","value","metric"])
        tidy = (
            df_wide.reset_index()
                   .melt(id_vars="date", var_name="lag", value_name="value")
                   .dropna(subset=["value"])
        )
        tidy["date"] = pd.to_datetime(tidy["date"])
        tidy["lag"] = tidy["lag"].astype(int)
        tidy["metric"] = metric_name
        return tidy

    # stability
    stab_tidy = _wide_to_tidy(stab_wide, "stability")
    if not stab_tidy.empty:
        stab_tidy["team_code"] = team_code
        stab_tidy["team_id"]   = team_id
        stab_tidy["label"]     = label
        stab_tidy["source"]    = source
        stab_tidy.sort_values(["lag","date","team_id"], inplace=True)
        stab_tidy.reset_index(drop=True, inplace=True)
        # *** THIS LINE actually narrows the columns and keeps it ***
        stab_tidy = stab_tidy[["date","lag","value","team_code","team_id","label","source","metric"]]

    if not return_acf:
        return stab_tidy

    # acf (raw ρ)
    acf_tidy = _wide_to_tidy(acf_wide, "acf")
    if not acf_tidy.empty:
        acf_tidy["team_code"] = team_code
        acf_tidy["team_id"]   = team_id
        acf_tidy["label"]     = label
        acf_tidy["source"]    = source
        acf_tidy.sort_values(["lag","date","team_id"], inplace=True)
        acf_tidy.reset_index(drop=True, inplace=True)
        acf_tidy = acf_tidy[["date","lag","value","team_code","team_id","label","source","metric"]]

    return stab_tidy, acf_tidy


def _aligned_power_mlb(
    power: pd.DataFrame,
    standings: pd.DataFrame,
    team_id: str,
    team_names: Dict[str, str],
) -> pd.DataFrame:
    """
    Align Power and MLB ranks on dates for a given team_id.
    Returns columns: ['power','mlb'] indexed by datetime 'date'.
    """
    # Power uses display names
    team_name = team_names.get(team_id)
    if team_name is None:
        raise KeyError(f"team_id '{team_id}' not found in team_names")

    p = (power.loc[power["team"] == team_name, ["date", "rank"]]
              .assign(date=lambda d: pd.to_datetime(d["date"]))
              .sort_values("date")
              .set_index("date")
              .rename(columns={"rank": "power"}))

    m = (standings.loc[standings["team_name"] == team_id, ["date", "mlb_rank"]]
                 .assign(date=lambda d: pd.to_datetime(d["date"]))
                 .sort_values("date")
                 .set_index("date")
                 .rename(columns={"mlb_rank": "mlb"}))

    df = p.join(m, how="inner").dropna()
    df["power"] = pd.to_numeric(df["power"], errors="coerce")
    df["mlb"]   = pd.to_numeric(df["mlb"],   errors="coerce")
    return df.dropna()


def granger_power_to_mlb_report(
    power: pd.DataFrame,
    standings: pd.DataFrame,
    team_names: Dict[str, str],   # team_id -> display name
    team_codes: Dict[str, str],   # team_id -> code (e.g., 'TOR')
    team_code: str,               # single code to test
    max_lag: int = 4,
    min_obs: int = 6,
    alpha: float = 0.05,          # significance reference (not used in testing)
) -> Tuple[pd.DataFrame, Dict]:
    """
    Run Granger test of Power → MLB for one team (first differences).
    Returns (df, stats):
      df columns: ['lag','p_value','team_code','team_id','label','direction','diff']
      stats keys : {'team_code','team_id','label','n_obs_raw','n_obs_used',
                    'maxlag_requested','maxlag_effective','best_lag','best_p',
                    'is_significant','alpha','direction','diff'}
    """
    # code -> id
    code_to_id = {code: tid for tid, code in team_codes.items()}
    if team_code not in code_to_id:
        raise KeyError(f"Unknown team code: {team_code}")
    team_id = code_to_id[team_code]
    label = team_names.get(team_id, team_code)

    # 1) Align series
    df = _aligned_power_mlb(power, standings, team_id, team_names)
    n_raw = len(df)

    # 2) First differences (per your design)
    df = df.diff().dropna()
    n_used = len(df)

    # Early exits on too few observations
    stats = {
        "team_code": team_code,
        "team_id": team_id,
        "label": label,
        "n_obs_raw": int(n_raw),
        "n_obs_used": int(n_used),
        "max_lag_requested": int(max_lag),
        "max_lag_effective": 0,
        "best_lag": None,
        "best_p": None,
        "is_significant": False,
        "alpha": float(alpha),
        "direction": "power_to_mlb",
        "diff": "first_difference",
    }

    if n_used < min_obs:
        # Not enough data; return empty df with metadata filled
        empty_df = pd.DataFrame(columns=[
            "lag","p_value","team_code","team_id","label","direction","diff"
        ])
        return empty_df, stats

    # 3) Effective maxlag (cap by sample size)
    eff_maxlag = int(min(max_lag, max(1, n_used - 3)))
    stats["maxlag_effective"] = eff_maxlag

    # 4) Run Granger: column 2 (power) causes column 1 (mlb)
    arr = df[["mlb", "power"]].values
    res = grangercausalitytests(arr, maxlag=eff_maxlag, verbose=False)

    pvals = [res[lag][0]["ssr_ftest"][1] for lag in range(1, eff_maxlag + 1)]

    # 5) Build tidy df
    out = pd.DataFrame({
        "lag": np.arange(1, eff_maxlag + 1, dtype=int),
        "p_value": pvals,
    })
    out["team_code"] = team_code
    out["team_id"]   = team_id
    out["label"]     = label
    out["direction"] = "power_to_mlb"
    out["diff"]      = "first_difference"

    # 6) Scalars
    best_idx = int(np.nanargmin(pvals))
    best_lag = int(best_idx + 1)
    best_p   = float(pvals[best_idx])
    stats["best_lag"] = best_lag
    stats["best_p"]   = best_p
    stats["is_significant"] = bool(best_p < alpha)

    return out, stats

# -- helpers -------------------------------------------------------------

def _zscore(x: pd.Series) -> pd.Series:
    mu = x.mean()
    sd = x.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return x * 0.0
    return (x - mu) / sd


def _dtw_distance_with_steps(a: np.ndarray, b: np.ndarray) -> Tuple[float, int]:
    """
    Basic DTW with L1 cost. Returns (total_distance, path_steps).
    """
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return float("inf"), 0
    D = np.full((n + 1, m + 1), np.inf)
    steps = np.zeros((n + 1, m + 1), dtype=int)
    D[0, 0] = 0.0

    for i in range(1, n + 1):
        ai = a[i - 1]
        for j in range(1, m + 1):
            cost = abs(ai - b[j - 1])
            idx = np.argmin([D[i - 1, j], D[i, j - 1], D[i - 1, j - 1]])
            if idx == 0:      # up
                D[i, j] = cost + D[i - 1, j]
                steps[i, j] = steps[i - 1, j] + 1
            elif idx == 1:    # left
                D[i, j] = cost + D[i, j - 1]
                steps[i, j] = steps[i, j - 1] + 1
            else:             # diag
                D[i, j] = cost + D[i - 1, j - 1]
                steps[i, j] = steps[i - 1, j - 1] + 1

    path_steps = steps[n, m] if steps[n, m] > 0 else (n + m)
    return float(D[n, m]), int(path_steps)

# -- main ---------------------------------------------------------------

def compute_trajectory_similarity(
    power: pd.DataFrame,
    standings: pd.DataFrame,
    team_names: Dict[str, str],   # team_id -> display name
    team_codes: Dict[str, str],   # team_id -> code (e.g., 'TOR', 'NYY')
    team_code_a: str,
    team_code_b: str,
    source: Source = "power",  # 'power' or 'mlb' for which rank to use
    min_overlap: int = 3,
    max_rank_gap_per_step: float = 29.0,  # ranks 1..30 → worst per-step gap ≈ 29
) -> Dict[str, float | int | str | None]:
    """
    Compute similarity metrics between two teams' rank trajectories.
    Returns a simple dict with the stats.
    """

    use_mlb = (source == "mlb")
    # code -> id
    code_to_id = {code: tid for tid, code in team_codes.items()}
    if team_code_a not in code_to_id or team_code_b not in code_to_id:
        raise KeyError("Unknown team code in inputs.")

    team_id_a = code_to_id[team_code_a]
    team_id_b = code_to_id[team_code_b]
    label_a   = team_names.get(team_id_a, team_code_a)
    label_b   = team_names.get(team_id_b, team_code_b)
    src       = "mlb" if use_mlb else "power"

    # 1) Pull series and align on common dates (inner join)
    sA = _rank_series_for_team(power, standings, team_id_a, team_names, src).rename("A")
    sB = _rank_series_for_team(power, standings, team_id_b, team_names, src).rename("B")
    df = pd.concat([sA, sB], axis=1, join="inner").dropna()

    overlap = int(len(df))
    if overlap < min_overlap:
        return {
            "team_a": label_a, "team_b": label_b, "source": src,
            "overlap": overlap,
            "corr_delta": None,
            "corr_levels": None,
            "dtw_z": None,
            "dtw_similarity_z": None,
            "avg_abs_rank_gap": None,
            "dtw_raw": None,
            "dtw_similarity_raw_0_100": None,
        }

    # 2) Corr of first differences (trajectory co-movement)
    dA, dB = df["A"].diff().dropna(), df["B"].diff().dropna()
    k = min(len(dA), len(dB))
    corr_delta = float(np.corrcoef(dA.iloc[-k:], dB.iloc[-k:])[0, 1]) if k >= 2 else np.nan

    # 3) Corr on standardized levels (shape similarity)
    Az, Bz = _zscore(df["A"]), _zscore(df["B"])
    corr_levels = float(np.corrcoef(Az, Bz)[0, 1]) if len(df) >= 2 else np.nan

    # 4) DTW on standardized levels (time-warp tolerant shape)
    dtw_z, steps_z = _dtw_distance_with_steps(Az.to_numpy(), Bz.to_numpy())
    dtw_similarity_z = 100.0 / (1.0 + (dtw_z / max(steps_z, 1)))

    # 5) Human-scale stats on RAW ranks
    avg_abs_rank_gap = float((df["A"] - df["B"]).abs().mean())

    # 6) DTW on RAW ranks, normalized and mapped to 0–100
    dtw_raw, steps_raw = _dtw_distance_with_steps(df["A"].to_numpy(), df["B"].to_numpy())
    dtw_raw_per_step = dtw_raw / max(steps_raw, 1)
    dtw_similarity_raw = 100.0 * max(0.0, 1.0 - (dtw_raw_per_step / max_rank_gap_per_step))

    return {
        "team_a": label_a,
        "team_b": label_b,
        "source": src,
        "overlap": overlap,
        "corr_delta": float(corr_delta) if np.isfinite(corr_delta) else None,
        "corr_levels": float(corr_levels) if np.isfinite(corr_levels) else None,
        "dtw_z": float(dtw_z),
        "dtw_similarity_z": float(dtw_similarity_z),
        "avg_abs_rank_gap": float(avg_abs_rank_gap),
        "dtw_raw": float(dtw_raw),
        "dtw_similarity_raw_0_100": float(dtw_similarity_raw),
    }

# ---------- helpers (as in your snippet) ----------
def _prep(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    assert 'team_name' in df.columns, f"{prefix}: expected a 'team_name' column"
    df = df.copy()
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    keep = ['team_name'] + num_cols
    df = df[keep]
    ren = {c: f"{prefix}_{c}" for c in num_cols}
    return df.rename(columns=ren)

def build_feature_matrix_single(
    batting: pd.DataFrame | None = None,
    pitching: pd.DataFrame | None = None,
    fielding: pd.DataFrame | None = None,
    which: str = "combo",
    use_cols: dict | None = None,
    drop_cols_contains: list[str] | None = None,
    scale: bool = True
) -> tuple[pd.DataFrame, list[str]]:
    pieces = []
    if which in ("batting", "combo") and batting is not None:
        pieces.append(_prep(batting, "bat"))
    if which in ("pitching", "combo") and pitching is not None:
        pieces.append(_prep(pitching, "pit"))
    if which in ("fielding", "combo") and fielding is not None:
        pieces.append(_prep(fielding, "fld"))
    if not pieces:
        raise ValueError("No stats provided; pass batting/pitching/fielding and set 'which'.")

    M = pieces[0]
    for p in pieces[1:]:
        M = M.merge(p, on='team_name', how='inner')

    if use_cols:
        keep = ['team_name']
        if which in ("batting", "combo") and batting is not None and "batting" in use_cols:
            keep += [f"bat_{c}" for c in use_cols["batting"] if f"bat_{c}" in M.columns]
        if which in ("pitching", "combo") and pitching is not None and "pitching" in use_cols:
            keep += [f"pit_{c}" for c in use_cols["pitching"] if f"pit_{c}" in M.columns]
        if which in ("fielding", "combo") and fielding is not None and "fielding" in use_cols:
            keep += [f"fld_{c}" for c in use_cols["fielding"] if f"fld_{c}" in M.columns]
        M = M[[c for c in keep if c in M.columns]]

    if drop_cols_contains:
        drop_me = [c for c in M.columns if c != "team_name" and any(tok in c for tok in drop_cols_contains)]
        M = M.drop(columns=drop_me, errors='ignore')

    M = M.set_index('team_name')
    M = M.apply(lambda col: col.fillna(col.median()), axis=0)

    cols_kept = M.columns.tolist()
    if scale and cols_kept:
        scaler = StandardScaler()
        M[cols_kept] = scaler.fit_transform(M[cols_kept])

    return M, cols_kept

def cluster_teams_stats_single(
    M: pd.DataFrame,
    k: int = 4,
    linkage_method: str = "ward",
    metric: str = "euclidean"
) -> pd.DataFrame:
    if linkage_method == "ward" and metric != "euclidean":
        raise ValueError("Ward linkage requires Euclidean distance.")
    D = pdist(M.values, metric=metric)
    Z = linkage(D, method=linkage_method)
    labels = fcluster(Z, t=k, criterion='maxclust')
    return pd.DataFrame({"team_name": M.index.tolist(), "cluster": labels})

def last_mlb_rank_per_team(standings: pd.DataFrame) -> pd.Series:
    s = standings.copy()
    s['date'] = pd.to_datetime(s['date'])
    s = s.sort_values(['team_name','date'])
    last_rank = s.groupby('team_name').tail(1).set_index('team_name')['mlb_rank']
    return last_rank

def playoff_team_ids_from_odds(odds: pd.DataFrame) -> set:
    """
    Accepts either 'make_playoff_odds' or 'make_playoffs_odds'.
    Uses the LAST date; teams with odds >= 1.0 are flagged as playoff teams.
    """
    o = odds.copy()
    o['date'] = pd.to_datetime(o['date'])
    last_day = o['date'].max()
    final = o[o['date'] == last_day]
    col = 'make_playoffs_odds' if 'make_playoffs_odds' in final.columns else 'make_playoff_odds'
    made = final.loc[final[col] >= 1.0, 'team_name']
    return set(made.tolist())

def summarize_clusters_by_last_rank(
    clusters: pd.DataFrame,
    standings: pd.DataFrame,
    odds: pd.DataFrame
) -> pd.DataFrame:
    last_rank = last_mlb_rank_per_team(standings)
    playoffs = playoff_team_ids_from_odds(odds)

    rows = []
    for c, g in clusters.groupby('cluster'):
        tm = g['team_name'].tolist()
        ranks = last_rank.reindex(tm)
        avg_lr = float(ranks.mean())
        med_lr = float(ranks.median())
        made = sum(1 for t in tm if t in playoffs)
        rows.append({
            "cluster": int(c),
            "n_teams": int(len(tm)),
            "avg_last_mlb_rank": avg_lr,
            "median_last_mlb_rank": med_lr,
            "made_playoffs": int(made),
            "pct_playoffs": (made / len(tm)) if len(tm) else np.nan,
            "teams": ", ".join(tm)
        })
    out = pd.DataFrame(rows).sort_values(
        ["avg_last_mlb_rank", "pct_playoffs"], ascending=[True, False]
    ).reset_index(drop=True)
    return out

# ---------- one-call pipeline that RETURNS THE DF ----------
def cluster_and_summarize_season_stats(
    standings: pd.DataFrame,
    odds: pd.DataFrame,
    batting: pd.DataFrame | None = None,
    pitching: pd.DataFrame | None = None,
    fielding: pd.DataFrame | None = None,
    which: str = "combo",
    use_cols: dict | None = None,
    drop_cols_contains: list[str] | None = None,
    scale: bool = True,
    k: int = 6,
    linkage_method: str = "ward",
    metric: str = "euclidean",
    return_intermediates: bool = False
):
    """
    Build features -> cluster teams -> summarize by last MLB rank + playoff odds.
    Returns the summary DataFrame. If return_intermediates=True, also returns
    a dict with the feature matrix, columns, and raw clusters.
    """
    M, feat_cols = build_feature_matrix_single(
        batting=batting, pitching=pitching, fielding=fielding,
        which=which, use_cols=use_cols,
        drop_cols_contains=drop_cols_contains, scale=scale
    )
    clusters = cluster_teams_stats_single(M, k=k, linkage_method=linkage_method, metric=metric)
    summary = summarize_clusters_by_last_rank(clusters, standings, odds)
    if not return_intermediates:
        return summary
    return summary, {"features": M, "feature_columns": feat_cols, "clusters": clusters}

# ----------------------------- league-aware feature prep -----------------------------
def _z_per_date(s: pd.Series) -> pd.Series:
    mu = s.mean()
    sd = s.std(ddof=0)

    if pd.isna(sd) or sd == 0 or not np.isfinite(sd):
        return (s - mu) / 1.0  # fallback to denom = 1
    else:
        return (s - mu) / sd
    
def prepare_power_features_for_hmm(power: pd.DataFrame) -> pd.DataFrame:
    """
    Input  power: ['team','date','rank'] with team = display name, rank = numeric, weekly rows.
    Output powerx: original + engineered features:
        level, d_rank, improve, mom3, level_z, chg_z, mom3_z, level_dev
    """
    powerx = power.copy(deep=True)
    powerx['date'] = pd.to_datetime(powerx['date']).dt.tz_localize(None)
    powerx['rank'] = pd.to_numeric(powerx['rank'], errors='coerce')
    powerx = powerx.dropna(subset=['date', 'rank']).sort_values(['team', 'date'])

    powerx['level']   = -powerx['rank']  # higher better
    powerx['d_rank']  = powerx.groupby('team')['rank'].diff()
    powerx['improve'] = -powerx['d_rank']  # + means improved rank
    powerx['mom3']    = (powerx.groupby('team')['improve']
                         .rolling(3, min_periods=1).sum()
                         .reset_index(level=0, drop=True))

    # cross-sectional z by date
    powerx['level_z'] = powerx.groupby('date')['level'].transform(_z_per_date)
    powerx['chg_z']   = powerx.groupby('date')['improve'].transform(_z_per_date)
    powerx['mom3_z']  = (powerx.groupby('date')['mom3'].transform(_z_per_date)
                         .fillna(0.0))

    # team-relative level deviation (keeps level signal without swamping change)
    powerx['level_dev'] = powerx['level_z'] - powerx.groupby('team')['level_z'].transform('mean')
    return powerx

# ----------------------------- utilities -----------------------------
def stationary_power(P: np.ndarray, iters: int = 1000, tol: float = 1e-12) -> np.ndarray:
    v = np.ones(P.shape[0]) / P.shape[0]
    for _ in range(iters):
        v_next = v @ P
        if not np.all(np.isfinite(v_next)):
            return np.ones_like(v) / v.size
        if np.linalg.norm(v_next - v, 1) < tol:
            v = v_next; break
        v = v_next
    s = v.sum()
    return v / s if s > 0 else np.ones_like(v) / v.size

def _means_init_quantiles(g_fit: pd.DataFrame) -> np.ndarray:
    q = g_fit[['level_dev','chg_z','mom3_z']].quantile([0.2, 0.5, 0.8])
    mean_good = np.array([q.loc[0.8,'level_dev'], q.loc[0.8,'chg_z'], q.loc[0.8,'mom3_z']])
    mean_med  = np.array([q.loc[0.5,'level_dev'], q.loc[0.5,'chg_z'], q.loc[0.5,'mom3_z']])
    mean_bad  = np.array([q.loc[0.2,'level_dev'], q.loc[0.2,'chg_z'], q.loc[0.2,'mom3_z']])
    return np.vstack([mean_good, mean_med, mean_bad])  # Good, Med, Bad

def _means_init_kmeans(X: np.ndarray) -> np.ndarray:
    km = KMeans(n_clusters=3, n_init=10, random_state=42, algorithm="lloyd")
    labs = km.fit_predict(X)
    centers = km.cluster_centers_
    # order centers by "goodness": change > momentum > level_dev
    w = np.array([0.2, 0.5, 0.3])  # [level_dev, chg_z, mom3_z]
    order = np.argsort(centers @ w)[::-1]
    return centers[order]

def _fit_with_init(X: np.ndarray, means_init: np.ndarray) -> GaussianHMM:
    cov_floor = 1e-3
    cov_init  = np.maximum(np.var(X, axis=0, ddof=1), cov_floor)
    covars_init = np.vstack([cov_init, cov_init, cov_init])
    stay = 0.85; move = (1.0 - stay) / 2.0
    P_init = np.array([[stay, move, move],
                       [move, stay, move],
                       [move, move, stay]], dtype=float)
    pi_init = np.array([1/3, 1/3, 1/3], dtype=float)

    hmm = GaussianHMM(
        n_components=3,
        covariance_type='diag',
        n_iter=500,
        tol=1e-3,
        init_params='',      # we provide all inits
        params='stmc'        # learn startprob, transmat, means, covars
    )
    hmm.startprob_ = pi_init
    hmm.transmat_  = P_init
    hmm.means_     = means_init
    hmm.covars_    = covars_init
    hmm.fit(X)
    return hmm

# ----------------------------- main: fit a single team -----------------------------
def fit_team_hmm(
    power: pd.DataFrame,
    team_code: str,                         # CODE ONLY (e.g., "NYY")
    team_names: dict,                      # team_id -> display name
    team_codes: dict,                      # team_id -> code
    power_features: pd.DataFrame | None = None,
    min_points: int = 8,
    lenient_thresholds: dict | None = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Fit a 3-state HMM (Good/Mediocre/Bad) for ONE team selected by CODE.

    Returns
    -------
    states_df : DataFrame ['date','state','label']   (state: Good=0, Mediocre=1, Bad=2)
    stats     : dict with
                - 'P'     : 3x3 transition matrix (rows→cols: Good, Mediocre, Bad)
                - 'pi'    : 1x3 start prob (approx stationary only if ergodic)
                - 'means' : 3x3 state means [level_dev, chg_z, mom3_z]
                - 'init'  : 'quant' | 'fallback' (we use quantile init; no kmeans)
                - 'n_used': int
    """
    import numpy as np
    import pandas as pd
    from hmmlearn.hmm import GaussianHMM

    # --- resolve code -> id -> display name (required; no fallbacks) ---
    code_to_id = {code: tid for tid, code in team_codes.items()}
    if team_code not in code_to_id:
        raise KeyError(f"Unknown team code: {team_code}")
    team_id = code_to_id[team_code]
    if team_id not in team_names:
        raise KeyError(f"team_id '{team_id}' missing from team_names")
    label_team = team_names[team_id]  # matches power['team']

    # thresholds (kept for compatibility even if not used directly here)
    thr = {"TAU": 0.50, "ALPHA": 0.60, "BETA": 0.40, "MIN_ABS": 0.05}
    if lenient_thresholds:
        thr.update(lenient_thresholds)

    # --- features ---
    powerx = prepare_power_features_for_hmm(power) if power_features is None else power_features
    g = powerx.loc[powerx['team'] == label_team].sort_values('date').copy()

    # nothing for this team
    if g.empty:
        return pd.DataFrame(columns=["date","state","label"]), {
            "P": pd.DataFrame(np.nan, index=["Good","Mediocre","Bad"], columns=["Good","Mediocre","Bad"]),
            "pi": pd.DataFrame([[0.0,0.0,0.0]], columns=["Good","Mediocre","Bad"]),
            "means": pd.DataFrame(np.nan, index=["Good","Mediocre","Bad"], columns=["level_dev","chg_z","mom3_z"]),
            "init": "fallback",
            "n_used": 0,
        }

    cols = ['level_dev','chg_z','mom3_z']
    # Ensure numeric floats (no pd.NA), then mask invalid rows
    g[cols] = g[cols].apply(pd.to_numeric, errors='coerce')
    X = g[cols].to_numpy(dtype='float64')
    mask = np.isfinite(X).all(axis=1)
    g_fit = g.loc[mask].copy()
    X = X[mask]

    # ---------- fallback (too few points / zero variance) ----------
    if (len(g_fit) < min_points) or (np.nan_to_num(np.std(X, axis=0)).sum() == 0):
        if len(g_fit) == 0:
            # absolute empty fallback
            states_df = pd.DataFrame(columns=["date","state","label"])
            label_order = ['Good','Mediocre','Bad']
            P_df = pd.DataFrame(np.nan, index=label_order, columns=label_order)
            pi_df = pd.DataFrame([[0.0,0.0,0.0]], columns=label_order)
            means_df = pd.DataFrame(np.nan, index=label_order, columns=cols)
            return states_df, {"P": P_df, "pi": pi_df, "means": means_df, "init": "fallback", "n_used": 0}

        q_hi = g_fit['chg_z'].quantile(0.60)
        q_lo = g_fit['chg_z'].quantile(0.40)
        lbl = np.where(g_fit['chg_z'] >= q_hi, 'Good',
              np.where(g_fit['chg_z'] <= q_lo, 'Bad', 'Mediocre'))
        label_order = ['Good','Mediocre','Bad']
        state_map = {'Good':0, 'Mediocre':1, 'Bad':2}

        states_df = pd.DataFrame({
            "date": g_fit['date'].values,
            "state": pd.Index(lbl).map(state_map).to_numpy(),
            "label": lbl
        }).sort_values('date').reset_index(drop=True)

        means_df = (g_fit.assign(label=lbl)
                    .groupby('label')[cols].mean()
                    .reindex(label_order))
        P_df = pd.DataFrame(np.nan, index=label_order, columns=label_order)
        pi_df = pd.DataFrame(
            [pd.Series(lbl).value_counts(normalize=True).reindex(label_order).fillna(0).values],
            columns=label_order
        )
        return states_df, {"P": P_df, "pi": pi_df, "means": means_df, "init": "fallback", "n_used": int(len(g_fit))}

    # ---------- fit HMM (3-state Gaussian) ----------
    # simple quantile-based initialization for stability
    q = np.quantile(X[:, 0], [0.33, 0.66])  # on level_dev
    means_init = np.array([
        [q[1],  0.25,  0.25],   # Good-ish
        [0.0,   0.00,  0.00],   # Mediocre-ish
        [q[0], -0.25, -0.25],   # Bad-ish
    ], dtype='float64')

    hmm = GaussianHMM(n_components=3, covariance_type="full", random_state=0)
    # Not all versions accept means_/covars_ preset cleanly; try-catch to be safe
    try:
        hmm.means_ = means_init
    except Exception:
        pass

    hmm.fit(X)
    z = hmm.predict(X)

    # order states by level_dev mean: high→Good(0), mid→Mediocre(1), low→Bad(2)
    means = hmm.means_.copy()
    order = np.argsort(means[:, 0])        # low .. high
    # map: high -> 0(Good), mid -> 1(Mediocre), low -> 2(Bad)
    # order currently [low, mid, high]
    remap = {order[2]: 0, order[1]: 1, order[0]: 2}
    z_std = np.vectorize(remap.get)(z)

    label_vec = np.array(['Good','Mediocre','Bad'])
    labels = label_vec[z_std]

    states_df = g_fit[['date']].copy()
    states_df['state'] = z_std.astype(int)
    states_df['label'] = labels
    states_df = states_df.sort_values('date').reset_index(drop=True)

    # transition matrix & start prob, reordered to Good/Mediocre/Bad
    P = hmm.transmat_[ [order[2], order[1], order[0]], : ][:, [order[2], order[1], order[0]] ]
    pi = hmm.startprob_[ [order[2], order[1], order[0]] ]
    means_ord = means[ [order[2], order[1], order[0]], : ]

    P_df = pd.DataFrame(P, index=['Good','Mediocre','Bad'], columns=['Good','Mediocre','Bad'])
    pi_df = pd.DataFrame([pi], columns=['Good','Mediocre','Bad'])
    means_df = pd.DataFrame(means_ord, index=['Good','Mediocre','Bad'], columns=cols)

    return states_df, {"P": P_df, "pi": pi_df, "means": means_df, "init": "quant", "n_used": int(len(g_fit))}

    # ---------- try both inits; keep best by log-likelihood ----------
    best = None
    try:
        hmm_q = _fit_with_init(X, _means_init_quantiles(g_fit))
        best = ("quant", hmm_q, hmm_q.score(X))
    except Exception:
        pass
    if len(g_fit) >= 20:
        try:
            hmm_k = _fit_with_init(X, _means_init_kmeans(X))
            score_k = hmm_k.score(X)
            if (best is None) or (score_k > best[2]):
                best = ("kmeans", hmm_k, score_k)
        except Exception:
            pass
    if best is None:
        q_hi = g_fit['chg_z'].quantile(0.60)
        q_lo = g_fit['chg_z'].quantile(0.40)
        lbl = np.where(g_fit['chg_z'] >= q_hi, 'Good',
              np.where(g_fit['chg_z'] <= q_lo, 'Bad', 'Mediocre'))
        label_order = ['Good','Mediocre','Bad']
        state_map = {'Good':0, 'Mediocre':1, 'Bad':2}
        states_df = pd.DataFrame({
            "date": g_fit['date'].values,
            "state": pd.Index(lbl).map(state_map).to_numpy(),
            "label": lbl
        }).sort_values('date').reset_index(drop=True)

        means_df = (g_fit.assign(label=lbl)
                    .groupby('label')[['level_dev','chg_z','mom3_z']]
                    .mean().reindex(label_order))
        P_df = pd.DataFrame(np.nan, index=label_order, columns=label_order)
        pi_df = pd.DataFrame([pd.Series(lbl).value_counts(normalize=True)
                              .reindex(label_order).fillna(0).values], columns=label_order)
        return states_df, {"P": P_df, "pi": pi_df, "means": means_df, "init": "fallback", "n_used": int(len(g_fit))}

    tag_source, hmm, _ = best
    z = hmm.predict(X)

    # ---------- base label ordering by "goodness" ----------
    base_goodness = 0.5*g_fit['chg_z'] + 0.3*g_fit['mom3_z'] + 0.2*g_fit['level_dev']
    order = base_goodness.groupby(z).mean().sort_values(ascending=False).index.tolist()
    label_map_by_state = {order[0]:'Good', order[1]:'Mediocre', order[2]:'Bad'}

    # ---------- lenient calibration (reduce "Mediocre") ----------
    TAU, ALPHA, BETA, MIN_ABS = thr["TAU"], thr["ALPHA"], thr["BETA"], thr["MIN_ABS"]
    _, post = hmm.score_samples(X)  # posterior per state
    sid_by_label = {lab: sid for sid, lab in label_map_by_state.items()}
    gid, mid, bid = sid_by_label['Good'], sid_by_label['Mediocre'], sid_by_label['Bad']

    s = base_goodness
    t_good = max(MIN_ABS, s.quantile(ALPHA))
    t_bad  = min(-MIN_ABS, s.quantile(BETA))

    new_lbl = pd.Series('Mediocre', index=g_fit.index)
    mask_good = ((z == gid) & (post[:, gid] >= TAU)) | (s >= t_good)
    mask_bad  = ((z == bid) & (post[:, bid] >= TAU)) | (s <= t_bad)
    new_lbl.loc[mask_good] = 'Good'
    new_lbl.loc[mask_bad]  = 'Bad'

    state_map_fixed = {'Good':0, 'Mediocre':1, 'Bad':2}
    states_df = pd.DataFrame({
        "date": g_fit['date'].values,
        "state": new_lbl.map(state_map_fixed).astype(int).values,
        "label": new_lbl.values
    }).sort_values('date').reset_index(drop=True)

    # ---------- model stats in fixed Good→Mediocre→Bad order ----------
    ord_ids = [gid, mid, bid]
    P = hmm.transmat_[ord_ids][:, ord_ids]
    means = hmm.means_[ord_ids]
    pi_vec = stationary_power(P)

    fixed_order = ['Good','Mediocre','Bad']
    P_df     = pd.DataFrame(P, index=fixed_order, columns=fixed_order)
    means_df = pd.DataFrame(means, index=fixed_order, columns=['level_dev','chg_z','mom3_z'])
    pi_df    = pd.DataFrame([pi_vec], columns=fixed_order)

    return states_df, {"P": P_df, "pi": pi_df, "means": means_df, "init": tag_source, "n_used": int(len(g_fit))}
