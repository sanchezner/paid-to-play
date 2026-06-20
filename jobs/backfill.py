"""One-time historical backfill for the training window (1999-00 onward).

Bronze: game logs + advanced stats (+ optional ESPN salary scrape/match)
Silver: process bronze partitions + ingest historical salaries
Gold:   rebuild feature_snapshots

After this completes, retrain both models:
  python -m modeling.train
  python -m modeling.train_calibration
"""

from __future__ import annotations

from dotenv import load_dotenv

from config.domain import training_start_season
from bronze.advanced_stats import ingest_advanced_stats
from bronze.gamelogs import backfill_training_game_logs, get_last_completed_season
from bronze.scrape_espn_salaries import main as scrape_espn_salaries
from silver.match_espn_to_bref import main as match_espn_salaries
from silver.pipeline import load_historical_contracts, load_stats
from silver.storage import get_engine
from gold.pipeline import build_gold


def backfill_bronze_stats(end_season=None):
    print(f"Backfilling game logs from {training_start_season} through {end_season or 'latest completed'}...")
    backfill_training_game_logs(
        start_season=training_start_season,
        end_season=end_season,
    )

    print(f"Backfilling advanced stats from {training_start_season} through {end_season or 'latest completed'}...")
    ingest_advanced_stats(
        start_season=training_start_season,
        end_season=end_season,
    )


def backfill_salaries():
    print("Scraping ESPN historical salaries...")
    scrape_espn_salaries()

    print("Matching ESPN names to Basketball Reference IDs...")
    match_espn_salaries()


def backfill_silver():
    engine = get_engine()
    print("Processing bronze game logs and advanced stats into silver...")
    load_stats(engine)

    print("Ingesting historical salary contracts...")
    load_historical_contracts(engine)


def backfill_gold():
    engine = get_engine()
    print("Rebuilding gold feature_snapshots...")
    build_gold(engine)


def run_backfill(*, bronze_stats=True, salaries=True, silver=True, gold=True, end_season=None):
    load_dotenv()

    if salaries:
        backfill_salaries()

    if bronze_stats:
        backfill_bronze_stats(end_season=end_season)

    if silver:
        backfill_silver()

    if gold:
        backfill_gold()

    print("Historical backfill complete.")


def main():
    # adjust accordingly; all True if for the first time
    run_backfill(
        bronze_stats=False,
        salaries=False,
        silver=False,
        gold=False,
        end_season=get_last_completed_season(),
    )


if __name__ == "__main__":
    main()
