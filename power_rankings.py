# power_rankings.py
# Script to scrape MLB power rankings from MLB.com using Selenium and store them in a DataFrame
import os
import shutil
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions


def get_webdriver():
    """
    Chrome-only, works locally and on Heroku when using the chrome-for-testing buildpack.
    The buildpack places 'chrome' and 'chromedriver' on PATH.
    """
    opts = ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")

    # Prefer explicit binaries if discoverable; otherwise Selenium will use PATH.
    chrome_bin = shutil.which("chrome")
    if chrome_bin:
        opts.binary_location = chrome_bin

    driver_path = shutil.which("chromedriver")
    service = ChromeService(executable_path=driver_path) if driver_path else ChromeService()

    return webdriver.Chrome(service=service, options=opts)

def get_all_articles(start_date, end_date, page, driver):
    SEARCHSTART = start_date
    SEARCHEND = end_date
    url = f"https://www.mlb.com/search?q=power+rankings&filter=news&page={page}"
    driver.get(url)
    articles = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='suggested-hit-container']")
    results = []
    for link in articles:
        title = link.find_element(By.CSS_SELECTOR, "h3").text
        date = link.find_element(By.CSS_SELECTOR, "time").get_attribute("datetime")
        # subtract a day and convert back to YYYY-MM-DD string
        date = (pd.to_datetime(date) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        link_url = link.get_attribute("href")
        if SEARCHSTART <= date <= SEARCHEND and "power rankings" in title.lower() and "hitter" not in title.lower() and "pitcher" not in title.lower():
            results.append((title, date, link_url))
    return results

def get_all_articles_in_range(start_date, end_date, driver):
    page = 1
    all_results = []
    while True:
        results = get_all_articles(start_date, end_date, page, driver)
        if not results:
            break
        all_results.extend(results)
        page += 1
    return all_results

def get_all_teams(driver):
    driver.get("https://www.mlb.com/team")
    stsr = """
        Arizona Diamondbacks - ARI

        Atlanta Braves - ATL

        Baltimore Orioles - BAL

        Boston Red Sox - BOS

        Chicago Cubs - CHC

        Chicago White Sox - CHW or CWS

        Cincinnati Reds - CIN

        Cleveland Indians - CLE

        Colorado Rockies - COL

        Detroit Tigers - DET

        Florida Marlins - FLA

        Houston Astros - HOU

        Kansas City Royals - KAN

        Los Angeles Angels of Anaheim - LAA

        Los Angeles Dodgers - LAD

        Milwaukee Brewers - MIL

        Minnesota Twins - MIN

        New York Mets - NYM

        New York Yankees - NYY

        Oakland Athletics - OAK

        Philadelphia Phillies - PHI

        Pittsburgh Pirates - PIT

        San Diego Padres - SD

        San Francisco Giants - SF

        Seattle Mariners - SEA

        St. Louis Cardinals - STL

        Tampa Bay Rays - TB

        Texas Rangers - TEX

        Toronto Blue Jays - TOR

        Washington Nationals - WAS
    """
    # div class p-forge-list-item, team name in id as a hyphenated string and in h2 inside the div as text
    team_elements = driver.find_elements(By.CSS_SELECTOR, "div.p-forge-list-item")
    teams = {}
    tms = {}
    for team in team_elements:
        team_name = team.find_element(By.TAG_NAME, "h2").text
        team_id = team.get_attribute("id")
        # for team code, match the team name to the abbreviation in stsr
        for line in stsr.split("\n"):
            line = line.strip()
            if not line:
                continue
            full_name, abbrev = line.split(" - ")
            if team_name == full_name:
                team_code = abbrev
                break
        teams[team_id] = team_name
        tms[team_id] = team_code
    return teams, tms

def match_team(name, teams):
    name = name.replace("'", "").replace(".", "").replace("’", "").replace("“", "").replace("”", "").replace('"', '').replace("`", "").replace("´", "").replace("–", "").replace("—", "").replace("-", "").strip()
    if name == "As":
        name = "Athletics"
    if name == "Dbacks":
        name = "Diamondbacks"
    for team_id, team_name in teams.items():
        team_name_clean = team_name.replace("'", "").replace(".", "").replace("’", "").replace("“", "").replace("”", "").replace('"', '').replace("`", "").replace("´", "").replace("–", "").replace("—", "").replace("-", "").strip()
        if name.lower() in team_name_clean.lower() or team_name_clean.lower() in name.lower():
            return team_id
    return None
def get_rankings_from_article(url, teams, driver):
    driver.get(url)
    # look for the first article tag
    article = driver.find_element(By.CSS_SELECTOR, "article")
    # Look for divs which have class 'markdown' as well as a strong tag inside them. Both need to be present inside the article tag
    ranking_elements = article.find_elements(By.CSS_SELECTOR, "div.markdown strong")
    rankings = []
    for i, elem in enumerate(ranking_elements):
        # get the rank. The string is of the form "{rank}. {team name}", so split on the first period
        text = elem.text
        # if the text does not start with a number, skip it
        if not text[0].isdigit():
            continue
        rank, team_name = text.split(".", 1) # split on the first period
        # if length of team_name is 0 after stripping, take the next sibling
        if len(team_name.strip()) == 0:
            team_name = ranking_elements[i + 1].text
        rank = rank.strip()
        team_name = team_name.strip()
        # team name has additional text, so split on the first comma or parenthesis, take the first part and match that to the teams dict (word match, i.e. "Yankees" should match "New York Yankees")
        team_name = team_name.split(",")[0].split("(")[0].strip()
        # fall back for Athletics -> A's
        # remove punctuation from team_name
        team_name = team_name.replace("'", "").replace(".", "").replace("’", "").replace("“", "").replace("”", "").replace('"', '').replace("`", "").replace("´", "").replace("–", "").replace("—", "").replace("-", "").strip()
        if team_name == "As":
            team_name = "Athletics"
        if team_name == "Dbacks":
            team_name = "Diamondbacks"
        matched_team = None
        for team_id, name in teams.items():
            if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                matched_team = (rank, team_id)
                break
        if matched_team:
            rankings.append(matched_team)
    return rankings

def rankings_wrapper(year):
    driver = get_webdriver()
    YEAR = 2025
    SEARCHSTART = f"{YEAR-1}-11-01"
    SEARCHEND = f"{YEAR}-10-31"

    searchstart = f"{year-1}-11-01"
    searchend = f"{year}-10-31"
    all_articles = get_all_articles_in_range(searchstart, searchend, driver)
    all_teams, l_tms = get_all_teams(driver)
    all_rankings = []

    # Progress bar over articles
    for title, date, url in tqdm(all_articles, desc="Scraping Power Rankings", unit="week"):
        rankings = get_rankings_from_article(url, all_teams, driver)
        for rank, team_id in rankings:
            all_rankings.append((date, team_id, rank, all_teams[team_id]))

    driver.quit()
    df_r = pd.DataFrame(all_rankings, columns=["date", "team_id", "rank", "team"])
    df_r["date"] = pd.to_datetime(df_r["date"])
    df_r["rank"] = pd.to_numeric(df_r["rank"], errors="coerce").astype("Int64")

    art = pd.DataFrame(all_articles, columns=["title", "date", "url"])
    art["date"] = pd.to_datetime(art["date"])

    # If multiple articles share the same date, prefer ones that look like team power rankings
    art["is_pr"] = art["title"].str.contains(r"\bpower rankings\b", case=False, na=False)
    art = (art.sort_values(["date", "is_pr"], ascending=[True, False])
              .drop_duplicates(subset=["date"], keep="first")[["date", "url"]])

    df_long = (df_r.merge(art, on="date", how="left")
                   [["date", "url", "team_id", "team", "rank"]]
                   .sort_values(["date", "rank"]))
    
    return df_long, all_teams, l_tms

def sunday_power(year=2025): # nicer name
    df, teams, tms = rankings_wrapper(year)
    return df, teams, tms

# TEST

if __name__ == "__main__":
    df, teams, tms = sunday_power(2025)
    print(df)
    df.to_csv("mlb_power_rankings_2025.csv", index=False)
