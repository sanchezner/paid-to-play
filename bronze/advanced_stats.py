from bs4 import BeautifulSoup, Comment

from bronze.contracts import (
    bbref_base_url,
    extract_bbref_id,
    get_soup,
)
from bronze.gamelogs import get_current_nba_season, get_nba_seasons
from bronze.storage import upload_json
from config.domain import training_start_season


advanced_stats_url_template = (
    "https://www.basketball-reference.com/leagues/NBA_{season_end_year}_advanced.html"
)
advanced_stats_str = {"player", "pos", "team_id", "awards"}


def get_basketball_reference_season_end_year(season):
    start_year = int(season.split("-")[0])
    return start_year + 1


def get_advanced_stats_url(season):
    season_end_year = get_basketball_reference_season_end_year(season)
    return advanced_stats_url_template.format(season_end_year=season_end_year)


def find_advanced_stats_table(soup):
    advanced_stats_table = soup.find("table", {"id": "advanced"})
    if advanced_stats_table:
        return advanced_stats_table

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment_soup = BeautifulSoup(comment, "html.parser")
        advanced_stats_table = comment_soup.find("table", {"id": "advanced"})
        if advanced_stats_table:
            return advanced_stats_table

    return None


def parse_advanced_stat_value(data_stat, value):
    if data_stat in advanced_stats_str:
        return value

    if value == "":
        return None

    normalized_value = value.replace(",", "").strip()

    try:
        if "." in normalized_value:
            return float(normalized_value)

        return int(normalized_value)
    except ValueError:
        return value


def get_advanced_stats_player_metadata(row):
    player_cell = row.find(["th", "td"], {"data-stat": "player"})
    player_anchor = player_cell.find("a") if player_cell else row.find("a", href=True)
    player_href = player_anchor.get("href") if player_anchor else None
    bbref_id = extract_bbref_id(player_href)
    player_name = player_anchor.get_text(strip=True) if player_anchor else ""

    if not player_name and player_cell:
        player_name = player_cell.get_text(strip=True)

    return {
        "bbref_id": bbref_id,
        "bbref_name": player_name,
        "bbref_url": f"{bbref_base_url}{player_href}" if player_href else None,
    }


def parse_advanced_stats_row(row, season):
    player_metadata = get_advanced_stats_player_metadata(row)
    if not player_metadata["bbref_id"]:
        return None

    advanced_stats_record = {"season": season, **player_metadata}
    for cell in row.find_all(["th", "td"]):
        data_stat = cell.get("data-stat")
        if not data_stat or data_stat in {"ranker", "player"}:
            continue

        value = cell.get_text(strip=True)
        advanced_stats_record[data_stat] = parse_advanced_stat_value(data_stat, value)

    return advanced_stats_record


def get_advanced_stats_records(season=None):
    season = season or get_current_nba_season()
    advanced_stats_url = get_advanced_stats_url(season)
    soup = get_soup(advanced_stats_url)
    advanced_stats_table = find_advanced_stats_table(soup)
    if not advanced_stats_table:
        raise ValueError(f"Advanced stats table not found for {season}: {advanced_stats_url}")

    table_body = advanced_stats_table.find("tbody") or advanced_stats_table
    advanced_stats_records = []

    for row in table_body.find_all("tr"):
        if row.get("class") and "thead" in row.get("class"):
            continue

        advanced_stats_record = parse_advanced_stats_row(row, season)
        if advanced_stats_record:
            advanced_stats_records.append(advanced_stats_record)

    if not advanced_stats_records:
        raise ValueError(f"No advanced stats records parsed for {season}: {advanced_stats_url}")

    return advanced_stats_records


def ingest_advanced_stats(start_season=training_start_season, end_season=None):
    for season in get_nba_seasons(start_season, end_season):
        key = f"bronze/advanced_stats/season={season}/response.json"

        try:
            upload_json(get_advanced_stats_records(season), key)
            print(f"Successfully uploaded {season} advanced stats")
        except Exception as e:
            print(f"Error uploading {season} advanced stats: {e}")