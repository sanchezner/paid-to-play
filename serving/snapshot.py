import os
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv
from pathlib import Path
from modeling.predict import load_models, predict_trend_cap_pct
from silver.storage import get_engine

display_stats = (
    'minutes_pg',
    'pts_pg',
    'reb_pg',
    'ast_pg',
    'stl_pg',
    'blk_pg',
    'tov_pg',
    'fg_pct',
    'ts_pct',
    'plus_minus_pg',
)

stat_windows = {
    'season': '',
    'roll15': 'roll15_',
    'roll40': 'roll40_',
}


def to_json_number(value):
    return None if pd.isna(value) else float(value)


def build_window_stats(row):
    stats = {}
    for window, prefix in stat_windows.items():
        games_column = f'{prefix}games' if prefix else 'games_seen'
        stats[window] = {
            'games': int(row[games_column]),
            **{stat: to_json_number(row[f'{prefix}{stat}']) for stat in display_stats},
        }
    return stats


def build_player_snapshot(engine, season, min_games=20):
    window_columns = []
    for prefix in stat_windows.values():
        window_columns.append(f'f.{prefix}games' if prefix else 'f.games_seen')
        window_columns.extend(f'f.{prefix}{stat}' for stat in display_stats)

    sql = text(f"""
        WITH latest AS (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY nba_id ORDER BY game_number DESC
            ) AS rk
            FROM predictions
            WHERE season = :season
        )
        SELECT
            l.nba_id,
            l.bref_id,
            l.season,
            l.game_number,
            l.snapshot_date,
            l.predicted_bpm,
            l.trend_cap_pct,
            l.salary,
            l.cap_pct,
            l.delta_from_trend,
            p.first_name || ' ' || p.last_name AS name,
            {', '.join(window_columns)}
        FROM latest l
        JOIN inference_features f
            ON f.nba_id = l.nba_id
           AND f.season = l.season
           AND f.game_number = l.game_number
        JOIN players p
            ON p.nba_id = l.nba_id
        WHERE l.rk = 1
          AND l.game_number >= :min_games
          AND l.salary IS NOT NULL
        ORDER BY l.predicted_bpm DESC
    """)
    snapshot_df = pd.read_sql(sql, engine, params={'season': str(season), 'min_games': min_games})
    snapshot_df['snapshot_date'] = snapshot_df['snapshot_date'].astype(str)

    player_records = []
    for _, row in snapshot_df.iterrows():
        player_records.append({
            'nba_id': int(row['nba_id']),
            'bref_id': row['bref_id'],
            'name': row['name'],
            'season': row['season'],
            'games_played': int(row['game_number']),
            'snapshot_date': row['snapshot_date'],
            'predicted_bpm': row['predicted_bpm'],
            'salary': int(row['salary']),
            'cap_pct': row['cap_pct'],
            'trend_cap_pct': row['trend_cap_pct'],
            'delta_from_trend': row['delta_from_trend'],
            'stats': build_window_stats(row),
        })

    return player_records


def build_history(engine, season, player_ids):
    sql = text("""
        SELECT nba_id, game_number, snapshot_date, predicted_bpm, delta_from_trend
        FROM predictions
        WHERE season = :season
        ORDER BY nba_id, game_number
    """)
    history_df = pd.read_sql(sql, engine, params={'season': str(season)})
    history_df = history_df[history_df['nba_id'].isin(player_ids)]
    history_df['snapshot_date'] = history_df['snapshot_date'].astype(str)

    series = {}
    for nba_id, player_df in history_df.groupby('nba_id'):
        series[str(int(nba_id))] = player_df[
            ['game_number', 'snapshot_date', 'predicted_bpm', 'delta_from_trend']
        ].to_dict(orient='records')

    return series


def build_trend_curve(trend_model, bpm_min=-15.0, bpm_max=15.0, step=0.1):
    grid = np.arange(bpm_min, bpm_max + step, step).round(2)
    return pd.DataFrame({
        'bpm': grid,
        'trend_cap_pct': predict_trend_cap_pct(grid, trend_model),
    })


def refresh_snapshot(season, output_dir):
    load_dotenv()
    engine = get_engine()
    output_dir = Path(output_dir)
    _, trend_model = load_models(os.getenv('TRACKING_URI'))

    player_records = build_player_snapshot(engine, season)
    player_ids = {player['nba_id'] for player in player_records}
    history_series = build_history(engine, season, player_ids)
    curve_df = build_trend_curve(trend_model)

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()

    players_payload = {
        'model_name': 'bpm-projector',
        'season': season,
        'generated_at': generated_at,
        'players': player_records,
    }
    (output_dir / 'players.json').write_text(json.dumps(players_payload, indent=2))

    history_payload = {
        'model_name': 'bpm-projector',
        'season': season,
        'generated_at': generated_at,
        'series': history_series,
    }
    # Compact on purpose: ~26k points pretty-print to ~4.4MB vs ~2MB compact,
    # and nobody reads this file by eye.
    (output_dir / 'history.json').write_text(json.dumps(history_payload, separators=(',', ':')))

    curve_payload = {
        'model_name': 'bpm-to-cap-trend',
        'generated_at': generated_at,
        'points': curve_df.to_dict(orient='records'),
    }
    (output_dir / 'trend_curve.json').write_text(json.dumps(curve_payload, indent=2))

    print(f'Snapshot refreshed: {len(player_records)} players, {len(history_series)} history series')


if __name__ == '__main__':
    refresh_snapshot('2025-26', 'frontend/public/data')
