import json
from pathlib import Path

import mlflow
import pandas as pd
from sqlalchemy import text

from config.domain import salary_cap_by_season
from modeling.predict import load_models, predict_bpm, predict_trend_cap_pct
from silver.storage import upsert_with_visibility


def load_feature_columns():
    artifacts_dir = Path('artifacts/bpm-projector')
    with open(artifacts_dir / 'feature_columns.json', 'r') as f:
        return json.load(f)


def get_champion_version(model_name='bpm-projector'):
    client = mlflow.tracking.MlflowClient()
    return client.get_model_version_by_alias(model_name, 'champion').version


def create_predictions_table(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS predictions (
                nba_id INTEGER NOT NULL REFERENCES ids(nba_id),
                bref_id VARCHAR NOT NULL REFERENCES ids(bref_id),
                season VARCHAR NOT NULL,
                game_number INTEGER NOT NULL,
                snapshot_date DATE NOT NULL,
                predicted_bpm DOUBLE PRECISION NOT NULL,
                trend_cap_pct DOUBLE PRECISION NOT NULL,
                salary BIGINT,
                cap_pct DOUBLE PRECISION,
                delta_from_trend DOUBLE PRECISION,
                model_version VARCHAR NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (nba_id, season, game_number)
            )
        """))


def get_unscored_features(engine, season):
    sql = text("""
        SELECT f.*
        FROM inference_features f
        WHERE f.season = :season
          AND NOT EXISTS (
              SELECT 1
              FROM predictions p
              WHERE p.nba_id = f.nba_id
                AND p.season = f.season
                AND p.game_number = f.game_number
          )
        ORDER BY f.snapshot_date, f.nba_id
    """)
    return pd.read_sql(sql, engine, params={'season': str(season)})


def score_unscored(engine, season, tracking_uri):
    create_predictions_table(engine)

    features_df = get_unscored_features(engine, season)
    if features_df.empty:
        print(f"Predictions: nothing to score for {season}")
        return 0

    bpm_model, trend_model = load_models(tracking_uri)
    feature_columns = load_feature_columns()
    model_version = get_champion_version()

    features_df['milestone_n'] = features_df['game_number']

    features_df['predicted_bpm'] = predict_bpm(features_df, feature_columns, bpm_model)
    features_df['trend_cap_pct'] = predict_trend_cap_pct(features_df['predicted_bpm'], trend_model)

    contracts_sql = text('SELECT bref_id, salary FROM contracts WHERE season = :season')
    contracts_df = pd.read_sql(contracts_sql, engine, params={'season': str(season)})

    scored_df = features_df.merge(contracts_df, on='bref_id', how='left')
    scored_df['salary_cap'] = scored_df['season'].map(salary_cap_by_season)
    scored_df['cap_pct'] = scored_df['salary'] / scored_df['salary_cap']
    scored_df['delta_from_trend'] = scored_df['cap_pct'] - scored_df['trend_cap_pct']
    scored_df['model_version'] = str(model_version)

    output_columns = [
        'nba_id',
        'bref_id',
        'season',
        'game_number',
        'snapshot_date',
        'predicted_bpm',
        'trend_cap_pct',
        'salary',
        'cap_pct',
        'delta_from_trend',
        'model_version',
    ]
    scored_df[output_columns].to_sql(
        'predictions_staging', engine, if_exists='replace', index=False
    )

    upsert_with_visibility(
        engine,
        staging_table='predictions_staging',
        insert_sql="""
            INSERT INTO predictions (
                nba_id, bref_id, season, game_number, snapshot_date,
                predicted_bpm, trend_cap_pct, salary, cap_pct,
                delta_from_trend, model_version
            )
            SELECT
                s.nba_id::integer,
                s.bref_id,
                s.season,
                s.game_number::integer,
                s.snapshot_date::date,
                s.predicted_bpm::double precision,
                s.trend_cap_pct::double precision,
                s.salary::bigint,
                s.cap_pct::double precision,
                s.delta_from_trend::double precision,
                s.model_version
            FROM predictions_staging s
            ON CONFLICT (nba_id, season, game_number) DO NOTHING
            RETURNING 1
        """,
        label='predictions',
    )

    return len(scored_df)
