from __future__ import annotations

import time
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from bronze.gamelogs import get_nba_seasons, get_upcoming_nba_season
from config.domain import training_start_season


cache_dir = Path("data/manual/espn_cache")
output_path = Path("data/manual/historical_salaries_raw.csv")
user_agent = "Mozilla/5.0 (paid-to-play research scraper)"
request_delay = 1.5
request_timeout = 15
max_pages = 20


def get_target_end_years(end_season=None):
    end_season = end_season or get_upcoming_nba_season()
    seasons = get_nba_seasons(training_start_season, end_season)
    return [int(season.split("-")[0]) + 1 for season in seasons]


def fetch_page_html(end_year, page):
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{end_year}_page_{page}.html"

    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    url = (
        f"https://www.espn.com/nba/salaries/_/year/{end_year}"
        f"/page/{page}/seasontype/3"
    )
    response = requests.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=request_timeout,
    )
    response.raise_for_status()
    cache_path.write_text(response.text, encoding="utf-8")
    time.sleep(request_delay)
    return response.text


def parse_salary_page(html, end_year):
    tables = pd.read_html(StringIO(html))
    if not tables:
        return pd.DataFrame()

    df = tables[0]
    df.columns = ["rank", "name_position", "team", "salary"]
    df = df[df["rank"] != "RK"].copy()
    if df.empty:
        return df

    name_position = df["name_position"].str.rsplit(",", n=1, expand=True)
    df["player_name"] = name_position[0].str.strip()
    df["position"] = name_position[1].str.strip()

    df["salary"] = (
        df["salary"]
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(int)
    )
    df["rank"] = df["rank"].astype(int)
    df["season_end_year"] = end_year

    return df[["season_end_year", "rank", "player_name", "position", "team", "salary"]]


def assert_dedupe(df):
    df.drop_duplicates(subset=["player_name", "season_end_year"], keep='first', inplace=True)
    return df


def scrape_all_seasons(end_season=None):
    all_pages: list[pd.DataFrame] = []

    for end_year in get_target_end_years(end_season):
        print(f"Scraping season ending {end_year}...")
        for page in range(1, max_pages + 1):
            html = fetch_page_html(end_year, page)
            page_df = parse_salary_page(html, end_year)
            if page_df.empty:
                print(f"  page {page}: empty, stopping.")
                break
            print(f"  page {page}: {len(page_df)} rows")
            all_pages.append(page_df)

    combined = pd.concat(all_pages, ignore_index=True)
    return assert_dedupe(combined)


def main():
    df = scrape_all_seasons()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df)} rows to {output_path}")


if __name__ == "__main__":
    main()
