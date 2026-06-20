import { scaleDiverging } from 'd3-scale';
import { interpolateRdBu } from 'd3-scale-chromatic';
import { rgb } from 'd3-color';

const max_delta = 0.15;
const d3Scale = scaleDiverging(interpolateRdBu).domain([-max_delta, 0, max_delta]);

export function deltaToColor(delta: number): string {
    const clampedDelta = Math.min(Math.max(delta, -max_delta), max_delta);

    const rawColor = d3Scale(clampedDelta);

    const c = rgb(rawColor);
    const mixFactor = 0.5;

    const r = Math.round(c.r + (255 - c.r) * mixFactor);
    const g = Math.round(c.g + (255 - c.g) * mixFactor);
    const b = Math.round(c.b + (255 - c.b) * mixFactor);

    return `rgb(${r}, ${g}, ${b})`;
}