import os

from dotenv import load_dotenv

from gold.inference_features import build_inference_features, validate_inference_features
from serving.predictions import score_unscored
from serving.snapshot import refresh_snapshot
from silver.storage import get_engine


def backfill_predictions(season, output_dir="frontend/public/data"):
    load_dotenv()
    engine = get_engine()

    build_inference_features(engine, season)
    validate_inference_features(engine, season)
    score_unscored(engine, season, os.getenv("TRACKING_URI"))
    refresh_snapshot(season, output_dir)


if __name__ == "__main__":
    backfill_predictions("2025-26")
