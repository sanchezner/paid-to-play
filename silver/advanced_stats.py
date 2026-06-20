from silver.storage import pull_json, list_keys
from sqlalchemy import text
import pandas as pd


def process_advanced_stats(engine):
    keys = list_keys('bronze/advanced_stats/')
    for key in keys:
        advanced_stats_json = pull_json(key)
        if not advanced_stats_json:
            print(f"[warn] Skipping empty advanced stats object: {key}")
            continue

        advanced_stats_df = pd.DataFrame(advanced_stats_json)
        advanced_stats_df.rename(columns={'bbref_id': 'bref_id', 'games': 'games_played'}, inplace=True)

        advanced_stats_df = advanced_stats_df[['bref_id', 'season', 'games_played', 'ws', 'ws_per_48', 'vorp', 'bpm']]
        ingest_advanced_stats(advanced_stats_df, engine)

    print('Successfully processed advanced stats')

        
def ingest_advanced_stats(advanced_stats_df, engine):
    advanced_stats_df.to_sql('advanced_stats_staging', engine, if_exists='replace', index=False)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO advanced_stats(bref_id, season, games_played, ws, ws_per_48, vorp, bpm)
            SELECT s.bref_id, s.season, s.games_played, s.ws, s.ws_per_48, s.vorp, s.bpm
            FROM advanced_stats_staging s
            WHERE EXISTS (SELECT 1 FROM ids i WHERE i.bref_id = s.bref_id)
            ON CONFLICT(bref_id, season) DO NOTHING
        """))