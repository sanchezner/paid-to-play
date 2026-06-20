from nba_api.stats.static import players, teams
from bronze.storage import upload_json


def ingest_players():
    key = "bronze/players/response.json"

    try:
        upload_json(players.get_players(), key)
        print("Successfully uploaded all players")
    except Exception as e:
        print(f"Error uploading object: {e}")


def ingest_teams():
    key = "bronze/teams/response.json"

    try:
        upload_json(teams.get_teams(), key)
        print("Successfully uploaded teams")
    except Exception as e:
        print(f"Error uploading object: {e}")