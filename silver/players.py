from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from silver.storage import pull_json
from sqlalchemy import text
import json
import pandas as pd


browser_headers = {"User-Agent": "Mozilla/5.0"}
root = Path(__file__).parent.parent


def obtain_wiki_data(query):
    url = 'https://query.wikidata.org/sparql'
    params = urlencode({
        "query": query,
        "format": "json",
    }).encode("utf-8")

    request = Request(
        url,
        data=params,
        headers=browser_headers,
        method="POST",
    )
    
    with urlopen(request) as res:
        data = res.read().decode("utf-8")

        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            response_tail = data[-500:]
            raise ValueError(f"Wikidata returned malformed JSON. ")
    
    
def normalize_wikidata(data_json):
    rows = []

    for item in data_json['results']['bindings']:
        rows.append({
            "wikidata_id": item["item"]["value"].split("/")[-1],
            "name": item.get("itemLabel", {}).get("value"),
            "basketball_ref_id": item.get("basketballRefID", {}).get("value"),
            "nba_id": item.get("NBAID", {}).get("value")
        })

    return pd.DataFrame(rows)


def clean_ids(ids_df):
    ids_df = ids_df.dropna(subset=["basketball_ref_id", "nba_id"]).copy()
    ids_df["nba_id"] = pd.to_numeric(ids_df["nba_id"], errors="coerce")
    ids_df = ids_df.dropna(subset=["nba_id"])
    ids_df["nba_id"] = ids_df["nba_id"].astype("int64")

    ids_df = ids_df.rename(columns={"basketball_ref_id": "bref_id"})
    ids_df = ids_df[["nba_id", "bref_id"]]
    return ids_df.drop_duplicates(subset=["nba_id", "bref_id"])
    

def map_players():
    query = '''
    SELECT ?item ?itemLabel ?basketballRefID ?NBAID
    WHERE {
        ?item wdt:P2685 ?basketballRefID.
        OPTIONAL{?item wdt:P3647 ?NBAID.}

        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE], en". }
    }
    '''
    data_json = obtain_wiki_data(query)
    df = normalize_wikidata(data_json)
    ids_df = clean_ids(df)
    
    bref_lookup = dict(zip(ids_df["nba_id"].astype(str), ids_df["bref_id"]))
    nba_lookup = dict(zip(ids_df["bref_id"], ids_df["nba_id"].astype(str)))

    with open(root / 'data' / 'nba_to_bref.json', 'w') as f:
        json.dump(bref_lookup, f, indent=4)

    with open(root / 'data' / 'bref_to_nba.json', 'w') as f:
        json.dump(nba_lookup, f, indent=4)

    return ids_df


def load_ids():
    map_players()


def clean_players():
    ids_df = map_players()
    players_json = pull_json("bronze/players/response.json")
    df = pd.DataFrame(players_json)
    df.rename(columns={'id': 'nba_id'}, inplace=True)

    with open(root / 'data' / 'nba_to_bref.json', 'r') as f:
        bref_lookup = json.load(f)

    df['bref_id'] = df['nba_id'].astype(str).map(bref_lookup)
    df = df.dropna(subset=['bref_id'])

    players_df = df[['nba_id', 'first_name', 'last_name']]

    return ids_df, players_df


def ingest_ids(ids_df, engine):
    ids_df.to_sql('ids_staging', engine, if_exists='replace', index=False)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO ids(nba_id, bref_id)
            SELECT nba_id, bref_id FROM ids_staging
            ON CONFLICT(nba_id) DO NOTHING
        """))

    print('Successfully ingested IDs!')


def ingest_players(players_df, engine):
    players_df.to_sql('players_staging', engine, if_exists='replace', index=False)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO players(nba_id, first_name, last_name)
            SELECT nba_id, first_name, last_name FROM players_staging
            ON CONFLICT(nba_id) DO NOTHING
        """))

    print('Successfully ingested players!')

