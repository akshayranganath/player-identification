import json
import requests
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime
from utils import process_player_identification

# Configure logging (only if not already configured by parent app)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)


# CFL team name mapping (short name -> full database name)
TEAM_NAME_MAPPING = {
    # Full names (as-is)
    "BC Lions": "BC Lions",
    "Calgary Stampeders": "Calgary Stampeders",
    "Edmonton Elks": "Edmonton Elks",
    "Hamilton Tiger-Cats": "Hamilton Tiger-Cats",
    "Montreal Alouettes": "Montreal Alouettes",
    "Ottawa Redblacks": "Ottawa Redblacks",
    "Saskatchewan Roughriders": "Saskatchewan Roughriders",
    "Toronto Argonauts": "Toronto Argonauts",
    "Winnipeg Blue Bombers": "Winnipeg Blue Bombers",
    
    # Short names / Aliases
    "Lions": "BC Lions",
    "Stampeders": "Calgary Stampeders",
    "Elks": "Edmonton Elks",
    "Tiger-Cats": "Hamilton Tiger-Cats",
    "Alouettes": "Montreal Alouettes",
    "Redblacks": "Ottawa Redblacks",
    "Roughriders": "Saskatchewan Roughriders",
    "Argonauts": "Toronto Argonauts",
    "Blue Bombers": "Winnipeg Blue Bombers",
    
    # Alternative names
    "Calgary": "Calgary Stampeders",
    "Edmonton": "Edmonton Elks",
    "Hamilton": "Hamilton Tiger-Cats",
    "Montreal": "Montreal Alouettes",
    "Ottawa": "Ottawa Redblacks",
    "Saskatchewan": "Saskatchewan Roughriders",
    "Toronto": "Toronto Argonauts",
    "Winnipeg": "Winnipeg Blue Bombers",
}


def normalize_team_name(team_name: str) -> str:
    """
    Normalize team name to match database format.
    
    Args:
        team_name: Team name from vision model (may be short form)
        
    Returns:
        Full team name as it appears in database, or original if no match
    """
    if not team_name or team_name == "Unknown":
        return team_name
    
    # Try exact match first
    if team_name in TEAM_NAME_MAPPING:
        normalized = TEAM_NAME_MAPPING[team_name]
        if normalized != team_name:
            logger.debug(f"Normalized team name: '{team_name}' -> '{normalized}'")
        return normalized
    
    # Try case-insensitive match
    for key, value in TEAM_NAME_MAPPING.items():
        if key.lower() == team_name.lower():
            logger.debug(f"Normalized team name (case-insensitive): '{team_name}' -> '{value}'")
            return value
    
    # No match found, return original
    logger.warning(f"Unknown team name: '{team_name}' - not found in mapping")
    return team_name


def filter_high_confidence_players(result):
    """
    Filter players from process_player_identification result that have at least two parameters with high confidence.

    Args:
        result (dict): Result from process_player_identification containing players data

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
        logger.debug("*"*100)
        logger.debug(f"Processing player: {player}")
        logger.debug("*"*100)
        high_confidence_count = 0
        player_info = {
            "player_name": None,
            "player_team": None,
            "player_number": None
        }

        # Check player_name confidence (from Agent 2 web search)
        if "player_name" in player and player["player_name"].get("confidence") == "high":
            high_confidence_count += 1
            player_info["player_name"] = player["player_name"].get("value")

        # Check jersey number confidence (from Agent 1)
        if "jersey_number" in player and player["jersey_number"].get("confidence") == "high":
            high_confidence_count += 1
            player_info["player_number"] = player["jersey_number"].get("value")

        # Check team confidence (from Agent 1)
        if "team" in player and player["team"].get("confidence") == "high":
            high_confidence_count += 1
            raw_team_name = player["team"].get("name")
            player_info["player_team"] = normalize_team_name(raw_team_name)

        # Only include if at least 2 parameters have high confidence
        if high_confidence_count >= 2:
            # Fill in missing values with data from lower confidence or "Unknown"
            if player_info["player_name"] is None:
                player_info["player_name"] = player.get("player_name", {}).get("value", "Unknown")

            if player_info["player_number"] is None:
                player_info["player_number"] = player.get("jersey_number", {}).get("value", "Unknown")

            if player_info["player_team"] is None:
                raw_team_name = player.get("team", {}).get("name", "Unknown")
                player_info["player_team"] = normalize_team_name(raw_team_name)

            # Only append the three fields
            filtered_player = {
                "player_name": player_info["player_name"],
                "player_team": player_info["player_team"],
                "player_number": player_info["player_number"]
            }
            filtered_players.append(filtered_player)
            logger.info(f"Filtered player (high_confidence_count={high_confidence_count}): {filtered_player}")
        else:
            logger.debug(f"Player skipped: only {high_confidence_count} high-confidence fields (need 2+)")

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

        logger.debug(f"Verifying player: team={team}, number={number}, name={name}")

        # Skip if essential fields are Unknown or None
        if not team or team == "Unknown" or not number or number == "Unknown":
            logger.debug(f"Skipped - missing essential fields: team={team}, number={number}")
            continue

        # Verify team and number exist in database
        if team in player_data and str(number) in player_data[team]:
            db_name = player_data[team][str(number)]

            # Handle case where multiple players have same number (list)
            if isinstance(db_name, list):
                db_name = db_name[0]  # Take first match

            # If name is Unknown, use database name
            if name == "Unknown" or not name:
                logger.info(f"Updated player name from database: '{name}' -> '{db_name}'")
                name = db_name

            verified_player = {
                "player_name": name,
                "player_team": team,
                "player_number": str(number)
            }
            verified_players.append(verified_player)
            logger.info(f"Verified player in database: {verified_player}")
        else:
            if team not in player_data:
                logger.warning(f"Team '{team}' not found in database")
            elif str(number) not in player_data[team]:
                logger.warning(f"Jersey number '{number}' not found for team '{team}' in database")

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

        logger.info(f"Image downloaded successfully to: {temp_filepath}")
        return temp_filepath

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image: {e}")
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
        logger.info(f"Loaded player data for {len(data)} teams")
        return data
    except FileNotFoundError:
        logger.error(f"Error: {json_path} not found")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return {}


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='CFL Player Identification CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Normal mode (INFO level)
  python main.py --verbose          # Verbose mode (DEBUG level)
  uv run main.py -v                 # Verbose mode (shorthand)
        """
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    args = parser.parse_args()

    # Configure logging based on verbose flag
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    
    if args.verbose:
        logger.info("Verbose logging enabled (DEBUG level)")
    
    # Load player data
    player_data = load_player_data()

    if not player_data:
        logger.error("Failed to load player data. Exiting.")
        return

    # Get URL from user input
    image_url = input("Enter image URL: ")

    # Download and save the image
    temp_image_path = download_image(image_url)

    if not temp_image_path:
        logger.error("Failed to download image")
        return

    logger.info(f"Temporary image path: {temp_image_path}")

    # Get player details from image (Agent 1 + Agent 2)
    result, telemetry = process_player_identification(temp_image_path)

    # Filter high confidence players
    filtered_players = filter_high_confidence_players(result)

    # Verify players exist in database
    verified_players = verify_players_in_database(filtered_players, player_data)

    # Output results as JSON
    logger.info("\n" + "="*50)
    logger.info("Identified Players:")
    logger.info("="*50)
    logger.info(json.dumps(verified_players, indent=2))
    
    # Output telemetry information
    logger.info("\n" + "="*50)
    logger.info("Token Usage (Telemetry):")
    logger.info("="*50)
    logger.info(f"Agent 1: Input tokens: {telemetry['agent_1']['input_tokens']}, Output tokens: {telemetry['agent_1']['output_tokens']}")
    logger.info(f"Agent 2: Input tokens: {telemetry['agent_2']['input_tokens']}, Output tokens: {telemetry['agent_2']['output_tokens']}")
    logger.info(f"Total: Input tokens: {telemetry['total']['input_tokens']}, Output tokens: {telemetry['total']['output_tokens']}")
    


if __name__ == "__main__":
    main()
