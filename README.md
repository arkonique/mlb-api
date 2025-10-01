# MLB Analytics API

A Flask-based API for exploring MLB team analytics, including power rankings, standings, odds, player stats, volatility, consistency, clustering, and advanced statistical models (ACF stability, Granger causality, HMM states).

Currently online at - [https://mlb.riddhimandal.com]
---

## Features

* **Data ingestion & caching**

  * Loads pre-saved CSV/JSON files from `data/` when available
  * Falls back to dynamic scraping & computation functions (`sunday_power`, `get_batting_stats`, etc.)
  * Keeps results in memory for speed

* **Endpoints for core data**

  * `/teams` — team metadata (names + codes)
  * `/power` — weekly power rankings
  * `/standings` — MLB standings
  * `/odds` — playoff odds
  * `/batting`, `/pitching`, `/fielding` — player/team performance stats

* **Analytics endpoints**

  * `/ranks` — combined view of power rankings vs MLB standings
  * `/kdes` — KDE + histogram of ranking changes
  * `/volatility` — ranking volatility over time
  * `/stability` & `/consistency` — ACF-based measures of rank dynamics
  * `/granger` — Granger causality (power → MLB standings)
  * `/similarity` — trajectory similarity between two teams
  * `/clusters` — k-means clustering of season stats
  * `/hmm` — hidden Markov model for team performance states

---

## Installation

Clone the repository and install dependencies:

```bash
git clone <your-repo-url>
cd mlb-api
pip install -r requirements.txt
```

You’ll also need **Google Chrome** + **chromedriver** installed if scraping is used.

---

## Running locally

```bash
python app.py
```

The API will start at [http://localhost:5000](http://localhost:5000).

---

## Deployment (Heroku)

Make sure you have a **Procfile**:

```
web: gunicorn app:app
```

Deploy:

```bash
git push heroku main
```

---

## Example Usage

* Get power rankings (default 2025):

```bash
curl http://localhost:5000/power
```

* Get team metadata:

```bash
curl http://localhost:5000/teams?year=2025
```

* Compare rankings for specific teams:

```bash
curl "http://localhost:5000/ranks?teams=TOR&teams=NYY&mode=both"
```

* Run Granger causality test:

```bash
curl "http://localhost:5000/granger?team=TOR&max_lag=3"
```

---

## Data Sources

* Uses a mix of **saved CSVs/JSON** in the `data/` directory and **scraping/stats functions** defined in the repo.
* Cached in memory per session for efficiency.

---

## Notes

* Some endpoints depend on others being loaded first (e.g., `/ranks` requires `/power` and `/standings`).
* If running on Heroku, set `WEB_CONCURRENCY=1` to avoid multiple Chrome workers.
* Data freshness depends on CSVs and scraping functions.
  
---

# API Endpoints

> Base URL (local): `http://localhost:5000/` 

## Quick Index

| Endpoint       | Method | Purpose                               | Notes                                                                                |
| -------------- | ------ | ------------------------------------- | ------------------------------------------------------------------------------------ |
| `/`            | GET    | Health check                          | Returns `{ "ok": true }`.                                                            |
| `/teams`       | GET    | Team metadata (names & codes)         | Reads from `data/teams_{year}.json` and `data/tms_{year}.json` if present.           |
| `/power`       | GET    | Weekly power rankings                 | Caches in memory; falls back to `data/power_rankings_{year}.csv` or `sunday_power`.  |
| `/standings`   | GET    | MLB standings time series             | Caches in memory; CSV fallback `data/standings_{year}.csv` else `sunday_standings`.  |
| `/odds`        | GET    | Playoff odds time series              | Caches in memory; CSV fallback `data/odds_{year}.csv` else `sunday_odds`.            |
| `/batting`     | GET    | Batting stats snapshot/series         | CSV fallback `data/batting_stats_{year}.csv` else `get_batting_stats`.               |
| `/pitching`    | GET    | Pitching stats snapshot/series        | CSV fallback `data/pitching_stats_{year}.csv` else `get_pitching_stats`.             |
| `/fielding`    | GET    | Fielding stats snapshot/series        | CSV fallback `data/fielding_stats_{year}.csv` else `get_fielding_stats`.             |
| `/ranks`       | GET    | Power vs MLB ranks for selected teams | Requires `/power` & `/standings` to be loaded first.                                 |
| `/kdes`        | GET    | KDE + histogram of Δrank              | Requires `/power` & `/standings`.                                                    |
| `/volatility`  | GET    | Rank volatility time series           | Requires `/power` & `/standings`.                                                    |
| `/stability`   | GET    | ACF-based stability (Δ Fisher-z)      | Requires `/power` & `/standings`.                                                    |
| `/consistency` | GET    | ACF values (consistency)              | Requires `/power` & `/standings`.                                                    |
| `/granger`     | GET    | Granger causality (power → MLB)       | Requires `/power` & `/standings`.                                                    |
| `/similarity`  | GET    | Trajectory similarity stats           | Requires `/power` & `/standings`.                                                    |
| `/clusters`    | GET    | Season clustering (k-means)           | Needs standings, odds, batting, pitching, fielding loaded.                           |
| `/hmm`         | GET    | Hidden Markov Model states            | Builds power features, fits HMM for a team.                                          |

---

## Endpoint Details & Examples

### `/` — Health

* **Method:** GET
* **Returns:** `{ "ok": true }`
* **Example:**

  ```bash
  curl http://localhost:5000/
  ```



---

### `/teams`

* **Method:** GET
* **Query:** `year` (int, default `2025`)
* **Notes:** If `data/teams_{year}.json` and `data/tms_{year}.json` exist, loads those; otherwise returns whatever is cached in memory.
* **Returns:** `{ "teams": {...}, "tms": {...} }`
* **Example:**

  ```bash
  curl "http://localhost:5000/teams?year=2025"
  ```



---

### `/power`

* **Method:** GET
* **Query:** `year` (int, default `2025`)
* **Logic:**

  1. Serve from in-memory cache if same `YEAR`
  2. Else try `data/power_rankings_{year}.csv`
  3. Else compute via `sunday_power(year)` (also sets `TEAMS`/`TMS`)
* **Returns:** `{ "power": [...], "teams": {...}, "tms": {...} }`
* **Example:**

  ```bash
  curl "http://localhost:5000/power?year=2025"
  ```



---

### `/standings`

* **Method:** GET
* **Query:** `year` (int, default `2025`)
* **Logic:** cache → `data/standings_{year}.csv` → `sunday_standings(year)`
* **Returns:** `{ "standings": [...] }`
* **Example:**

  ```bash
  curl "http://localhost:5000/standings?year=2025"
  ```



---

### `/odds`

* **Method:** GET
* **Query:** `year` (int, default `2025`)
* **Logic:** cache → `data/odds_{year}.csv` → `sunday_odds(year)`
* **Returns:** `{ "odds": [...] }`
* **Example:**

  ```bash
  curl "http://localhost:5000/odds?year=2025"
  ```



---

### `/batting`

* **Method:** GET
* **Query:** `year` (int, default `2025`)
* **Logic:** cache → `data/batting_stats_{year}.csv` → `get_batting_stats(year)`
* **Returns:** `{ "batting": [...] }`
* **Example:**

  ```bash
  curl "http://localhost:5000/batting?year=2025"
  ```



---

### `/pitching`

* **Method:** GET
* **Query:** `year` (int, default `2025`)
* **Logic:** cache → `data/pitching_stats_{year}.csv` → `get_pitching_stats(year)`
* **Returns:** `{ "pitching": [...] }`
* **Example:**

  ```bash
  curl "http://localhost:5000/pitching?year=2025"
  ```



---

### `/fielding`

* **Method:** GET
* **Query:** `year` (int, default `2025`)
* **Logic:** cache → `data/fielding_stats_{year}.csv` → `get_fielding_stats(year)`
* **Returns:** `{ "fielding": [...] }`
* **Example:**

  ```bash
  curl "http://localhost:5000/fielding?year=2025"
  ```



---

### `/ranks`

* **Method:** GET
* **Requires:** `/power` and `/standings` loaded first (in memory)
* **Query:**

  * `teams` (repeatable) — team codes (e.g., `teams=TOR&teams=NYY`)
  * `mode` — one of `power`, `mlb`, `diff`, `both` (default `both`)
* **Returns:** `{ "ranks": [...] }` (tidy table for plotting/compare)
* **Example:**

  ```bash
  curl "http://localhost:5000/ranks?teams=TOR&teams=NYY&mode=both"
  ```



---

### `/kdes`

* **Method:** GET
* **Requires:** `/power` & `/standings`
* **Query:**

  * `teams` (repeatable) — team codes (optional; if omitted, logic in your builder decides scope)
  * `source` — `power` or `mlb` (default `power`)
* **Returns:**

  ```json
  {
    "kde_data": [...],
    "hist_data": [...],
    "peaks": {...},
    "bandwidth": <float>
  }
  ```
* **Example:**

  ```bash
  curl "http://localhost:5000/kdes?teams=TOR&source=power"
  ```



---

### `/volatility`

* **Method:** GET
* **Requires:** `/power` & `/standings`
* **Query:**

  * `teams` (repeatable) — team codes
  * `source` — `power` or `mlb` (default `power`)
* **Returns:** `{ "volatility_data": [...] }`
* **Example:**

  ```bash
  curl "http://localhost:5000/volatility?teams=TOR&source=mlb"
  ```



---

### `/stability`

* **Method:** GET
* **Requires:** `/power` & `/standings`
* **Query:**

  * `team` — single team code (e.g., `TOR`)
  * `source` — `power` or `mlb` (default `power`)
  * `max_lag` — int, default `4`
* **Returns:** `{ "stability_data": [...] }`
* **Example:**

  ```bash
  curl "http://localhost:5000/stability?team=TOR&source=power&max_lag=4"
  ```



---

### `/consistency`

* **Method:** GET
* **Requires:** `/power` & `/standings`
* **Query:**

  * `team` — single team code
  * `source` — `power` or `mlb` (default `power`)
  * `max_lag` — int, default `4`
* **Returns:** `{ "consistency_data": [...] }` (raw ACF values)
* **Example:**

  ```bash
  curl "http://localhost:5000/consistency?team=TOR&source=mlb&max_lag=3"
  ```



---

### `/granger`

* **Method:** GET
* **Requires:** `/power` & `/standings`
* **Query:**

  * `team` — single team code
  * `max_lag` — int, default `4`
* **Returns:**

  ```json
  {
    "granger_data": [...],
    "stats": {...}
  }
  ```
* **Example:**

  ```bash
  curl "http://localhost:5000/granger?team=TOR&max_lag=4"
  ```



---

### `/similarity`

* **Method:** GET
* **Requires:** `/power` & `/standings`
* **Query:**

  * `team_a` — team code A
  * `team_b` — team code B
  * `source` — `power` or `mlb` (default `power`)
* **Returns:** `{ "similarity_stats": {...} }`
* **Example:**

  ```bash
  curl "http://localhost:5000/similarity?team_a=TOR&team_b=NYY&source=power"
  ```



---

### `/clusters`

* **Method:** GET
* **Requires:** `/standings`, `/odds`, `/batting`, `/pitching`, `/fielding` (all loaded)
* **Query:**

  * `k` — number of clusters (int, default `6`)
* **Returns:** `{ "clusters": [...] }` where `teams` is an array per cluster
* **Example:**

  ```bash
  curl "http://localhost:5000/clusters?k=6"
  ```



---

### `/hmm`

* **Method:** GET
* **Requires:** (implicitly uses current `POWER`, `TEAMS`, `TMS`; builds features internally)
* **Query:**

  * `team` — team code (required)
* **Returns:**

  ```json
  {
    "states": [...],
    "stats": {
      "P": [[...]], "P_labels": ["Good","Mediocre","Bad"],
      "pi": [...],
      "means": [[...]],
      "mean_cols": ["level_dev","chg_z","mom3_z"],
      "init": "quant",
      "n_used": 0
    }
  }
  ```
* **Example:**

  ```bash
  curl "http://localhost:5000/hmm?team=TOR"
  ```



---

## Usage Tips

* Load the foundational datasets first (e.g., call `/power` and `/standings`) so downstream analytics endpoints have their inputs warmed in memory. Many endpoints return `400` if prerequisites aren’t loaded. 
* CSV/JSON files in `data/` are preferred when present; otherwise the API triggers scraping/compute functions defined in your code. 
* Everything is **GET** for now; results are JSON and generally return tidy records suitable for plotting/dataframes. 
