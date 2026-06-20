import { useEffect, useRef } from 'react';
import * as Plot from '@observablehq/plot';
import type { PlayerRow, CurvePointRow } from './types';
import { deltaToColor } from './colorScale';
import { core_highlights, figure_width } from './constants';

interface PlayerChartProps {
    players: PlayerRow[];
    curvePoints: CurvePointRow[];
    selectedId: number | null;
    height?: number;
}

export default function PlayerChart({ players, curvePoints, selectedId, height = 400 }: PlayerChartProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {
        if (!containerRef.current) return;

        const selectedPlayer = players.find(p => p.nba_id === selectedId);

        const chart = Plot.plot({
            style: { 
                background: 'transparent', 
                color: '#222222',
                fontFamily: '-apple-system, sans-serif'
            },
            width: figure_width,
            height,
            grid: true,
            // x: {},
            y: { tickFormat: '%' },
            marks: [
                Plot.dot(players, {
                    x: 'predicted_bpm',
                    y: 'cap_pct',
                    fill: (d) => deltaToColor(d.delta_from_trend),
                    fillOpacity: selectedId ? (d => d.nba_id === selectedId ? 1.0 : 0.15) : 0.85,
                    r: 4,
                    channels: {
                        'Name:': 'name'
                    },
                    tip: { format: { x: false, y: false } }
                }),

                Plot.dot(players.filter(p => core_highlights.has(p.nba_id)), {
                    x: 'predicted_bpm',
                    y: 'cap_pct',
                    stroke: '#222222',
                    strokeWidth: 1.5,
                    strokeOpacity: selectedId ? (d => d.nba_id === selectedId ? 1.0 : 0.15) : 1.0,
                    strokeDasharray: 1.5,
                    fill: 'none',
                    r: 6,
                }),

                Plot.line(curvePoints, {
                    x: 'bpm',
                    y: 'trend_cap_pct',
                    stroke: '#999',
                    strokeDasharray: '4,4',
                    strokeWidth: 2,
                    strokeOpacity: 0.6,
                }),

                Plot.text(players.filter(p => core_highlights.has(p.nba_id) && p.nba_id !== selectedId), {
                    x: 'predicted_bpm',
                    y: 'cap_pct',
                    text: 'name',
                    dy: -14,
                    fontSize: 13,
                    fill: '#555555',
                    stroke: 'white',
                    strokeWidth: 5,
                    fontWeight: 500,
                    opacity: selectedId ? (d => d.nba_id === selectedId ? 1.0 : 0.15) : 1.0,
                }),

                ...(selectedPlayer ? [
                    Plot.dot([selectedPlayer], {
                        x: 'predicted_bpm',
                        y: 'cap_pct',
                        stroke: '#000000',
                        strokeWidth: 2,
                        r: 6,
                        fill: 'none',
                    }),
                    Plot.text([selectedPlayer], {
                        x: 'predicted_bpm',
                        y: 'cap_pct',
                        text: 'name',
                        dy: -14,
                        fontSize: 13,
                        fontWeight: 'bold',
                        fill: '#000000',
                    })
                ] : []),

                Plot.axisX({ color: '#e7e7e7', fontSize: 13, fill: '#787878' }),

                Plot.axisY({ color: '#e7e7e7', fontSize: 13, fill: '#787878', tickFormat: '%' })
            ],
        });
        
        containerRef.current.appendChild(chart);

        return () => {
            chart.remove();
        }
    }, [players, curvePoints, selectedId, height]);

    return <div ref={containerRef} />;
}