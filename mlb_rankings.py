# File that imports power_rankings.py and table_rankings.py into one convenient import
from power_rankings import *
from table_rankings import *
from io import StringIO

def get_batting_stats(year=2025):
    driver = get_webdriver()
    url = f"https://www.baseball-reference.com/leagues/majors/{year}.shtml#all_teams_standard_batting"

    # get the url and parse the table #teams_standard_batting
    driver.get(url)
    table = driver.find_element("css selector", "table#teams_standard_batting")
    # read the html table into a pandas dataframe
    html_str = table.get_attribute('outerHTML')
    df = pd.read_html(StringIO(html_str))[0]
    driver.quit()

    # remove last 3 rows (totals, etc)
    df = df.iloc[:-3]

    # convert team names to team ids
    df['team_name'] = df['Tm'].apply(lambda name: match_team(name, TEAMS))
    # remove Tm column
    df = df.drop(columns=['Tm'])

    # rename columns to for better readability
    df = df.rename(columns={
        '#Bat': 'num_batters', # number of players used in games
        'BatAge': 'batting_age', # average age of batters
        'R/G': 'runs_per_game', # runs per game
        'G': 'games', # games played
        'PA': 'plate_appearances', # plate appearances
        'AB': 'at_bats', # at bats
        'R': 'runs', # runs scored
        'H': 'hits', # hits
        '2B': 'doubles', # doubles
        '3B': 'triples', # triples
        'HR': 'home_runs', # home runs
        'RBI': 'runs_batted_in', # runs batted in
        'SB': 'stolen_bases', # stolen bases
        'CS': 'caught_stealing', # caught stealing
        'BB': 'base_on_balls', # walks
        'SO': 'strikeouts', # strikeouts
        'BA': 'batting_average', # batting average
        'OBP': 'on_base_percentage', # on-base percentage
        'SLG': 'slugging_percentage', # slugging percentage
        'OPS': 'on_base_plus_slugging', # on-base plus slugging
        'OPS+': 'ops_plus', # adjusted on-base plus slugging
        'TB': 'total_bases', # total bases
        'GDP': 'grounded_into_double_play', # grounded into double play
        'HBP': 'hit_by_pitch', # hit by pitch
        'SH': 'sacrifice_hits', # sacrifice hits
        'SF': 'sacrifice_flies', # sacrifice flies
        'IBB': 'intentional_base_on_balls', # intentional walks
        'LOB': 'left_on_base', # left on base
    })
    return df

def get_pitching_stats(year=2025):
    driver = get_webdriver()
    url = f"https://www.baseball-reference.com/leagues/majors/{year}.shtml#all_teams_standard_pitching"

    # get the url and parse the table #teams_standard_pitching
    driver.get(url)
    table = driver.find_element("css selector", "table#teams_standard_pitching")
    # read the html table into a pandas dataframe
    html_str = table.get_attribute('outerHTML')
    df = pd.read_html(StringIO(html_str))[0]
    driver.quit()

    # remove last 3 rows (totals, etc)
    df = df.iloc[:-3]

    # convert team names to team ids
    df['team_name'] = df['Tm'].apply(lambda name: match_team(name, TEAMS))
    # remove Tm column
    df = df.drop(columns=['Tm'])

    # rename columns to for better readability
    df = df.rename(columns={
        '#P': 'num_pitchers', # number of players used in games
        'PAge': 'pitching_age', # average age of pitchers
        'RA/G': 'runs_allowed_per_game', # runs allowed per game
        'W': 'wins', # wins
        'L': 'losses', # losses
        'W-L%': 'win_loss_percentage', # win-loss percentage
        'ERA': 'earned_run_average', # earned run average
        'G': 'games', # games played
        'GS': 'games_started', # games started
        'GF': 'games_finished', # games finished
        'CG': 'complete_games', # complete games
        'tSho': 'team_shutout', # shutouts by team
        'cSho': 'complete_shutout', # complete shutouts
        'SV': 'saves', # saves
        'IP': 'innings_pitched', # innings pitched
        'H': 'hits_allowed', # hits allowed
        'R': 'runs_allowed', # runs allowed
        'ER': 'earned_runs_allowed', # earned runs allowed
        'HR': 'home_runs_allowed', # home runs allowed
        'BB': 'base_on_balls', # walks allowed
        'IBB': 'intentional_base_on_balls', # intentional walks allowed
        'SO': 'strikeouts', # strikeouts
        'HBP': 'hit_by_pitch', # hit by pitch
        'BK': 'balks', # balks
        'WP': 'wild_pitches', # wild pitches
        'BF': 'batters_faced', # batters faced
        'ERA+': 'era_plus', # adjusted earned run average
        'FIP': 'fielding_independent_pitching', # fielding independent pitching
        'WHIP': 'walks_hits_per_inning_pitched', # walks + hits
        'H9': 'hits_per_nine_innings', # hits per 9 innings
        'HR9': 'home_runs_per_nine_innings', # home runs per 9 innings
        'BB9': 'walks_per_nine_innings', # walks per 9 innings
        'SO9': 'strikeouts_per_nine_innings', # strikeouts per 9 innings
        'SO/W': 'strikeout_to_walk_ratio', # strikeout to walk ratio
        'LOB': 'left_on_base', # runners left on base
    })

    return df

def get_fielding_stats(year=2025):
    driver = get_webdriver()
    url = f"https://www.baseball-reference.com/leagues/majors/{year}.shtml#all_teams_standard_fielding"

    # get the url and parse the table #teams_standard_fielding
    driver.get(url)
    table = driver.find_element("css selector", "table#teams_standard_fielding")
    # read the html table into a pandas dataframe
    html_str = table.get_attribute('outerHTML')
    df = pd.read_html(StringIO(html_str))[0]
    driver.quit()

    # remove last 3 rows (totals, etc)
    df = df.iloc[:-3]

    # convert team names to team ids
    df['team_name'] = df['Tm'].apply(lambda name: match_team(name, TEAMS))
    # remove Tm column
    df = df.drop(columns=['Tm'])

    # rename columns to for better readability
    df = df.rename(columns={
        '#Fld': 'num_fielders', # number of players used in games
        'RA/G': 'runs_allowed_per_game', # runs allowed per game
        'G': 'games', # games played
        'GS': 'games_started', # games started
        'CG': 'complete_games', # complete games
        'Inn': 'innings', # innings played
        'Ch': 'chances', # defensive chances
        'PO': 'putouts', # putouts
        'A': 'assists', # assists
        'E': 'errors', # errors
        'DP': 'double_plays', # double plays
        'Fld%': 'fielding_percentage', # fielding percentage
        'Rtot': 'total_zone_runs', # total zone runs
        'Rtot/yr': 'total_zone_runs_per_year', # total zone runs per year
        'Rdrs': 'defensive_runs_saved', # defensive runs saved
        'Rdrs/yr': 'defensive_runs_saved_per_year', # defensive runs
        'Rgood': 'good_plays', # good plays
    })
    return df