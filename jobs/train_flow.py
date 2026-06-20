from prefect import flow, task
from prefect.client.schemas.schedules import CronSchedule

from bronze.contracts import ingest_contracts as fetch_bronze_contracts
from bronze.gamelogs import get_upcoming_nba_season
from silver.contracts import clean_contracts, ingest_contracts as ingest_silver_contracts
from silver.storage import get_engine
from gold.pipeline import build_gold
from modeling.promote import run_promotion_gates
from modeling.train import train_baseline
from modeling.train_calibration import train_calibration

schedule_cron = "0 8 1 8 *"
schedule_timezone = "America/New_York"


@task(name="fetch-bronze-contracts", retries=2, retry_delay_seconds=60, log_prints=True)
def fetch_bronze_contracts_task():
    season = get_upcoming_nba_season()
    return fetch_bronze_contracts(season=season)


@task(name="ingest-silver-contracts", retries=2, retry_delay_seconds=60, log_prints=True)
def ingest_silver_contracts_task():
    season = get_upcoming_nba_season()
    contracts_df = clean_contracts(season=season, require_non_empty=True)
    engine = get_engine()
    ingest_silver_contracts(contracts_df, engine)
    print(f"Ingested {len(contracts_df)} contract rows for {season}")


@task(name="rebuild-feature-snapshots", retries=2, retry_delay_seconds=60, log_prints=True)
def rebuild_feature_snapshots():
    engine = get_engine()
    build_gold(engine)


@task(name="train-bpm-projector", retries=2, retry_delay_seconds=60, log_prints=True)
def train_bpm_projector():
    return train_baseline()


@task(name="train-calibration", retries=2, retry_delay_seconds=60, log_prints=True)
def train_calibration_model():
    return train_calibration()


@task(name="promotion-gate", retries=1, retry_delay_seconds=30, log_prints=True)
def promotion_gate(bpm_run_id, calibration_run_id):
    return run_promotion_gates(bpm_run_id, calibration_run_id)


@flow(name="paid-to-play-annual-retrain", log_prints=True)
def annual_retrain_pipeline():
    rebuild_feature_snapshots()
    bpm_run_id = train_bpm_projector()
    fetch_bronze_contracts_task()
    ingest_silver_contracts_task()
    calibration_run_id = train_calibration_model()
    promotion_gate(bpm_run_id, calibration_run_id)


if __name__ == "__main__":
    annual_retrain_pipeline.serve(
        name="annual-retrain",
        schedule=CronSchedule(
            cron=schedule_cron,
            timezone=schedule_timezone,
        ),
        tags=["annual", "off-season"],
    )
