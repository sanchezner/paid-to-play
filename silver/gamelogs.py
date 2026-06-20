from silver.storage import pull_json, list_keys
from sqlalchemy import text
import pandas as pd


def parse_minutes_played(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0

    if isinstance(value, (int, float)):
        return int(value)

    raw = str(value).strip()
    if not raw:
        return 0

    if ':' in raw:
        minutes, seconds = raw.split(':', 1)
        return int(minutes) + round(int(seconds or 0) / 60)

    return int(float(raw))


gamelog_columns = [
    'game_id',
    'nba_id',
    'season',
    'game_date',
    'minutes_played',
    'fgm',
    'fga',
    'fg3m',
    'fg3a',
    'ftm',
    'fta',
    'oreb',
    'dreb',
    'reb',
    'ast',
    'tov',
    'stl',
    'blk',
    'pf',
    'pfd',
    'pts',
    'plus_minus',
]


def normalize_gamelog_df(gamelog_json, key):
    if not gamelog_json:
        print(f"[warn] Skipping empty gamelog object: {key}")
        return None

    gamelog_df = pd.DataFrame(gamelog_json)
    gamelog_df.columns = gamelog_df.columns.str.lower()
    gamelog_df.rename(
        columns={
            'player_id': 'nba_id',
            'season_year': 'season',
            'min': 'minutes_played',
        },
        inplace=True,
    )

    missing_columns = set(gamelog_columns) - set(gamelog_df.columns)
    if missing_columns:
        raise ValueError(f"{key} is missing gamelog columns: {sorted(missing_columns)}")

    gamelog_df = gamelog_df[gamelog_columns].copy()
    gamelog_df['minutes_played'] = gamelog_df['minutes_played'].map(parse_minutes_played)
    return gamelog_df


def process_gamelogs(engine, game_date=None):
    prefix = 'bronze/gamelogs/'
    if game_date is not None:
        prefix += f'game_date={game_date.isoformat()}/'

    keys = list_keys(prefix)
    if not keys:
        print("[warn] No gamelog records found")
        return

    for key in keys:
        gamelog_json = pull_json(key)
        gamelog_df = normalize_gamelog_df(gamelog_json, key)
        if gamelog_df is None:
            continue

        ingest_gamelog(gamelog_df, engine)

    print("Successfully processed game logs!")


def ingest_gamelog(gamelog_df, engine):
    gamelog_df.to_sql('gamelogs_staging', engine, if_exists='replace', index=False)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO gamelogs(game_id, nba_id, season, game_date, minutes_played, fgm, fga, fg3m, fg3a, ftm, fta, oreb, dreb, reb, ast, tov, stl, blk, pf, pfd, pts, plus_minus)
            SELECT
                s.game_id,
                s.nba_id::integer,
                s.season,
                s.game_date::date,
                s.minutes_played::integer,
                s.fgm::integer,
                s.fga::integer,
                s.fg3m::integer,
                s.fg3a::integer,
                s.ftm::integer,
                s.fta::integer,
                s.oreb::integer,
                s.dreb::integer,
                s.reb::integer,
                s.ast::integer,
                s.tov::integer,
                s.stl::integer,
                s.blk::integer,
                s.pf::integer,
                s.pfd::integer,
                s.pts::integer,
                s.plus_minus::integer
            FROM gamelogs_staging s
            WHERE EXISTS (SELECT 1 FROM ids i WHERE i.nba_id = s.nba_id)
            ON CONFLICT(game_id, nba_id) DO NOTHING
        """))