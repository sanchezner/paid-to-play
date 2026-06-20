export type StatWindow = 'season' | 'roll15' | 'roll40';

// Percentage stats can be null over a window (e.g. zero free-throw attempts
// in the last 15 games), so every stat is nullable and formatters must guard.
export interface WindowStats {
    games: number;
    minutes_pg: number | null;
    pts_pg: number | null;
    reb_pg: number | null;
    ast_pg: number | null;
    stl_pg: number | null;
    blk_pg: number | null;
    tov_pg: number | null;
    fg_pct: number | null;
    ts_pct: number | null;
    plus_minus_pg: number | null;
}

export interface PlayerRow {
    nba_id: number;
    bref_id: string;
    name: string;
    season: string;
    games_played: number;
    snapshot_date: string;
    predicted_bpm: number;
    salary: number;
    cap_pct: number;
    trend_cap_pct: number;
    delta_from_trend: number;
    stats: Record<StatWindow, WindowStats>;
}

export interface CurvePointRow {
    bpm: number;
    trend_cap_pct: number;
}

export interface HistoryPoint {
    game_number: number;
    snapshot_date: string;
    predicted_bpm: number;
    delta_from_trend: number | null;
}

export interface PlayersPayload {
    model_name: string;
    season: string;
    generated_at: string;
    players: PlayerRow[];
}

export interface CurvePayload {
    model_name: string;
    generated_at: string;
    points: CurvePointRow[];
}

export interface HistoryPayload {
    model_name: string;
    season: string;
    generated_at: string;
    series: Record<string, HistoryPoint[]>;
}
