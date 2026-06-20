from bronze.advanced_stats import ingest_advanced_stats
from bronze.contracts import ingest_contracts, ingest_payroll
from bronze.entities import ingest_players, ingest_teams
from bronze.gamelogs import backfill_training_game_logs, ingest_yesterdays_game_logs
from config.domain import training_start_season


def run_static(): # data that only needs to be run once/season
    # ingest_players()
    # ingest_teams()
    ingest_contracts()
    ingest_payroll()
    ingest_advanced_stats(start_season=training_start_season)
    # backfill_training_game_logs(start_season=training_start_season)
    pass


def run_incremental():
    ingest_yesterdays_game_logs()