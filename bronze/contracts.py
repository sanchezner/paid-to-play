from datetime import date
from pathlib import Path
import re
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from bronze.gamelogs import get_current_nba_season
from bronze.storage import upload_json

bbref_base_url = "https://www.basketball-reference.com"
contracts_url = f"{bbref_base_url}/contracts/players.html"
payroll_url = f"{bbref_base_url}/contracts/"
bbref_href_pattern = re.compile(r"/players/(?P<bbref_id>[a-z]/[a-z0-9]+)\.html")
browser_headers = {"User-Agent": "Mozilla/5.0"}


def get_soup(url):
    request = Request(url, headers=browser_headers)

    with urlopen(request) as res:
        html = res.read().decode("utf-8")

    return BeautifulSoup(html, "html.parser")


def extract_bbref_id(player_href):
    if not player_href:
        return None

    match = bbref_href_pattern.search(player_href)
    if match:
        return match.group("bbref_id")

    return Path(player_href).stem


def parse_salary(value):
    if not value:
        return None

    normalized_value = value.replace("$", "").replace(",", "").strip()
    return int(normalized_value) if normalized_value.isdigit() else None


def get_contract_player_metadata(row):
    player_cell = row.find("td", {"data-stat": "player"})
    player_anchor = player_cell.find("a") if player_cell else row.find("a", href=bbref_href_pattern)
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


def parse_contract_row(row):
    player_metadata = get_contract_player_metadata(row)
    if not player_metadata["bbref_id"]:
        return None

    contract_record = player_metadata.copy()
    for cell in row.find_all(["th", "td"]):
        data_stat = cell.get("data-stat")
        if not data_stat or data_stat == "player":
            continue

        value = cell.get_text(strip=True)
        contract_record[data_stat] = parse_salary(value) if value.startswith("$") else value

    return contract_record


def get_contract_records():
    soup = get_soup(contracts_url)
    contract_table = soup.find("table", {"id": "contracts"}) or soup.find("table")
    table_body = contract_table.find("tbody") if contract_table else soup
    contract_records = []

    for row in table_body.find_all("tr"):
        if row.get("class") and "thead" in row.get("class"):
            continue

        contract_record = parse_contract_row(row)
        if contract_record:
            contract_records.append(contract_record)

    return contract_records


def get_payroll_records():
    soup = get_soup(payroll_url)
    headers = [th.get_text() for th in soup.find_all("tr")[1].find_all("th")]
    rows = soup.find_all("tr")[2:]
    rows_data = []

    for row in rows:
        if row.get("class") and "thead" in row.get("class"):
            continue

        rank = row.find("th", {"data-stat": "ranker"}).get_text()
        stats = [td.get_text() for td in row.find_all("td")]
        rows_data.append(dict(zip(headers, [rank] + stats)))

    return rows_data


def ingest_contracts(season=None):
    season = season or get_current_nba_season()
    key = f"bronze/contracts/season={season}/response.json"
    contract_records = get_contract_records()

    if not contract_records:
        raise ValueError("No contract records found on Basketball Reference")

    upload_json(contract_records, key)
    print(f"Successfully uploaded {len(contract_records)} contract records for {season}")
    return len(contract_records)


def ingest_payroll():
    current_year = date.today().year
    key = f"bronze/payroll/season={current_year}/response.json"

    try:
        upload_json(get_payroll_records(), key)
        print(f"Successfully uploaded {current_year} payroll data")
    except Exception as e:
        print(f"Error uploading object: {e}")