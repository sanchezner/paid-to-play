from datetime import date, timedelta
from nba_api.stats.endpoints import PlayerGameLogs
import pandas as pd
from bronze.storage import upload_json
from config.domain import training_start_season


def get_current_nba_season(reference_date=None):
    reference_date = reference_date or date.today()
    season_start_year = reference_date.year if reference_date.month >= 10 else reference_date.year - 1
    season_end_year = str(season_start_year + 1)[-2:]

    return f"{season_start_year}-{season_end_year}"


def get_upcoming_nba_season(reference_date=None):
    current = get_current_nba_season(reference_date)
    start_year = int(current.split("-")[0]) + 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def get_last_completed_season(reference_date=None):
    reference_date = reference_date or date.today()
    current = get_current_nba_season(reference_date)

    if 7 <= reference_date.month <= 9:
        return current

    start_year = int(current.split("-")[0]) - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def get_train_season_splits(reference_date=None, train_start=training_start_season):
    reference_date = reference_date or date.today()
    test_season = get_last_completed_season(reference_date)
    val_start_year = int(test_season.split("-")[0]) - 1
    val_season = f"{val_start_year}-{str(val_start_year + 1)[-2:]}"

    train_end_year = val_start_year - 1
    train_start_year = int(train_start.split("-")[0])
    if train_end_year < train_start_year:
        raise ValueError(
            f"Not enough seasons for train/val/test split "
            f"(train_start={train_start}, test={test_season})"
        )

    train_end = f"{train_end_year}-{str(train_end_year + 1)[-2:]}"
    train_seasons = tuple(get_nba_seasons(train_start, train_end))
    val_seasons = (val_season,)
    test_seasons = (test_season,)

    excluded = {get_upcoming_nba_season(reference_date)}
    current = get_current_nba_season(reference_date)
    if current not in test_seasons:
        excluded.add(current)

    return {
        "train_seasons": train_seasons,
        "val_seasons": val_seasons,
        "test_seasons": test_seasons,
        "excluded_seasons": tuple(sorted(excluded)),
    }


def get_nba_seasons(start_season=training_start_season, end_season=None):
    end_season = end_season or get_current_nba_season()
    start_year = int(start_season.split("-")[0])
    end_year = int(end_season.split("-")[0])

    return [f"{year}-{str(year + 1)[-2:]}" for year in range(start_year, end_year + 1)]


def format_nba_api_date(game_date):
    if isinstance(game_date, date):
        return game_date.strftime("%m/%d/%Y")

    return pd.to_datetime(game_date).strftime("%m/%d/%Y")


def format_partition_date(game_date):
    return pd.to_datetime(game_date).date().isoformat()


def get_game_log_records(season=None, season_type="Regular Season", game_date=None):
    season = season or get_current_nba_season()
    player_game_log_params = {
        "season_nullable": season,
        "season_type_nullable": season_type,
    }

    if game_date:
        nba_api_date = format_nba_api_date(game_date)
        player_game_log_params["date_from_nullable"] = nba_api_date
        player_game_log_params["date_to_nullable"] = nba_api_date

    player_game_logs = PlayerGameLogs(**player_game_log_params)
    game_logs_df = player_game_logs.player_game_logs.get_data_frame()

    return game_logs_df.to_dict(orient="records")


def write_game_log_partition(game_date, game_log_records):
    partition_date = format_partition_date(game_date)
    key = f"bronze/gamelogs/game_date={partition_date}/response.json"

    try:
        upload_json(game_log_records, key)
        print(f"Successfully uploaded {partition_date} game logs")
    except Exception as e:
        print(f"Error uploading object: {e}")


def ingest_game_log_records_by_date(game_log_records):
    if not game_log_records:
        print("Skipping upload: no game logs found.")
        return

    game_logs_df = pd.DataFrame(game_log_records)
    for game_date, game_date_df in game_logs_df.groupby("GAME_DATE"):
        write_game_log_partition(game_date, game_date_df.to_dict(orient="records"))


def backfill_training_game_logs(start_season=training_start_season, end_season=None, season_type="Regular Season"):
    for season in get_nba_seasons(start_season, end_season):
        print(f"Getting {season} {season_type} game logs...")
        game_log_records = get_game_log_records(season=season, season_type=season_type)
        ingest_game_log_records_by_date(game_log_records)


def ingest_yesterdays_game_logs(reference_date=None, season_type="Regular Season"):
    game_date = (reference_date or date.today()) - timedelta(days=1)
    season = get_current_nba_season(game_date)
    game_log_records = get_game_log_records(
        season=season,
        season_type=season_type,
        game_date=game_date,
    )
    ingest_game_log_records_by_date(game_log_records)