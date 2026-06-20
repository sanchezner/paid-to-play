import { useState, useEffect } from "react";
import type { PlayersPayload, CurvePayload } from "./types";

type LoadState = | { status: 'loading' } | { status: 'error'; message: string; } | { status: 'ready'; players: PlayersPayload; curve: CurvePayload };

export function useSnapshot() {
    const [state, setState] = useState<LoadState>({ status: 'loading' })
    useEffect(() => {
        let isMounted = true;

        Promise.all([
            fetch(`${import.meta.env.BASE_URL}data/players.json`).then((res) => {
                if (!res.ok) throw new Error('Failed to load players.json');
                return res.json() as Promise<PlayersPayload>;
            }),
            fetch(`${import.meta.env.BASE_URL}data/trend_curve.json`).then((res) => {
                if (!res.ok) throw new Error('Failed to load trend_curve.json');
                return res.json() as Promise<CurvePayload>;
            })
        ])
            .then(([playersData, curveData]) => {
                if (isMounted) {
                    setState({ status: 'ready', players: playersData, curve: curveData });
                }
            })
            .catch((err) => {
                if (isMounted) {
                    setState({ status: 'error', message: err instanceof Error ? err.message : 'An unknown error occurred' });
                }
            });

        return () => {
            isMounted = false;
        }
    }, []);

    return state;
}