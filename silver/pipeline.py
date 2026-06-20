from silver.players import clean_players, ingest_ids, ingest_players
from silver.advanced_stats import process_advanced_stats
from silver.gamelogs import process_gamelogs
from silver.contracts import clean_contracts, clean_historical_salaries, ingest_contracts


def load_players(engine):
    ids_df, players_df = clean_players()
    ingest_ids(ids_df, engine)
    ingest_players(players_df, engine)


def load_stats(engine):
    process_advanced_stats(engine)
    process_gamelogs(engine)


def load_contracts(engine):
    contracts_df = clean_contracts()
    ingest_contracts(contracts_df, engine)


def load_historical_contracts(engine):
    historical_df = clean_historical_salaries()
    ingest_contracts(historical_df, engine)
    print(f"Ingested {len(historical_df)} historical salary rows")