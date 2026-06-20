from __future__ import annotations
from pathlib import Path
import unicodedata
import pandas as pd
from rapidfuzz import process, fuzz
from silver.storage import get_engine

raw_path = Path("data/manual/historical_salaries_raw.csv")
overrides_path = Path("data/manual/salary_name_overrides.csv")
matched_path = Path("data/manual/historical_salaries_matched.csv")
unmatched_path = Path("data/manual/historical_salaries_unmatched.csv")

fuzzy_accept = 92
fuzzy_flag = 80

suffixes = ("iv", "iii", "ii", "jr", "sr")


def normalize_name(full_name):
    decomposed = unicodedata.normalize("NFKD", full_name.lower())
    name = "".join(c for c in decomposed if not unicodedata.combining(c) and c != ".")

    tokens = name.split()
    if tokens and tokens[-1].rstrip(".") in suffixes:
        tokens = tokens[:-1]

    return " ".join(tokens)


def load_player_lookup(engine):
    players_df = pd.read_sql(
        """
        SELECT p.first_name, p.last_name, i.bref_id
        FROM players p
        JOIN ids i USING (nba_id)
        WHERE i.bref_id IS NOT NULL
        """,
        engine,
    )

    lookup: dict[str, list[str]] = {}
    for _, row in players_df.iterrows():
        key = normalize_name(f"{row['first_name']} {row['last_name']}")
        lookup.setdefault(key, []).append(row["bref_id"])

    return lookup


def load_overrides():
    if not overrides_path.exists():
        return {}
    df = pd.read_csv(overrides_path)
    return dict(zip(df["espn_name"], df["bref_id"]))


def match_rows(raw_df, player_lookup, overrides):
    matched_rows = []
    unmatched_rows = []

    fuzzy_keys = list(player_lookup.keys())

    for _, row in raw_df.iterrows():
        espn_name = row["player_name"]

        if espn_name in overrides:
            matched_rows.append(_matched(row, overrides[espn_name], "manual_override", 1.00))
            continue

        norm_key = normalize_name(espn_name)
        exact_hits = player_lookup.get(norm_key, [])

        if len(exact_hits) == 1:
            matched_rows.append(_matched(row, exact_hits[0], "exact_normalized", 0.99))
            continue

        if len(exact_hits) > 1:
            unmatched_rows.append(_unmatched(row, reason=f"ambiguous_exact:{','.join(exact_hits)}"))
            continue

        best = process.extractOne(norm_key, fuzzy_keys, scorer=fuzz.WRatio)
        if best is None:
            unmatched_rows.append(_unmatched(row, reason="no_candidates"))
            continue

        match_str, score, idx = best
        candidate_bref_ids = player_lookup[fuzzy_keys[idx]]

        if score >= fuzzy_accept and len(candidate_bref_ids) == 1:
            matched_rows.append(_matched(row, candidate_bref_ids[0], f"fuzzy_{int(score)}", score / 100))
        else:
            unmatched_rows.append(_unmatched(row, reason=f"fuzzy_low:{int(score)}->{match_str}"))

    return pd.DataFrame(matched_rows), pd.DataFrame(unmatched_rows)


def _matched(row, bref_id, method, confidence):
    return {
        "bref_id": bref_id,
        "season": _season_label(row["season_end_year"]),
        "salary": row["salary"],
        "espn_name": row["player_name"],
        "match_method": method,
        "match_confidence": round(confidence, 3),
    }


def _unmatched(row, reason):
    return {
        "espn_name": row["player_name"],
        "season": _season_label(row["season_end_year"]),
        "salary": row["salary"],
        "team": row["team"],
        "position": row["position"],
        "reason": reason,
    }


def _season_label(season_end_year):
    """2020 -> '2019-20'. Matches the season format used in advanced_stats."""
    start = season_end_year - 1
    return f"{start}-{str(season_end_year)[-2:]}"


def main():
    if not raw_path.exists():
        raise FileNotFoundError(f"Run the scraper first: {raw_path} not found.")

    raw_df = pd.read_csv(raw_path)
    engine = get_engine()
    player_lookup = load_player_lookup(engine)
    overrides = load_overrides()

    matched_df, unmatched_df = match_rows(raw_df, player_lookup, overrides)

    matched_df.to_csv(matched_path, index=False)
    unmatched_df.to_csv(unmatched_path, index=False)

    total = len(raw_df)
    matched = len(matched_df)
    print(f"Matched   : {matched}/{total} ({matched/total:.1%})")
    print(f"Unmatched : {len(unmatched_df)}/{total}")
    if matched:
        print("\nMatch method breakdown:")
        print(matched_df["match_method"].str.replace(r"_\d+$", "_X", regex=True).value_counts())


if __name__ == "__main__":
    main()
