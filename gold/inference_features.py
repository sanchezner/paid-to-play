from sqlalchemy import text

windows = (
    ("", None),
    ("roll15_", 15),
    ("roll40_", 40),
)

avg_stats = (
    ("minutes_pg", "minutes_played"),
    ("pts_pg", "pts"),
    ("reb_pg", "reb"),
    ("ast_pg", "ast"),
    ("stl_pg", "stl"),
    ("blk_pg", "blk"),
    ("tov_pg", "tov"),
    ("plus_minus_pg", "plus_minus"),
)

per_36_stats = (
    ("pts_per_36", "pts"),
    ("reb_per_36", "reb"),
    ("ast_per_36", "ast"),
    ("stl_per_36", "stl"),
    ("blk_per_36", "blk"),
    ("tov_per_36", "tov"),
    ("plus_minus_per_36", "plus_minus"),
)

pct_stats = (
    ("fg_pct", "fgm", "fga"),
    ("fg3_pct", "fg3m", "fg3a"),
    ("ft_pct", "ftm", "fta"),
)

prior_stats = (
    "prior_games_played",
    "prior_ws",
    "prior_ws_per_48",
    "prior_vorp",
    "prior_bpm",
)


def _window_exprs(prefix, window):
    flt = f' FILTER (WHERE g.game_number > s.game_number - {window})' if window else ''

    def agg_sum(col):
        return f'SUM(g.{col}){flt}'

    minutes_sum = f'NULLIF({agg_sum('minutes_played')}, 0)'
    
    games_name = f'{prefix}games' if prefix else 'games_seen'

    exprs = [(games_name, f"(COUNT(*){flt})::integer")]

    for name, col in avg_stats:
        exprs.append((f'{prefix}{name}', f'(AVG(g.{col}){flt})::double precision'))

    for name, col in per_36_stats:
        exprs.append((
            f'{prefix}{name}',
            f'(({agg_sum(col)})::double precision / {minutes_sum} * 36)',
        ))

    for name, made, attempted in pct_stats:
        exprs.append((
            f'{prefix}{name}',
            f'(({agg_sum(made)})::double precision / NULLIF({agg_sum(attempted)}, 0))',
        ))

    exprs.append((
        f'{prefix}ts_pct',
        f'(({agg_sum('pts')})::double precision'
        f' / NULLIF(2 * (({agg_sum('fga')}) + 0.44 * ({agg_sum('fta')})), 0))',
    ))

    return exprs


def _stat_exprs():
    exprs = []
    for prefix, window in windows:
        exprs.extend(_window_exprs(prefix, window))
    return exprs


def _column_type(name):
    if name in ('games_seen', 'prior_games_played') or name.endswith('_games') or name.endswith('games'):
        return 'INTEGER'
    return 'DOUBLE PRECISION'


def create_inference_features_table(engine):
    stat_columns = ',\n '.join(
        f'{name} {_column_type(name)}' for name, _ in _stat_exprs()
    )
    prior_columns = ',\n '.join(
        f'{name} {_column_type(name)}' for name in prior_stats
    )

    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS inference_features (
                nba_id INTEGER NOT NULL REFERENCES ids(nba_id),
                bref_id VARCHAR NOT NULL REFERENCES ids(bref_id),
                season VARCHAR NOT NULL,
                game_number INTEGER NOT NULL,
                snapshot_date DATE NOT NULL,
                {stat_columns},
                {prior_columns},
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (nba_id, season, game_number)
            )
        """))


def build_inference_features(engine, season):
    create_inference_features_table(engine)

    stat_exprs = _stat_exprs()
    stat_names = [name for name, _ in stat_exprs]
    insert_columns = ['nba_id', 'bref_id', 'season', 'game_number', 'snapshot_date'] + stat_names + list(prior_stats)

    stat_select = ',\n '.join(
        f'{expr} AS {name}' for name, expr in stat_exprs
    )
    feature_select = ',\n '.join(f'f.{name}' for name in stat_names)

    with engine.begin() as conn:
        result = conn.execute(text(f"""
            INSERT INTO inference_features (
                {', '.join(insert_columns)}
            )
            WITH ranked_gamelogs AS (
                SELECT
                    g.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY g.nba_id, g.season
                        ORDER BY g.game_date, g.game_id
                    ) AS game_number
                FROM gamelogs g
                WHERE g.season = :season
            ),
            snapshot_games AS (
                SELECT
                    r.nba_id,
                    r.season,
                    r.game_number,
                    r.game_date AS snapshot_date
                FROM ranked_gamelogs r
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM inference_features f
                    WHERE f.nba_id = r.nba_id
                      AND f.season = r.season
                      AND f.game_number = r.game_number
                )
            ),
            features AS (
                SELECT
                    s.nba_id,
                    i.bref_id,
                    s.season,
                    s.game_number,
                    s.snapshot_date,
                    {stat_select}
                FROM snapshot_games s
                JOIN ranked_gamelogs g
                    ON g.nba_id = s.nba_id
                   AND g.season = s.season
                   AND g.game_number <= s.game_number
                JOIN ids i
                    ON i.nba_id = s.nba_id
                GROUP BY
                    s.nba_id,
                    i.bref_id,
                    s.season,
                    s.game_number,
                    s.snapshot_date
            )
            SELECT
                f.nba_id,
                f.bref_id,
                f.season,
                f.game_number,
                f.snapshot_date,
                {feature_select},
                pa.games_played::integer AS prior_games_played,
                pa.ws::double precision AS prior_ws,
                pa.ws_per_48::double precision AS prior_ws_per_48,
                pa.vorp::double precision AS prior_vorp,
                pa.bpm::double precision AS prior_bpm
            FROM features f
            LEFT JOIN advanced_stats pa
                ON pa.bref_id = f.bref_id
               AND pa.season = (
                   (split_part(f.season, '-', 1)::integer - 1)::text
                   || '-'
                   || right(split_part(f.season, '-', 1), 2)
               )
            ON CONFLICT (nba_id, season, game_number) DO NOTHING
        """), {'season': str(season)})

    print(f'Inference features: inserted {result.rowcount} new rows for {season}')
    return result.rowcount


def validate_inference_features(engine, season):
    validation_queries = {
        'missing_gamelog_coverage': """
            SELECT COUNT(*)
            FROM (
                SELECT
                    g.nba_id,
                    g.season,
                    ROW_NUMBER() OVER (
                        PARTITION BY g.nba_id, g.season
                        ORDER BY g.game_date, g.game_id
                    ) AS game_number
                FROM gamelogs g
                WHERE g.season = :season
            ) ranked
            WHERE NOT EXISTS (
                SELECT 1
                FROM inference_features f
                WHERE f.nba_id = ranked.nba_id
                  AND f.season = ranked.season
                  AND f.game_number = ranked.game_number
            )
        """,
        'games_seen_mismatch': """
            SELECT COUNT(*)
            FROM inference_features
            WHERE season = :season
              AND games_seen <> game_number
        """,
        'incorrect_roll15_games': """
            SELECT COUNT(*)
            FROM inference_features
            WHERE season = :season
              AND roll15_games <> LEAST(games_seen, 15)
        """,
        'incorrect_roll40_games': """
            SELECT COUNT(*)
            FROM inference_features
            WHERE season = :season
              AND roll40_games <> LEAST(games_seen, 40)
        """,
        # Snapshot date must be the date of the snapshot game (no leakage
        # from later games into the snapshot point).
        'incorrect_snapshot_dates': """
            WITH ranked_gamelogs AS (
                SELECT
                    g.nba_id,
                    g.season,
                    g.game_date,
                    ROW_NUMBER() OVER (
                        PARTITION BY g.nba_id, g.season
                        ORDER BY g.game_date, g.game_id
                    ) AS game_number
                FROM gamelogs g
                WHERE g.season = :season
            )
            SELECT COUNT(*)
            FROM inference_features f
            JOIN ranked_gamelogs g
                ON g.nba_id = f.nba_id
               AND g.season = f.season
               AND g.game_number = f.game_number
            WHERE f.season = :season
              AND g.game_date <> f.snapshot_date
        """,
    }

    with engine.begin() as conn:
        results = {
            name: conn.execute(text(query), {'season': str(season)}).scalar()
            for name, query in validation_queries.items()
        }

    failures = {name: count for name, count in results.items() if count}
    if failures:
        raise ValueError(f'Inference feature validation failed: {failures}')

    print(f'Inference feature validation passed: {results}')
    return results
