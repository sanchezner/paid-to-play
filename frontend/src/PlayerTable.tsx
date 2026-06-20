import { useEffect, useMemo, useRef, useState } from 'react';
import type { PlayerRow, StatWindow, WindowStats } from './types';
import { deltaToColor } from './colorScale';
import './PlayerTable.css';

interface PlayerTableProps {
    players: PlayerRow[];
    selectedId: number | null;
    onSelectPlayer: (id: number | null) => void;
}

type TopLevelKey = 'name' | 'delta_from_trend' | 'predicted_bpm' | 'salary' | 'cap_pct';
type StatKey = keyof WindowStats;
type SortableKeys = TopLevelKey | StatKey;
type SortDirection = 'asc' | 'desc';

interface SortIntent {
    key: SortableKeys;
    direction: SortDirection;
}

const top_level_keys: ReadonlySet<string> = new Set<TopLevelKey>(['name', 'delta_from_trend', 'predicted_bpm', 'salary', 'cap_pct',]);

const window_labels: Record<StatWindow, string> = {
    season: 'Season',
    roll15: 'Last 15',
    roll40: 'Last 40',
};

function getSortValue(player: PlayerRow, key: SortableKeys, window: StatWindow): string | number | null {
    if (top_level_keys.has(key)) {
        return player[key as TopLevelKey];
    }
    return player.stats[window][key as StatKey];
}

const fmt1 = (v: number | null) => (v == null ? '—' : v.toFixed(1));
const fmtPct = (v: number | null) => (v == null ? '—' : `${(v * 100).toFixed(1)}%`);
const fmtSigned = (v: number | null) => (v == null ? '—' : `${v > 0 ? '+' : ''}${v.toFixed(1)}`);

export default function PlayerTable({ players, selectedId, onSelectPlayer }: PlayerTableProps) {
    const [sortIntent, setSortIntent] = useState<SortIntent>({
        key: 'predicted_bpm',
        direction: 'desc'
    });

    const [query, setQuery] = useState('');
    const [window, setWindow] = useState<StatWindow>('season');
    const tableContainerRef = useRef<HTMLDivElement>(null);

    const sortedFilteredPlayers = useMemo(() => {
        const filtered = players.filter(p =>
            p.name.toLowerCase().includes(query.toLowerCase())
        );

        return filtered.sort((a, b) => {
            const aValue = getSortValue(a, sortIntent.key, window);
            const bValue = getSortValue(b, sortIntent.key, window);

            if (aValue == null && bValue == null) return 0;
            if (aValue == null) return 1;
            if (bValue == null) return -1;
            if (aValue === bValue) return 0;

            if (sortIntent.direction === 'asc') {
                return aValue > bValue ? 1 : -1;
            } else {
                return aValue < bValue ? 1 : -1;
            }
        });
    }, [players, sortIntent, query, window]);

    useEffect(() => {
        if (selectedId == null) return;
        const container = tableContainerRef.current;
        if (!container) return;

        // Defer until after layout/paint so the scroll viewport is correct.
        const raf = requestAnimationFrame(() => {
            const row = container.querySelector<HTMLTableRowElement>(`tr[data-player-id="${selectedId}"]`);
            if (!row) return;
            row.scrollIntoView({ block: 'center' });
        });

        return () => cancelAnimationFrame(raf);
    }, [selectedId, window, query, sortIntent]);

    const handleSort = (key: SortableKeys) => {
        setSortIntent((prev) => {
            if (prev.key === key) {
                return {key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
            }
            return { key, direction: 'desc' };
        });
    };

    const renderSortArrow = (key: SortableKeys) => {
        if (sortIntent.key !== key) return null;
        return sortIntent.direction === 'asc' ? ' ▲' : ' ▼';
    };

    return (
        <div className='table-block'>
            <div className='window-toggle' role='group' aria-label='Stat window'>
                <span className='window-toggle-label'>Stats:</span>
                {(Object.keys(window_labels) as StatWindow[]).map((w) => (
                    <button
                        key={w}
                        className={`window-toggle-button${window === w ? ' is-active' : ''}`}
                        onClick={() => setWindow(w)}
                    >
                        {window_labels[w]}
                    </button>
                ))}
            </div>
            <div className='table-container' ref={tableContainerRef}>
                <table className='analytics-table'>
                    <thead>
                        <tr>
                            <th className='col-identity header-search-cell'>
                                <div className='header-search-wrapper'>
                                    <span className='clickable-header-lable' onClick={() => handleSort('name')}>
                                        Player{renderSortArrow('name')}
                                    </span>
                                    <input
                                        type='text'
                                        className='table-filter-input'
                                        placeholder='Search players...'
                                        value={query}
                                        onChange={(e) => setQuery(e.target.value)}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                </div>
                            </th>

                            <th className='col-value-block' onClick={() => handleSort('delta_from_trend')}>Value vs Trend{renderSortArrow('delta_from_trend')}</th>
                            <th className='col-value-block' onClick={() => handleSort('predicted_bpm')}>pBPM{renderSortArrow('predicted_bpm')}</th>
                            <th className='col-value-block' onClick={() => handleSort('salary')}>Salary{renderSortArrow('salary')}</th>
                            <th className='col-value-block' onClick={() => handleSort('cap_pct')}>CAP%{renderSortArrow('cap_pct')}</th>

                            <th className='col-production-block group-divider' onClick={() => handleSort('games')}>G{renderSortArrow('games')}</th>
                            <th className='col-production-block' onClick={() => handleSort('minutes_pg')}>MP{renderSortArrow('minutes_pg')}</th>
                            <th className='col-production-block' onClick={() => handleSort('pts_pg')}>PTS{renderSortArrow('pts_pg')}</th>
                            <th className='col-production-block' onClick={() => handleSort('reb_pg')}>REB{renderSortArrow('reb_pg')}</th>
                            <th className='col-production-block' onClick={() => handleSort('ast_pg')}>AST{renderSortArrow('ast_pg')}</th>
                            <th className='col-production-block' onClick={() => handleSort('stl_pg')}>STL{renderSortArrow('stl_pg')}</th>
                            <th className='col-production-block' onClick={() => handleSort('blk_pg')}>BLK{renderSortArrow('blk_pg')}</th>
                            <th className='col-production-block' onClick={() => handleSort('tov_pg')}>TOV{renderSortArrow('tov_pg')}</th>
                            <th className='col-production-block' onClick={() => handleSort('fg_pct')}>FG%{renderSortArrow('fg_pct')}</th>
                            <th className='col-production-block' onClick={() => handleSort('ts_pct')}>TS%{renderSortArrow('ts_pct')}</th>
                            <th className='col-production-block' onClick={() => handleSort('plus_minus_pg')}>+/-{renderSortArrow('plus_minus_pg')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedFilteredPlayers.map((player) => {
                            const isSelected = player.nba_id === selectedId;
                            const stats = player.stats[window];

                            return (
                                <tr
                                    key={player.nba_id}
                                    data-player-id={player.nba_id}
                                    className={isSelected ? 'is-selected' : ''}
                                    onClick={() => onSelectPlayer(isSelected ? null : player.nba_id)}
                                    style={{ cursor: 'pointer' }}
                                >
                                    <td className='col-identity'><strong>{player.name}</strong></td>

                                    <td className='col-value-block' style={{ backgroundColor: deltaToColor(player.delta_from_trend) }}>
                                        {player.delta_from_trend >= 0 ? '+' : ''}{(player.delta_from_trend * 100).toFixed(1)}%
                                    </td>
                                    <td className='col-value-block'>{player.predicted_bpm.toFixed(2)}</td>
                                    <td className='col-value-block'>${player.salary.toLocaleString()}</td>
                                    <td className='col-value-block'>{(player.cap_pct * 100).toFixed(1)}%</td>

                                    <td className='col-production-block group-divider'>{stats.games}</td>
                                    <td className='col-production-block'>{fmt1(stats.minutes_pg)}</td>
                                    <td className='col-production-block'>{fmt1(stats.pts_pg)}</td>
                                    <td className='col-production-block'>{fmt1(stats.reb_pg)}</td>
                                    <td className='col-production-block'>{fmt1(stats.ast_pg)}</td>
                                    <td className='col-production-block'>{fmt1(stats.stl_pg)}</td>
                                    <td className='col-production-block'>{fmt1(stats.blk_pg)}</td>
                                    <td className='col-production-block'>{fmt1(stats.tov_pg)}</td>
                                    <td className='col-production-block'>{fmtPct(stats.fg_pct)}</td>
                                    <td className='col-production-block'>{fmtPct(stats.ts_pct)}</td>
                                    <td className='col-production-block'>{fmtSigned(stats.plus_minus_pg)}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
