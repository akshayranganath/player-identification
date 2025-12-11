import json
import requests
import os
from pathlib import Path
from datetime import datetime
from utils import get_player_details


def filter_high_confidence_players(result):
    """
    Filter players from get_player_details result that have at least two parameters with high confidence.

    Args:
        result (dict): Result from get_player_details containing players data

    Returns:
        list: List of dictionaries with player_name, player_team, and player_number
    """
    filtered_players = []

    # Handle error case
    if "error" in result:
        return filtered_players

    # Get players from result
    players = result.get("players", [])

    for player in players:
        high_confidence_count = 0
        player_info = {
            "player_name": None,
            "player_team": None,
            "player_number": None
        }

        # Check name confidence
        if "name" in player and player["name"].get("confidence") == "high":
            high_confidence_count += 1
            player_info["player_name"] = player["name"].get("value")

        # Check jersey number confidence
        if "jersey_number" in player and player["jersey_number"].get("confidence") == "high":
            high_confidence_count += 1
            player_info["player_number"] = player["jersey_number"].get("value")

        # Check team confidence
        if "team" in player and player["team"].get("confidence") == "high":
            high_confidence_count += 1
            player_info["player_team"] = player["team"].get("name")

        # Only include if at least 2 parameters have high confidence
        if high_confidence_count >= 2:
            # Fill in missing values with data from lower confidence or "Unknown"
            if player_info["player_name"] is None:
                player_info["player_name"] = player.get("name", {}).get("value", "Unknown")

            if player_info["player_number"] is None:
                player_info["player_number"] = player.get("jersey_number", {}).get("value", "Unknown")

            if player_info["player_team"] is None:
                player_info["player_team"] = player.get("team", {}).get("name", "Unknown")

            # Only append the three fields
            filtered_players.append({
                "player_name": player_info["player_name"],
                "player_team": player_info["player_team"],
                "player_number": player_info["player_number"]
            })

    return filtered_players


def verify_players_in_database(filtered_players, player_data):
    """
    Verify that filtered players exist in the player database.
    Fill in player name from database if it's Unknown.

    Args:
        filtered_players (list): List of player dicts from filter_high_confidence_players
        player_data (dict): Player database organized by team -> number -> player name(s)

    Returns:
        list: List of verified player dictionaries that exist in the database
    """
    verified_players = []

    for player in filtered_players:
        team = player.get("player_team")
        number = player.get("player_number")
        name = player.get("player_name")

        # Skip if essential fields are Unknown or None
        if not team or team == "Unknown" or not number or number == "Unknown":
            continue

        # Verify team and number exist in database
        if team in player_data and str(number) in player_data[team]:
            db_name = player_data[team][str(number)]

            # Handle case where multiple players have same number (list)
            if isinstance(db_name, list):
                db_name = db_name[0]  # Take first match

            # If name is Unknown, use database name
            if name == "Unknown" or not name:
                name = db_name

            verified_players.append({
                "player_name": name,
                "player_team": team,
                "player_number": str(number)
            })

    return verified_players


def download_image(url):
    """
    Download an image from a URL and store it in the current directory.

    Args:
        url (str): The URL of the image to download

    Returns:
        str: Path to the downloaded image file
    """
    try:
        # Download the image
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Get file extension from URL or default to .jpg
        url_path = Path(url)
        extension = url_path.suffix if url_path.suffix else '.jpg'

        # Create a temporary filename with timestamp in current directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"temp_image_{timestamp}{extension}"
        temp_filepath = os.path.join(os.getcwd(), temp_filename)

        # Write image to file
        with open(temp_filepath, 'wb') as f:
            f.write(response.content)

        print(f"Image downloaded successfully to: {temp_filepath}")
        return temp_filepath

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None


def load_player_data(json_path='cfl_players.json'):
    """
    Load CFL player data from JSON file.

    Args:
        json_path (str): Path to the JSON file

    Returns:
        dict: Player data organized by team -> number -> player name(s)
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded player data for {len(data)} teams")
        return data
    except FileNotFoundError:
        print(f"Error: {json_path} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}


def main():
    # Load player data
    player_data = load_player_data()

    if not player_data:
        print("Failed to load player data. Exiting.")
        return

    # Get URL from user input
    image_url = input("Enter image URL: ")

    # Download and save the image
    temp_image_path = download_image(image_url)

    if not temp_image_path:
        print("Failed to download image")
        return

    print(f"Temporary image path: {temp_image_path}")

    # Get player details from image
    result = get_player_details(temp_image_path)

    # Filter high confidence players
    filtered_players = filter_high_confidence_players(result)

    # Verify players exist in database
    verified_players = verify_players_in_database(filtered_players, player_data)

    # Output results as JSON
    print("\n" + "="*50)
    print("Identified Players:")
    print("="*50)
    print(json.dumps(verified_players, indent=2))
    


if __name__ == "__main__":
    main()
