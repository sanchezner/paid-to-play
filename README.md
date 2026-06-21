# paid to play

Daily-refreshed NBA player valuation chart: every dot is an active player plotted on **predicted BPM** (horizontal) vs **salary cap %** (vertical). A dashed trend line shows what the league has historically paid for a given level of expected production.

**Live demo:** [sanchezner.com/paid-to-play](https://www.sanchezner.com/paid-to-play)

---

## What this project does

- Ingests game logs, advanced stats, and contracts from public sources
- Trains an XGBoost model to project full-season BPM from in-season snapshots
- Fits a calibration curve (BPM → fair cap %) on historical salary data
- Scores active players daily and writes static JSON snapshots for the frontend

The frontend is a React + Observable Plot scatter chart with a searchable player table and per-player season trajectory view. No live API — data refreshes once per day via batch pipeline.

For full architecture decisions and modeling rationale, see [my blog](https://sanchezner.com/2026/06/21/building-paid-to-play).

---

## Project structure

```
bronze/       Raw JSON from nba_api + Basketball Reference (stored in S3)
silver/       Cleaned Postgres tables: players, gamelogs, stats, contracts
gold/         Point-in-time feature snapshots for training and inference
modeling/     MLflow-tracked training, promotion gates, inference
serving/      Prediction scoring and static JSON snapshot export
jobs/         Prefect flows: daily pipeline + annual retrain
frontend/     React + Vite app (reads from public/data/*.json)
artifacts/    Exported model configs, feature columns, eval metrics
data/         ID mappings and manually matched historical salary CSVs
```

---

## Prerequisites

- Python 3.12+
- Node.js 20+
- Postgres database (I used Neon)
- AWS S3 bucket with bronze-layer data (or run bronze ingest yourself)
- MLflow local store (`mlflow.db` + `mlruns/` — generated on first train run)

---

## Setup

### 1. Environment variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

| Variable | Purpose |
|---|---|
| `CONN_STRING` | Postgres connection string |
| `S3_BUCKET` | Bronze-layer JSON in S3 |
| `TRACKING_URI` | MLflow tracking backend |
| `AWS_*` | S3 access via boto3 |
| `PREFECT_*` | Prefect Cloud (scheduled flows only) |

### 2. Python backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-worker.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

---

## Running locally

### Frontend only

The committed JSON snapshots in `frontend/public/data/` are enough to browse the chart without a database:

```bash
cd frontend
npm run dev
```

Open the URL Vite prints (typically `http://localhost:5173/paid-to-play/`).

### Daily pipeline (manual)

Runs bronze ingest → silver gamelogs → gold features → inference → snapshot refresh:

```bash
source .venv/bin/activate
python -m jobs.daily
```

Writes updated JSON to `frontend/public/data/`.

### Scheduled flows (Prefect)

Requires Prefect Cloud credentials in `.env`:

```bash
python -m jobs.daily_flow    # daily at 6am ET
python -m jobs.train_flow    # annual retrain, Aug 1 at 8am ET
```

### Initial / backfill load

`main.py` loads static silver tables and rebuilds gold features:

```bash
python main.py
```

---

## Docker

```bash
docker compose up daily-worker   # daily pipeline
docker compose up annual-worker  # annual retrain
```

The Dockerfile expects a local `mlflow.db` and `mlruns/` directory (gitignored, created during training). Run at least one training job locally before building the image.

---

## Data sources

- [nba_api](https://github.com/swar/nba_api) — game logs and player metadata
- [Basketball Reference](https://www.basketball-reference.com) — advanced stats (via Wikidata ID mapping)
- [ESPN Salaries](https://www.espn.com/nba/salaries) — historical contract data
- [Wikidata](https://www.wikidata.org) — cross-source player ID resolution

---

## Author

[Sanchezner Orange](https://www.sanchezner.com)
