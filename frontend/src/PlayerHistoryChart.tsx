import { useEffect, useRef } from 'react';
import * as Plot from '@observablehq/plot';
import type { HistoryPoint } from './types';
import { deltaToColor } from './colorScale';
import { figure_width } from './constants';

interface PlayerHistoryChartProps {
    name: string;
    points: HistoryPoint[];
}

export default function PlayerHistoryChart({ name, points }: PlayerHistoryChartProps) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!containerRef.current || points.length === 0) return;

        const data = points.map((p) => ({
            ...p,
            date: new Date(p.snapshot_date),
        }));

        const chart = Plot.plot({
            style: {
                background: 'transparent',
                color: '#222222',
                fontFamily: '-apple-system, sans-serif',
            },
            width: figure_width,
            height: 160,
            marginTop: 24,
            grid: true,
            x: { type: 'time' },
            y: { label: null },
            marks: [
                Plot.lineY(data, {
                    x: 'date',
                    y: 'predicted_bpm',
                    curve: 'step-after',
                    stroke: '#999',
                    strokeWidth: 1.5,
                }),
                Plot.dot(data, {
                    x: 'date',
                    y: 'predicted_bpm',
                    r: 2.5,
                    fill: (d) => deltaToColor(d.delta_from_trend ?? 0),
                    stroke: '#888888',
                    strokeWidth: 0.5,
                    channels: { 
                        'Game:': 'game_number',
                        'Date:': 'snapshot_date',
                    },
                    tip: { format: { x: false } },
                }),
                Plot.text([`${name} — pBPM by game`], {
                    frameAnchor: 'top-left',
                    dy: -18,
                    fontSize: 13,
                    fontWeight: 'bold',
                    fill: '#222222',
                }),
                Plot.axisX({ color: '#e7e7e7', fontSize: 12, fill: '#787878' }),
                Plot.axisY({ color: '#e7e7e7', fontSize: 12, fill: '#787878' }),
            ],
        });

        containerRef.current.appendChild(chart);

        return () => {
            chart.remove();
        };
    }, [name, points]);

    return <div ref={containerRef} />;
}
