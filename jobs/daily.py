import os
from datetime import date, timedelta

from dotenv import load_dotenv

from bronze.gamelogs import get_current_nba_season
from bronze.pipeline import run_incremental
from gold.inference_features import build_inference_features, validate_inference_features
from serving.predictions import score_unscored
from serving.publish import publish_snapshot
from serving.snapshot import refresh_snapshot
from silver.gamelogs import process_gamelogs
from silver.storage import get_engine

output_dir = "frontend/public/data"


def resolve_daily_context(reference_date=None):
    yesterday = (reference_date or date.today()) - timedelta(days=1)
    season = get_current_nba_season(yesterday)
    return yesterday, season


def ingest_bronze():
    run_incremental()


def ingest_silver(game_date):
    load_dotenv()
    process_gamelogs(get_engine(), game_date=game_date)


def build_and_validate_features(season):
    load_dotenv()
    engine = get_engine()
    new_rows = build_inference_features(engine, season)
    validate_inference_features(engine, season)
    return new_rows


def score_predictions(season):
    load_dotenv()
    score_unscored(get_engine(), season, os.getenv('TRACKING_URI'))


def maybe_refresh_snapshot(season, new_rows, game_date, output_dir=output_dir):
    if new_rows:
        refresh_snapshot(season, output_dir)
        publish_snapshot(output_dir)
    else:
        print(f"No new games for {game_date}; snapshot left unchanged")


def run_daily(reference_date=None):
    yesterday, season = resolve_daily_context(reference_date)

    ingest_bronze()
    ingest_silver(yesterday)
    new_rows = build_and_validate_features(season)
    score_predictions(season)
    maybe_refresh_snapshot(season, new_rows, yesterday)


if __name__ == "__main__":
    run_daily()
