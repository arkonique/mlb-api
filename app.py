from flask import Flask, request, jsonify
from mlb_analytics import *
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# Global variables to cache data
POWER = pd.DataFrame()
STANDINGS = pd.DataFrame()
ODDS = pd.DataFrame()
BATTING = pd.DataFrame()
PITCHING = pd.DataFrame()
FIELDING = pd.DataFrame()
TEAMS = {}
TMS = {}
YEAR = 2025  # default year

@app.route("/")
def home():
    return {"ok": True}

@app.route("/teams")
def teams():
    global TEAMS, TMS
    get_teams_and_tms()
    teams = TEAMS
    tms = TMS
    return {"teams": teams, "tms": tms}

@app.route("/power")
def power():
    global POWER, TEAMS, TMS, YEAR
    year = int(request.args.get("year", 2025))

    # 1) Serve from in-memory cache if same year
    if not POWER.empty and YEAR == year:
        return {"power": POWER.to_dict(orient="records"), "teams": TEAMS, "tms": TMS}

    # 2) If cache is empty, prefer on-disk CSV (do NOT touch TEAMS/TMS)
    csv_path = f"power_rankings_{year}.csv"
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        POWER = df
        YEAR = year
        # leave TEAMS and TMS exactly as they are
        return {"power": POWER.to_dict(orient="records"), "teams": TEAMS, "tms": TMS}

    # 3) Fall back to the original function (this will also update TEAMS/TMS)
    power_df, teams, tms = sunday_power(year)
    POWER = power_df
    TEAMS = teams
    TMS = tms
    YEAR = year
    return {"power": POWER.to_dict(orient="records"), "teams": TEAMS, "tms": TMS}

@app.route("/standings")
def standings():
    global STANDINGS, YEAR
    year = int(request.args.get("year", 2025))

    # serve from warm cache
    if not STANDINGS.empty and YEAR == year:
        return {"standings": STANDINGS.to_dict(orient="records")}

    # CSV fallback
    csv_path = f"standings_{year}.csv"
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        STANDINGS = df
        YEAR = year
        return {"standings": STANDINGS.to_dict(orient="records")}

    # compute/fetch
    df = sunday_standings(year)
    STANDINGS = df
    YEAR = year
    return {"standings": df.to_dict(orient="records")}


@app.route("/odds")
def odds():
    global ODDS, YEAR
    year = int(request.args.get("year", 2025))

    if not ODDS.empty and YEAR == year:
        return {"odds": ODDS.to_dict(orient="records")}

    csv_path = f"odds_{year}.csv"
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        ODDS = df
        YEAR = year
        return {"odds": ODDS.to_dict(orient="records")}

    df = sunday_odds(year)
    ODDS = df
    YEAR = year
    return {"odds": df.to_dict(orient="records")}


@app.route("/batting")
def batting():
    global BATTING, YEAR
    year = int(request.args.get("year", 2025))

    if not BATTING.empty and YEAR == year:
        return {"batting": BATTING.to_dict(orient="records")}

    csv_path = f"batting_stats_{year}.csv"
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        BATTING = df
        YEAR = year
        return {"batting": BATTING.to_dict(orient="records")}

    df = get_batting_stats(year)
    BATTING = df
    YEAR = year
    return {"batting": df.to_dict(orient="records")}


@app.route("/pitching")
def pitching():
    global PITCHING, YEAR
    year = int(request.args.get("year", 2025))

    if not PITCHING.empty and YEAR == year:
        return {"pitching": PITCHING.to_dict(orient="records")}

    csv_path = f"pitching_stats_{year}.csv"
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        PITCHING = df
        YEAR = year
        return {"pitching": PITCHING.to_dict(orient="records")}

    df = get_pitching_stats(year)
    PITCHING = df
    YEAR = year
    return {"pitching": df.to_dict(orient="records")}


@app.route("/fielding")
def fielding():
    global FIELDING, YEAR
    year = int(request.args.get("year", 2025))

    if not FIELDING.empty and YEAR == year:
        return {"fielding": FIELDING.to_dict(orient="records")}

    csv_path = f"fielding_stats_{year}.csv"
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        FIELDING = df
        YEAR = year
        return {"fielding": FIELDING.to_dict(orient="records")}

    df = get_fielding_stats(year)
    FIELDING = df
    YEAR = year
    return {"fielding": df.to_dict(orient="records")}

@app.route("/ranks")
def ranks():
    selected_codes = request.args.getlist("teams")  # list of team codes
    mode = request.args.get("mode", "both")       # 'power', 'mlb', 'diff', or 'both'

    if POWER.empty or STANDINGS.empty:
        return {"error": "Data not loaded. Please fetch /power, /standings endpoints first."}, 400

    df = build_plot_table(
        power=POWER,
        standings=STANDINGS,
        selected_codes=selected_codes,
        team_names=TEAMS,
        team_codes=TMS,
        mode=mode
    )
    return {"ranks": df.to_dict(orient="records")}


@app.route("/kdes")
def kdes():
    selected_codes = request.args.getlist("teams")  # list of team codes
    source = request.args.get("source", "power")    # 'power' or 'mlb'

    if POWER.empty or STANDINGS.empty:
        return {"error": "Data not loaded. Please fetch /power, /standings endpoints first."}, 400

    kde_data, hist_data, peaks, bw = build_delta_kde_and_hist(
        power=POWER,
        standings=STANDINGS,
        team_names=TEAMS,
        team_codes=TMS,
        selected_codes=selected_codes,
        source=source,
        grid=np.linspace(-15, 15, 300),
        bin_edges=np.linspace(-15, 15, 31)
    )
    return {
        "kde_data": kde_data.to_dict(orient="records"),
        "hist_data": hist_data.to_dict(orient="records"),
        "peaks": peaks,
        "bandwidth": bw
    }


@app.route("/volatility")
def volatility():
    selected_codes = request.args.getlist("teams")  # list of team codes
    source = request.args.get("source", "power")    # 'power' or 'mlb'

    if POWER.empty or STANDINGS.empty:
        return {"error": "Data not loaded. Please fetch /power, /standings endpoints first."}, 400

    volatiliy_data = build_rank_volatility(
        power=POWER,
        standings=STANDINGS,
        team_names=TEAMS,
        team_codes=TMS,
        selected_codes=selected_codes,
        source=source
    )
    return {"volatility_data": volatiliy_data.to_dict(orient="records")}


@app.route("/stability")
def stability():
    team_code = request.args.get("team")            # single team code
    source = request.args.get("source", "power")    # 'power' or 'mlb'
    max_lag = int(request.args.get("max_lag", 4))   # max lag for ACF

    if POWER.empty or STANDINGS.empty:
        return {"error": "Data not loaded. Please fetch /power, /standings endpoints first."}, 400

    stab_df, _ = build_acf_stability_timeseries(
        power=POWER,
        standings=STANDINGS,
        team_names=TEAMS,
        team_codes=TMS,
        team_code=team_code,
        source=source,
        max_lag=max_lag,
        return_acf=False,
    )
    return {
        "stability_data": stab_df.to_dict(orient="records"),
    }
@app.route("/consistency")
def consistency():
    team_code = request.args.get("team")            # single team code
    source = request.args.get("source", "power")    # 'power' or 'mlb'
    max_lag = int(request.args.get("max_lag", 4))   # max lag for ACF

    if POWER.empty or STANDINGS.empty:
        return {"error": "Data not loaded. Please fetch /power, /standings endpoints first."}, 400

    _ , cons_df = build_acf_stability_timeseries(
        power=POWER,
        standings=STANDINGS,
        team_names=TEAMS,
        team_codes=TMS,
        team_code=team_code,
        source=source,
        max_lag=max_lag,
        return_acf=True,
    )
    return {
        "consistency_data": cons_df.to_dict(orient="records"),
    }


@app.route("/granger")
def granger():
    team_code = request.args.get("team")            # single team code
    max_lag = int(request.args.get("max_lag", 4))   # max lag for Granger test

    if POWER.empty or STANDINGS.empty:
        return {"error": "Data not loaded. Please fetch /power, /standings endpoints first."}, 400

    granger_df, stats = granger_power_to_mlb_report(
        power=POWER,
        standings=STANDINGS,
        team_names=TEAMS,
        team_codes=TMS,
        team_code=team_code,
        max_lag=max_lag
    )
    return {
        "granger_data": granger_df.to_dict(orient="records"),
        "stats": stats
    }


@app.route("/similarity")
def similarity():
    team_code_a = request.args.get("team_a")        # single team code A
    team_code_b = request.args.get("team_b")        # single team code B
    source = request.args.get("source", "power")    # 'power' or 'mlb'

    if POWER.empty or STANDINGS.empty:
        return {"error": "Data not loaded. Please fetch /power, /standings endpoints first."}, 400

    stats = compute_trajectory_similarity(
        power=POWER,
        standings=STANDINGS,
        team_names=TEAMS,
        team_codes=TMS,
        team_code_a=team_code_a,
        team_code_b=team_code_b,
        source=source
    )
    return {
        "similarity_stats": stats
    }


@app.route("/clusters")
def clusters():
    k = int(request.args.get("k", 6))               # number of clusters

    if STANDINGS.empty or ODDS.empty or BATTING.empty or PITCHING.empty or FIELDING.empty:
        return {"error": "Data not loaded. Please fetch /standings, /odds, /batting, /pitching, /fielding endpoints first."}, 400

    clusters = cluster_and_summarize_season_stats(
        standings=STANDINGS,
        odds=ODDS,
        batting=BATTING,
        pitching=PITCHING,
        fielding=FIELDING,
        k=k
    )
    clusters = clusters.assign(teams=clusters["teams"].astype(str).str.split(r"\s*,\s*"))
    return {
        "clusters": clusters.to_dict(orient="records")
    }

@app.route("/hmm")
def hmm():
    team = request.args.get("team")  # e.g., TOR
    if not team:
        return {"error": "team param required"}, 400

    # build features once (or reuse your cache)
    powerx = prepare_power_features_for_hmm(POWER)

    states_df, stats = fit_team_hmm(
        power=POWER,
        team_code=team,
        team_names=TEAMS,
        team_codes=TMS,
        power_features=powerx,
        min_points=8
    )

    # --- JSON-safe serialization ---
    out = {
        "states": states_df.to_dict(orient="records"),
        "stats": {
            "P": stats["P"].values.tolist() if hasattr(stats["P"], "values") else stats["P"],
            "P_labels": stats["P"].index.tolist() if hasattr(stats["P"], "index") else ["Good","Mediocre","Bad"],
            "pi": stats["pi"].values.tolist() if hasattr(stats["pi"], "values") else stats["pi"],
            "means": stats["means"].values.tolist() if hasattr(stats["means"], "values") else stats["means"],
            "mean_cols": list(stats["means"].columns) if hasattr(stats["means"], "columns") else ["level_dev","chg_z","mom3_z"],
            "init": stats.get("init", "quant"),
            "n_used": int(stats.get("n_used", 0)),
        }
    }
    return out

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))