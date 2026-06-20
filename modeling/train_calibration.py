from __future__ import annotations

import json
from pathlib import Path

import mlflow
import mlflow.pyfunc
import pandas as pd
import numpy as np
from mlflow.models import infer_signature
from sklearn.isotonic import IsotonicRegression

import os
from dotenv import load_dotenv

from silver.storage import get_engine
from config.domain import salary_cap_by_season

load_dotenv()

tracking_uri = os.getenv("TRACKING_URI")


experiment = "bpm-valuation"
model_name = "bpm-to-cap-trend"
artifact_dir = Path("artifacts/bpm-to-cap-trend")


min_games_played = 20


class LeagueSalaryTrendModel(mlflow.pyfunc.PythonModel):
    def __init__(self, iso):
        self.iso = iso

    def predict(self, context, model_input, params=None):
        input_df = pd.DataFrame(model_input).copy()
        bpm_column = _find_bpm_column(input_df)

        output_df = pd.DataFrame(index=input_df.index)
        output_df["trend_cap_pct"] = self.iso.predict(input_df[bpm_column])

        return output_df


def _find_bpm_column(df):
    for column in ("predicted_bpm", "bpm"):
        if column in df.columns:
            return column

    raise ValueError("Expected input to include either 'predicted_bpm' or 'bpm'.")


def load_training_data(engine):
    df = pd.read_sql("SELECT a.season, a.bref_id, a.games_played, a.bpm, c.salary, c.source FROM advanced_stats a JOIN contracts c USING (bref_id, season)", engine)
    df = df[df["season"].isin(salary_cap_by_season)]
    df['salary_cap'] = df['season'].map(salary_cap_by_season)
    df['cap_pct'] = df['salary'] / df['salary_cap']
    df = df.dropna(subset=["bpm", "cap_pct"])
    df = df[df['games_played'] >= min_games_played]

    return df.reset_index(drop=True)


def fit_trend_model(training_df):
    iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
    iso.fit(training_df["bpm"], training_df["cap_pct"])
    return iso


def write_curve_artifact(iso, training_df):
    artifact_dir.mkdir(parents=True, exist_ok=True)

    grid = np.arange(
        np.floor(training_df["bpm"].min()),
        np.ceil(training_df["bpm"].max()) + 0.1,
        0.1,
    )

    curve_df = pd.DataFrame({
        "bpm": grid.round(2),
        "trend_cap_pct": iso.predict(grid),
    })

    curve_path = artifact_dir / "trend_curve.csv"
    curve_df.to_csv(curve_path, index=False)
    return curve_path


def write_artifacts(season_values_df, model_config):
    artifact_dir.mkdir(parents=True, exist_ok=True)

    season_values_path = artifact_dir / "season_value_points.csv"
    season_values_df.to_csv(season_values_path, index=False)

    model_config_path = artifact_dir / "model_config.json"
    model_config_path.write_text(json.dumps(model_config, indent=2), encoding="utf-8")

    return season_values_path, model_config_path


def train_calibration():
    engine = get_engine()
    training_df = load_training_data(engine)
    iso = fit_trend_model(training_df)
    model = LeagueSalaryTrendModel(iso=iso)

    salary_data_sources = sorted(training_df["source"].unique().tolist())
    seasons = sorted(training_df["season"].unique().tolist())

    input_example = pd.DataFrame({"predicted_bpm": [-2.0, 0.0, 4.0]})
    output_example = model.predict(None, input_example)
    signature = infer_signature(input_example, output_example)

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment)

    with mlflow.start_run(run_name="bpm-to-cap-trend") as run:
        mlflow.set_tags({
            "project": "paid-to-play",
            "target": "trend_cap_pct",
            "model_family": "empircal_isotonic",
            "interpretation": "descriptive_league_trend",
        })

        mlflow.log_params({
            "min_games_played": min_games_played,
            "seasons": seasons,
            "salary_data_sources": salary_data_sources,
        })

        mlflow.log_metric("training_rows", len(training_df))
        mlflow.log_metric("unique_players", training_df["bref_id"].nunique())

        curve_path = write_curve_artifact(iso, training_df)
        mlflow.log_artifact(str(curve_path))

        mlflow.pyfunc.log_model(
            name="model",
            python_model=model,
            input_example=input_example,
            signature=signature,
            registered_model_name=model_name,
        )

        return run.info.run_id


if __name__ == "__main__":
    train_calibration()