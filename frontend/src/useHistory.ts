import { useState, useEffect } from "react";
import type { HistoryPayload } from "./types";

export function useHistory() {
    const [history, setHistory] = useState<HistoryPayload | null>(null);

    useEffect(() => {
        let isMounted = true;

        fetch(`${import.meta.env.BASE_URL}data/history.json`)
            .then((res) => {
                if (!res.ok) throw new Error('Failed to load history.json');
                return res.json() as Promise<HistoryPayload>;
            })
            .then((data) => {
                if (isMounted) setHistory(data);
            })
            .catch(() => {
                if (isMounted) setHistory(null);
            });

        return () => {
            isMounted = false;
        };
    }, []);

    return history;
}
