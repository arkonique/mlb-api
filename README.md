# MLB Analytics API

A Flask-based API for exploring MLB team analytics, including power rankings, standings, odds, player stats, volatility, consistency, clustering, and advanced statistical models (ACF stability, Granger causality, HMM states).

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
