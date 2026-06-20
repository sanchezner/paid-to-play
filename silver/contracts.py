from pathlib import Path

import pandas as pd
from sqlalchemy import text

from bronze.gamelogs import get_current_nba_season
from silver.storage import pull_json, list_keys


historical_salaries_path = Path("data/manual/historical_salaries_matched.csv")


def get_contracts_key(season):
    season_end_year = int(season.split("-")[0]) + 1
    candidates = [
        f"bronze/contracts/season={season}/response.json",
        f"bronze/contracts/season={season_end_year}/response.json",
    ]
    available_keys = set(list_keys("bronze/contracts/"))

    for key in candidates:
        if key in available_keys:
            return key

    raise FileNotFoundError(f"No bronze contracts object found for {season}")


def clean_contracts(season=None, *, require_non_empty=False):
    season = season or get_current_nba_season()
    contracts_json = pull_json(get_contracts_key(season))

    if not contracts_json:
        if require_non_empty:
            raise ValueError(f"No contract data found for season {season}")
        return pd.DataFrame(columns=['bref_id', 'season', 'salary', 'source'])

    contracts_df = pd.DataFrame(contracts_json)
    contracts_df['season'] = season
    contracts_df.rename(columns={'bbref_id': 'bref_id', 'y1': 'salary'}, inplace=True)
    contracts_df['source'] = 'bref_api'
    contracts_df = contracts_df[['bref_id', 'season', 'salary', 'source']]

    if require_non_empty and contracts_df.empty:
        raise ValueError(f"No contract rows parsed for season {season}")

    return contracts_df


def clean_historical_salaries():
    if not historical_salaries_path.exists():
        raise FileNotFoundError(
            f"{historical_salaries_path} not found. "
            f"Run bronze/match_espn_to_bref.py first."
        )

    df = pd.read_csv(historical_salaries_path)
    df['source'] = 'espn_manual'
    return df[['bref_id', 'season', 'salary', 'source']]


def ingest_contracts(contracts_df, engine):
    contracts_df.to_sql('contracts_staging', engine, if_exists='replace', index=False)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO contracts(bref_id, season, salary, source)
            SELECT DISTINCT ON (s.bref_id, s.season)
                s.bref_id,
                s.season,
                NULLIF(s.salary::text, '')::integer,
                s.source
            FROM contracts_staging s
            WHERE EXISTS (SELECT 1 FROM ids i WHERE i.bref_id = s.bref_id)
              AND NULLIF(s.salary::text, '') IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM contracts c
                  WHERE c.bref_id = s.bref_id
                    AND c.season = s.season
              )
        """))

    print('Successfully processed contracts!')


# def clean_payroll():
#     pass
    

# def ingest_payroll(payroll_df, engine):
#     pass