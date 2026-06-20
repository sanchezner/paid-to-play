from sqlalchemy import text
import pandas as pd


milestones = (5, 10, 15, 25, 40, 60, 75)
milestone_sql = ", ".join(str(milestone) for milestone in milestones)

# feature_column_sql = """
#     ADD COLUMN IF NOT EXISTS pts_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS reb_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS ast_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS stl_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS blk_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS tov_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS plus_minus_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS ts_pct DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_games INTEGER,
#     ADD COLUMN IF NOT EXISTS roll15_minutes_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_pts_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_reb_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_ast_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_stl_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_blk_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_tov_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_pts_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_reb_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_ast_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_stl_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_blk_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_tov_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_fg_pct DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_fg3_pct DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_ft_pct DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_ts_pct DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_plus_minus_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll15_plus_minus_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_games INTEGER,
#     ADD COLUMN IF NOT EXISTS roll40_minutes_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_pts_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_reb_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_ast_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_stl_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_blk_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_tov_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_pts_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_reb_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_ast_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_stl_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_blk_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_tov_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_fg_pct DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_fg3_pct DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_ft_pct DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_ts_pct DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_plus_minus_pg DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS roll40_plus_minus_per_36 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS prior_games_played INTEGER,
#     ADD COLUMN IF NOT EXISTS prior_ws DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS prior_ws_per_48 DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS prior_vorp DOUBLE PRECISION,
#     ADD COLUMN IF NOT EXISTS prior_bpm DOUBLE PRECISION
# """


def create_feature_snapshots_table(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS feature_snapshots (
                nba_id INTEGER NOT NULL REFERENCES ids(nba_id),
                bref_id VARCHAR NOT NULL REFERENCES ids(bref_id),
                season VARCHAR NOT NULL,
                milestone_n INTEGER NOT NULL,
                snapshot_date DATE NOT NULL,
                games_seen INTEGER NOT NULL,
                minutes_pg DOUBLE PRECISION,
                pts_pg DOUBLE PRECISION,
                reb_pg DOUBLE PRECISION,
                ast_pg DOUBLE PRECISION,
                stl_pg DOUBLE PRECISION,
                blk_pg DOUBLE PRECISION,
                tov_pg DOUBLE PRECISION,
                pts_per_36 DOUBLE PRECISION,
                reb_per_36 DOUBLE PRECISION,
                ast_per_36 DOUBLE PRECISION,
                stl_per_36 DOUBLE PRECISION,
                blk_per_36 DOUBLE PRECISION,
                tov_per_36 DOUBLE PRECISION,
                fg_pct DOUBLE PRECISION,
                fg3_pct DOUBLE PRECISION,
                ft_pct DOUBLE PRECISION,
                ts_pct DOUBLE PRECISION,
                plus_minus_pg DOUBLE PRECISION,
                plus_minus_per_36 DOUBLE PRECISION,
                roll15_games INTEGER,
                roll15_minutes_pg DOUBLE PRECISION,
                roll15_pts_pg DOUBLE PRECISION,
                roll15_reb_pg DOUBLE PRECISION,
                roll15_ast_pg DOUBLE PRECISION,
                roll15_stl_pg DOUBLE PRECISION,
                roll15_blk_pg DOUBLE PRECISION,
                roll15_tov_pg DOUBLE PRECISION,
                roll15_pts_per_36 DOUBLE PRECISION,
                roll15_reb_per_36 DOUBLE PRECISION,
                roll15_ast_per_36 DOUBLE PRECISION,
                roll15_stl_per_36 DOUBLE PRECISION,
                roll15_blk_per_36 DOUBLE PRECISION,
                roll15_tov_per_36 DOUBLE PRECISION,
                roll15_fg_pct DOUBLE PRECISION,
                roll15_fg3_pct DOUBLE PRECISION,
                roll15_ft_pct DOUBLE PRECISION,
                roll15_ts_pct DOUBLE PRECISION,
                roll15_plus_minus_pg DOUBLE PRECISION,
                roll15_plus_minus_per_36 DOUBLE PRECISION,
                roll40_games INTEGER,
                roll40_minutes_pg DOUBLE PRECISION,
                roll40_pts_pg DOUBLE PRECISION,
                roll40_reb_pg DOUBLE PRECISION,
                roll40_ast_pg DOUBLE PRECISION,
                roll40_stl_pg DOUBLE PRECISION,
                roll40_blk_pg DOUBLE PRECISION,
                roll40_tov_pg DOUBLE PRECISION,
                roll40_pts_per_36 DOUBLE PRECISION,
                roll40_reb_per_36 DOUBLE PRECISION,
                roll40_ast_per_36 DOUBLE PRECISION,
                roll40_stl_per_36 DOUBLE PRECISION,
                roll40_blk_per_36 DOUBLE PRECISION,
                roll40_tov_per_36 DOUBLE PRECISION,
                roll40_fg_pct DOUBLE PRECISION,
                roll40_fg3_pct DOUBLE PRECISION,
                roll40_ft_pct DOUBLE PRECISION,
                roll40_ts_pct DOUBLE PRECISION,
                roll40_plus_minus_pg DOUBLE PRECISION,
                roll40_plus_minus_per_36 DOUBLE PRECISION,
                prior_games_played INTEGER,
                prior_ws DOUBLE PRECISION,
                prior_ws_per_48 DOUBLE PRECISION,
                prior_vorp DOUBLE PRECISION,
                prior_bpm DOUBLE PRECISION,
                label_games_played INTEGER NOT NULL,
                label_bpm DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (nba_id, season, milestone_n)
            )
        """))
        # conn.execute(text(f"ALTER TABLE feature_snapshots {feature_column_sql}"))


def build_feature_snapshots(engine):
    create_feature_snapshots_table(engine)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE feature_snapshots"))
        conn.execute(text(f"""
            INSERT INTO feature_snapshots (
                nba_id,
                bref_id,
                season,
                milestone_n,
                snapshot_date,
                games_seen,
                minutes_pg,
                pts_pg,
                reb_pg,
                ast_pg,
                stl_pg,
                blk_pg,
                tov_pg,
                pts_per_36,
                reb_per_36,
                ast_per_36,
                stl_per_36,
                blk_per_36,
                tov_per_36,
                fg_pct,
                fg3_pct,
                ft_pct,
                ts_pct,
                plus_minus_pg,
                plus_minus_per_36,
                roll15_games,
                roll15_minutes_pg,
                roll15_pts_pg,
                roll15_reb_pg,
                roll15_ast_pg,
                roll15_stl_pg,
                roll15_blk_pg,
                roll15_tov_pg,
                roll15_pts_per_36,
                roll15_reb_per_36,
                roll15_ast_per_36,
                roll15_stl_per_36,
                roll15_blk_per_36,
                roll15_tov_per_36,
                roll15_fg_pct,
                roll15_fg3_pct,
                roll15_ft_pct,
                roll15_ts_pct,
                roll15_plus_minus_pg,
                roll15_plus_minus_per_36,
                roll40_games,
                roll40_minutes_pg,
                roll40_pts_pg,
                roll40_reb_pg,
                roll40_ast_pg,
                roll40_stl_pg,
                roll40_blk_pg,
                roll40_tov_pg,
                roll40_pts_per_36,
                roll40_reb_per_36,
                roll40_ast_per_36,
                roll40_stl_per_36,
                roll40_blk_per_36,
                roll40_tov_per_36,
                roll40_fg_pct,
                roll40_fg3_pct,
                roll40_ft_pct,
                roll40_ts_pct,
                roll40_plus_minus_pg,
                roll40_plus_minus_per_36,
                prior_games_played,
                prior_ws,
                prior_ws_per_48,
                prior_vorp,
                prior_bpm,
                label_games_played,
                label_bpm
            )
            WITH ranked_gamelogs AS (
                SELECT
                    g.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY g.nba_id, g.season
                        ORDER BY g.game_date, g.game_id
                    ) AS game_number
                FROM gamelogs g
            ),
            snapshot_games AS (
                SELECT
                    nba_id,
                    season,
                    game_number AS milestone_n,
                    game_date AS snapshot_date
                FROM ranked_gamelogs
                WHERE game_number IN ({milestone_sql})
            ),
            season_to_date_features AS (
                SELECT
                    s.nba_id,
                    i.bref_id,
                    s.season,
                    s.milestone_n,
                    s.snapshot_date,
                    COUNT(*)::integer AS games_seen,
                    AVG(g.minutes_played)::double precision AS minutes_pg,
                    AVG(g.pts)::double precision AS pts_pg,
                    AVG(g.reb)::double precision AS reb_pg,
                    AVG(g.ast)::double precision AS ast_pg,
                    AVG(g.stl)::double precision AS stl_pg,
                    AVG(g.blk)::double precision AS blk_pg,
                    AVG(g.tov)::double precision AS tov_pg,
                    (SUM(g.pts)::double precision / NULLIF(SUM(g.minutes_played), 0) * 36) AS pts_per_36,
                    (SUM(g.reb)::double precision / NULLIF(SUM(g.minutes_played), 0) * 36) AS reb_per_36,
                    (SUM(g.ast)::double precision / NULLIF(SUM(g.minutes_played), 0) * 36) AS ast_per_36,
                    (SUM(g.stl)::double precision / NULLIF(SUM(g.minutes_played), 0) * 36) AS stl_per_36,
                    (SUM(g.blk)::double precision / NULLIF(SUM(g.minutes_played), 0) * 36) AS blk_per_36,
                    (SUM(g.tov)::double precision / NULLIF(SUM(g.minutes_played), 0) * 36) AS tov_per_36,
                    (SUM(g.fgm)::double precision / NULLIF(SUM(g.fga), 0)) AS fg_pct,
                    (SUM(g.fg3m)::double precision / NULLIF(SUM(g.fg3a), 0)) AS fg3_pct,
                    (SUM(g.ftm)::double precision / NULLIF(SUM(g.fta), 0)) AS ft_pct,
                    (SUM(g.pts)::double precision / NULLIF(2 * (SUM(g.fga) + 0.44 * SUM(g.fta)), 0)) AS ts_pct,
                    AVG(g.plus_minus)::double precision AS plus_minus_pg,
                    (SUM(g.plus_minus)::double precision / NULLIF(SUM(g.minutes_played), 0) * 36) AS plus_minus_per_36,
                    COUNT(*) FILTER (WHERE g.game_number > s.milestone_n - 15)::integer AS roll15_games,
                    AVG(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 15)::double precision AS roll15_minutes_pg,
                    AVG(g.pts) FILTER (WHERE g.game_number > s.milestone_n - 15)::double precision AS roll15_pts_pg,
                    AVG(g.reb) FILTER (WHERE g.game_number > s.milestone_n - 15)::double precision AS roll15_reb_pg,
                    AVG(g.ast) FILTER (WHERE g.game_number > s.milestone_n - 15)::double precision AS roll15_ast_pg,
                    AVG(g.stl) FILTER (WHERE g.game_number > s.milestone_n - 15)::double precision AS roll15_stl_pg,
                    AVG(g.blk) FILTER (WHERE g.game_number > s.milestone_n - 15)::double precision AS roll15_blk_pg,
                    AVG(g.tov) FILTER (WHERE g.game_number > s.milestone_n - 15)::double precision AS roll15_tov_pg,
                    ((SUM(g.pts) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 15), 0) * 36) AS roll15_pts_per_36,
                    ((SUM(g.reb) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 15), 0) * 36) AS roll15_reb_per_36,
                    ((SUM(g.ast) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 15), 0) * 36) AS roll15_ast_per_36,
                    ((SUM(g.stl) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 15), 0) * 36) AS roll15_stl_per_36,
                    ((SUM(g.blk) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 15), 0) * 36) AS roll15_blk_per_36,
                    ((SUM(g.tov) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 15), 0) * 36) AS roll15_tov_per_36,
                    ((SUM(g.fgm) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.fga) FILTER (WHERE g.game_number > s.milestone_n - 15), 0)) AS roll15_fg_pct,
                    ((SUM(g.fg3m) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.fg3a) FILTER (WHERE g.game_number > s.milestone_n - 15), 0)) AS roll15_fg3_pct,
                    ((SUM(g.ftm) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.fta) FILTER (WHERE g.game_number > s.milestone_n - 15), 0)) AS roll15_ft_pct,
                    ((SUM(g.pts) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(2 * ((SUM(g.fga) FILTER (WHERE g.game_number > s.milestone_n - 15)) + 0.44 * (SUM(g.fta) FILTER (WHERE g.game_number > s.milestone_n - 15))), 0)) AS roll15_ts_pct,
                    AVG(g.plus_minus) FILTER (WHERE g.game_number > s.milestone_n - 15)::double precision AS roll15_plus_minus_pg,
                    ((SUM(g.plus_minus) FILTER (WHERE g.game_number > s.milestone_n - 15))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 15), 0) * 36) AS roll15_plus_minus_per_36,
                    COUNT(*) FILTER (WHERE g.game_number > s.milestone_n - 40)::integer AS roll40_games,
                    AVG(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 40)::double precision AS roll40_minutes_pg,
                    AVG(g.pts) FILTER (WHERE g.game_number > s.milestone_n - 40)::double precision AS roll40_pts_pg,
                    AVG(g.reb) FILTER (WHERE g.game_number > s.milestone_n - 40)::double precision AS roll40_reb_pg,
                    AVG(g.ast) FILTER (WHERE g.game_number > s.milestone_n - 40)::double precision AS roll40_ast_pg,
                    AVG(g.stl) FILTER (WHERE g.game_number > s.milestone_n - 40)::double precision AS roll40_stl_pg,
                    AVG(g.blk) FILTER (WHERE g.game_number > s.milestone_n - 40)::double precision AS roll40_blk_pg,
                    AVG(g.tov) FILTER (WHERE g.game_number > s.milestone_n - 40)::double precision AS roll40_tov_pg,
                    ((SUM(g.pts) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 40), 0) * 36) AS roll40_pts_per_36,
                    ((SUM(g.reb) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 40), 0) * 36) AS roll40_reb_per_36,
                    ((SUM(g.ast) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 40), 0) * 36) AS roll40_ast_per_36,
                    ((SUM(g.stl) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 40), 0) * 36) AS roll40_stl_per_36,
                    ((SUM(g.blk) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 40), 0) * 36) AS roll40_blk_per_36,
                    ((SUM(g.tov) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 40), 0) * 36) AS roll40_tov_per_36,
                    ((SUM(g.fgm) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.fga) FILTER (WHERE g.game_number > s.milestone_n - 40), 0)) AS roll40_fg_pct,
                    ((SUM(g.fg3m) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.fg3a) FILTER (WHERE g.game_number > s.milestone_n - 40), 0)) AS roll40_fg3_pct,
                    ((SUM(g.ftm) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.fta) FILTER (WHERE g.game_number > s.milestone_n - 40), 0)) AS roll40_ft_pct,
                    ((SUM(g.pts) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(2 * ((SUM(g.fga) FILTER (WHERE g.game_number > s.milestone_n - 40)) + 0.44 * (SUM(g.fta) FILTER (WHERE g.game_number > s.milestone_n - 40))), 0)) AS roll40_ts_pct,
                    AVG(g.plus_minus) FILTER (WHERE g.game_number > s.milestone_n - 40)::double precision AS roll40_plus_minus_pg,
                    ((SUM(g.plus_minus) FILTER (WHERE g.game_number > s.milestone_n - 40))::double precision / NULLIF(SUM(g.minutes_played) FILTER (WHERE g.game_number > s.milestone_n - 40), 0) * 36) AS roll40_plus_minus_per_36
                FROM snapshot_games s
                JOIN ranked_gamelogs g
                    ON g.nba_id = s.nba_id
                   AND g.season = s.season
                   AND g.game_number <= s.milestone_n
                JOIN ids i
                    ON i.nba_id = s.nba_id
                GROUP BY
                    s.nba_id,
                    i.bref_id,
                    s.season,
                    s.milestone_n,
                    s.snapshot_date
            )
            SELECT
                f.nba_id,
                f.bref_id,
                f.season,
                f.milestone_n,
                f.snapshot_date,
                f.games_seen,
                f.minutes_pg,
                f.pts_pg,
                f.reb_pg,
                f.ast_pg,
                f.stl_pg,
                f.blk_pg,
                f.tov_pg,
                f.pts_per_36,
                f.reb_per_36,
                f.ast_per_36,
                f.stl_per_36,
                f.blk_per_36,
                f.tov_per_36,
                f.fg_pct,
                f.fg3_pct,
                f.ft_pct,
                f.ts_pct,
                f.plus_minus_pg,
                f.plus_minus_per_36,
                f.roll15_games,
                f.roll15_minutes_pg,
                f.roll15_pts_pg,
                f.roll15_reb_pg,
                f.roll15_ast_pg,
                f.roll15_stl_pg,
                f.roll15_blk_pg,
                f.roll15_tov_pg,
                f.roll15_pts_per_36,
                f.roll15_reb_per_36,
                f.roll15_ast_per_36,
                f.roll15_stl_per_36,
                f.roll15_blk_per_36,
                f.roll15_tov_per_36,
                f.roll15_fg_pct,
                f.roll15_fg3_pct,
                f.roll15_ft_pct,
                f.roll15_ts_pct,
                f.roll15_plus_minus_pg,
                f.roll15_plus_minus_per_36,
                f.roll40_games,
                f.roll40_minutes_pg,
                f.roll40_pts_pg,
                f.roll40_reb_pg,
                f.roll40_ast_pg,
                f.roll40_stl_pg,
                f.roll40_blk_pg,
                f.roll40_tov_pg,
                f.roll40_pts_per_36,
                f.roll40_reb_per_36,
                f.roll40_ast_per_36,
                f.roll40_stl_per_36,
                f.roll40_blk_per_36,
                f.roll40_tov_per_36,
                f.roll40_fg_pct,
                f.roll40_fg3_pct,
                f.roll40_ft_pct,
                f.roll40_ts_pct,
                f.roll40_plus_minus_pg,
                f.roll40_plus_minus_per_36,
                pa.games_played::integer AS prior_games_played,
                pa.ws::double precision AS prior_ws,
                pa.ws_per_48::double precision AS prior_ws_per_48,
                pa.vorp::double precision AS prior_vorp,
                pa.bpm::double precision AS prior_bpm,
                a.games_played::integer AS label_games_played,
                a.bpm::double precision AS label_bpm
            FROM season_to_date_features f
            JOIN advanced_stats a
                ON a.bref_id = f.bref_id
               AND a.season = f.season
            LEFT JOIN advanced_stats pa
                ON pa.bref_id = f.bref_id
               AND pa.season = (
                   (split_part(f.season, '-', 1)::integer - 1)::text
                   || '-'
                   || right(split_part(f.season, '-', 1), 2)
               )
            WHERE a.games_played >= 20
              AND a.bpm IS NOT NULL
              AND f.milestone_n <= a.games_played
        """))

    print("Successfully built feature snapshots!")


def validate_feature_snapshots(engine):
    validation_queries = {
        "duplicate_keys": """
            SELECT COUNT(*)
            FROM (
                SELECT nba_id, season, milestone_n
                FROM feature_snapshots
                GROUP BY nba_id, season, milestone_n
                HAVING COUNT(*) > 1
            ) duplicates
        """,
        "milestones_over_label_games": """
            SELECT COUNT(*)
            FROM feature_snapshots
            WHERE milestone_n > label_games_played
        """,
        "incorrect_snapshot_dates": f"""
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
            )
            SELECT COUNT(*)
            FROM feature_snapshots f
            JOIN ranked_gamelogs g
                ON g.nba_id = f.nba_id
               AND g.season = f.season
               AND g.game_number = f.milestone_n
            WHERE g.game_date <> f.snapshot_date
              AND f.milestone_n IN ({milestone_sql})
        """,
        "low_quality_labels": """
            SELECT COUNT(*)
            FROM feature_snapshots
            WHERE label_games_played < 20
        """,
        "incorrect_roll15_games": """
            SELECT COUNT(*)
            FROM feature_snapshots
            WHERE roll15_games <> LEAST(games_seen, 15)
        """,
        "incorrect_roll40_games": """
            SELECT COUNT(*)
            FROM feature_snapshots
            WHERE roll40_games <> LEAST(games_seen, 40)
        """,
        "null_labels": """
            SELECT COUNT(*)
            FROM feature_snapshots
            WHERE label_bpm IS NULL
        """,
    }

    with engine.begin() as conn:
        results = {
            name: conn.execute(text(query)).scalar()
            for name, query in validation_queries.items()
        }

    failures = {name: count for name, count in results.items() if count}
    if failures:
        raise ValueError(f"Feature snapshot validation failed: {failures}")

    print(f"Feature snapshot validation passed: {results}")
    return results


def get_latest_inference_snapshot(engine, season):
    sql = text(f"""
    WITH ranked AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY nba_id, season ORDER BY milestone_n DESC
        ) AS rk
        FROM feature_snapshots
        WHERE season = :season
    )
    SELECT * FROM ranked WHERE rk = 1
    """)
    return pd.read_sql(sql, engine, params={'season': str(season)})