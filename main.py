from bronze.pipeline import run_static
from silver.pipeline import *
from gold.pipeline import build_gold
from silver.storage import get_engine


if __name__ == "__main__":
    engine = get_engine()
    load_players(engine)
    load_stats(engine)
    load_contracts(engine)
    build_gold(engine)
    # run_static()
    # load_ids()
    # process_and_ingest_gamelogs()
    # ids_df, players_df = clean_players()
    # print(players_df)
    pass