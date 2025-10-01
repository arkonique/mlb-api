import statsapi, pandas as pd
from datetime import timedelta
import requests
import json
import os
import time
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from power_rankings import get_all_teams, match_team, get_webdriver

# Usage:
TEAMS = None
TMS = None

def get_teams_and_tms():
    global TEAMS, TMS
    if TEAMS is None or TMS is None:
        driver = get_webdriver()
        try:
            TEAMS, TMS = get_all_teams(driver)
        finally:
            driver.quit()
    return TEAMS, TMS

def sunday_range(start="2025-03-01", end="2025-10-31"):
    """
    Return a list of all Sundays between start and end (inclusive).
    If start isn't a Sunday, bump to the next Sunday.
    """
    start_d = pd.to_datetime(start).normalize()
    end_d   = pd.to_datetime(end).normalize()
    # pandas weekday: Monday=0 ... Sunday=6
    offset_days = (6 - start_d.weekday()) % 7
    first_sun = start_d + pd.Timedelta(days=offset_days)
    if first_sun > end_d:
        return []
    return list(pd.date_range(first_sun, end_d, freq="W-SUN"))

def sunday_standings(year=2025):
    """
    Pull standings snapshots for AL (103) and NL (104) on every Sunday.
    Uses date=MM/DD/YYYY and season=int to avoid the StatsAPI date/season bug.
    Returns a tidy DataFrame with one row per team per Sunday.
    """
    start=f"{year}-03-01"
    end=f"{year}-10-31"
    leagues = ["103", "104"]
    sundays = sunday_range(start, end)
    rows = []

    for d in tqdm(sundays, desc="Importing weekly standings", unit="week"):
        # Display progress bar
        season = d.year
        date_str = pd.to_datetime(d).strftime("%m/%d/%Y")
        for lg in leagues:
            try:
                data = statsapi.standings_data(
                    leagueId=lg,
                    season=season,
                    date=date_str,
                    standingsTypes="regularSeason",
                )
            except Exception:
                # If StatsAPI hiccups or date not valid yet, just skip this league/date
                continue
            if not isinstance(data, dict) or not data:
                continue

            # Each value is a division blob with a 'teams' list of flat dicts (as you printed)
            for div_blob in data.values():
                for t in div_blob.get("teams", []):
                    rows.append({
                        "date": pd.to_datetime(d).normalize(),
                        "league_id": lg,
                        "team_id": t.get("team_id"),
                        "team_name": match_team(t.get("name"), TEAMS),
                        "wins": t.get("w"),
                        "losses": t.get("l"),
                        "winning_pct": t.get("w")/max(t.get("w") + t.get("l"),1),
                        "division_rank": t.get("div_rank"),
                        "league_rank": t.get("league_rank"),
                        "sport_rank": t.get("sport_rank"),
                        "games_back": t.get("gb"),
                        "wc_rank": t.get("wc_rank"),
                        "wc_gb": t.get("wc_gb"),
                        "wc_elim_num": t.get("wc_elim_num"),
                        "elim_num": t.get("elim_num"),
                    })

    df = pd.DataFrame(rows)

    # Normalize types where it helps (many fields arrive as strings)
    if not df.empty:
        # Coerce numeric-ish columns; keep GB/wc_gb as strings because they include '-', '+2.0', 'E'
        for col in ["wins", "losses", "league_rank", "division_rank", "sport_rank"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        # winning_pct sometimes "0.593" string or already float
        df["winning_pct"] = pd.to_numeric(df["winning_pct"], errors="coerce")

        # Ensure date is normalized midnight
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()

        # mlb rank
        df["mlb_rank"] = (
            df.groupby("date")["winning_pct"]
            .rank(method="min", ascending=False)
            .astype(int)
        )

        # Optional: sort for downstream asof merges/plots
        df = df.sort_values(["team_id", "date"]).reset_index(drop=True)

    return df

def sunday_odds(year = 2025):
    """
    Pull Fangraphs playoff odds for every Sunday in the given year.
    """
    start=f"{year}-03-01"
    end=f"{year}-10-31"
    sundays = sunday_range(start, end)
    rows = []
    for d in tqdm(sundays, desc="Importing weekly odds", unit="week"):
        current = pd.to_datetime(d).strftime("%Y-%m-%d")
        url = f"https://www.fangraphs.com/api/playoff-odds/odds?dateEnd={current}&dateDelta=&projectionMode=2&standingsType=mlb"
        json = requests.get(url).json()

        if not json:
            continue

        # each element in json is a team blob. We want 
        # Team name - shortName, 
        # Expected wins - endData.ExpW, 
        # Expected losses - endData.ExpL, 
        # Rest of season wins - endData.rosW, 
        # Wild card win odds - endData.wcWin, 
        # Division series win odds - endData.dsWin, 
        # Championship series win odds - endData.csWin, 
        # World series win odds - endData.wsWin,
        # Make playoffs odds - endData.poffTitle
        # Clinch wild card - endData.wcTitle
        # Clinch bye - endData.div2Title
        # Win division - endData.divTitle
        for team in json:
            ed = team.get("endData", {})
            rows.append({
                "date": pd.to_datetime(d).normalize(),
                "team_name": match_team(team.get("shortName"), TEAMS),
                "expected_wins": ed.get("ExpW"),
                "expected_losses": ed.get("ExpL"),
                "ros_wins": ed.get("rosW"),
                "wc_win_odds": ed.get("wcWin"),
                "ds_win_odds": ed.get("dsWin"),
                "cs_win_odds": ed.get("csWin"),
                "ws_win_odds": ed.get("wsWin"),
                "make_playoffs_odds": ed.get("poffTitle"),
                "clinch_wc_odds": ed.get("wcTitle"),
                "clinch_bye_odds": ed.get("div2Title"),
                "win_division_odds": ed.get("divTitle"),
            })
        time.sleep(0.2)  # be nice to Fangraphs servers
    df = pd.DataFrame(rows)
    if not df.empty:
        # Coerce numericish columns
        for col in ["expected_wins", "expected_losses", "ros_wins",
                    "wc_win_odds", "ds_win_odds", "cs_win_odds", "ws_win_odds",
                    "make_playoffs_odds", "clinch_wc_odds", "clinch_bye_odds", "win_division_odds"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Ensure date is normalized midnight
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()

        # Optional: sort for downstream asof merges/plots
        df = df.sort_values(["team_name", "date"]).reset_index(drop=True)
    return df
