from datetime import date

from prefect import flow, task
from prefect.client.schemas.schedules import CronSchedule

from jobs.daily import (
    build_and_validate_features,
    ingest_bronze,
    ingest_silver,
    maybe_refresh_snapshot,
    resolve_daily_context,
    score_predictions,
)

schedule_cron = "0 6 * * *"
schedule_timezone = "America/New_York"


@task(name="bronze-ingest", retries=2, retry_delay_seconds=60, log_prints=True)
def bronze_ingest():
    ingest_bronze()


@task(name="silver-gamelogs", retries=2, retry_delay_seconds=60, log_prints=True)
def silver_gamelogs(yesterday_iso: str):
    ingest_silver(date.fromisoformat(yesterday_iso))


@task(name="gold-features", retries=2, retry_delay_seconds=60, log_prints=True)
def gold_features(season: str) -> int:
    return build_and_validate_features(season)


@task(name="score-predictions", retries=2, retry_delay_seconds=60, log_prints=True)
def score_predictions_task(season: str):
    score_predictions(season)


@task(name="refresh-snapshot", retries=1, retry_delay_seconds=30, log_prints=True)
def refresh_snapshot_task(season: str, new_rows: int, yesterday_iso: str):
    maybe_refresh_snapshot(season, new_rows, date.fromisoformat(yesterday_iso))


@flow(name="paid-to-play-daily", log_prints=True)
def daily_pipeline(reference_date: str | None = None):
    ref = date.fromisoformat(reference_date) if reference_date else None
    yesterday, season = resolve_daily_context(ref)
    yesterday_iso = yesterday.isoformat()

    bronze_ingest()
    silver_gamelogs(yesterday_iso)
    new_rows = gold_features(season)
    score_predictions_task(season)
    refresh_snapshot_task(season, new_rows, yesterday_iso)


if __name__ == "__main__":
    daily_pipeline.serve(
        name="daily-6am-et",
        schedule = CronSchedule(
            cron=schedule_cron,
            timezone=schedule_timezone,
        ),
        tags=["daily", "in-season"],
    )
