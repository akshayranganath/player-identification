#!/usr/bin/env python3
"""
Fetch CFL player data from https://www.cfl.ca/
Extracts: Player Name, Team, and Jersey Number
Saves to CSV file

Uses the CFL internal API endpoint for reliable data retrieval.
"""

import csv
import requests


# Team abbreviation to full name mapping
TEAM_ABBREV = {
    "BC": "BC Lions",
    "CGY": "Calgary Stampeders",
    "EDM": "Edmonton Elks",
    "HAM": "Hamilton Tiger-Cats",
    "MTL": "Montreal Alouettes",
    "OTT": "Ottawa Redblacks",
    "SSK": "Saskatchewan Roughriders",
    "TOR": "Toronto Argonauts",
    "WPG": "Winnipeg Blue Bombers",
}


def fetch_players_from_api() -> list[dict]:
    """
    Fetch player data directly from CFL's internal API.
    
    API returns a list of lists with structure:
    [jersey_number, name, team_abbrev, position, nationality, height, weight, age, college, url]
    
    Returns:
        List of dicts with keys: name, team, jersey_number
    """
    url = "https://www.cfl.ca/wp-content/themes/cfl.ca/inc/admin-ajax.php?action=get_all_players"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.cfl.ca/players/",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    print(f"Fetching from: {url}")
    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    
    data = response.json()
    
    # Extract nested data if present
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    
    if not isinstance(data, list):
        print(f"Unexpected data type: {type(data)}")
        return []
    
    print(f"Received {len(data)} player records")
    
    players = []
    for record in data:
        if not isinstance(record, list) or len(record) < 3:
            continue
        
        # Structure: [jersey, name, team_abbrev, position, ...]
        jersey_number = str(record[0]) if record[0] is not None else ""
        name = str(record[1]).strip() if record[1] else ""
        team_abbrev = str(record[2]).strip() if record[2] else ""
        
        # Convert team abbreviation to full name
        team = TEAM_ABBREV.get(team_abbrev, team_abbrev)
        
        if name:
            players.append({
                "name": name,
                "team": team,
                "jersey_number": jersey_number,
            })
    
    return players


def save_to_csv(players: list[dict], filename: str = "data/cfl_players.csv") -> None:
    """Save player data to CSV file."""
    if not players:
        print("No players to save!")
        return
    
    # Ensure data directory exists
    import os
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "team", "jersey_number"])
        writer.writeheader()
        writer.writerows(players)
    
    print(f"Saved {len(players)} players to {filename}")


def main():
    print("Fetching CFL player data from API...")
    print("=" * 50)
    
    players = fetch_players_from_api()
    
    if players:
        print(f"\nTotal: {len(players)} players")
        
        # Stats
        players_with_team = [p for p in players if p["team"]]
        print(f"Players with team info: {len(players_with_team)}")
        
        # Show team distribution
        teams = {}
        for p in players:
            t = p["team"] or "(No Team)"
            teams[t] = teams.get(t, 0) + 1
        
        print("\nPlayers by team:")
        for team, count in sorted(teams.items()):
            print(f"  {team}: {count}")
        
        # Preview
        print("\nPreview (first 10 players with teams):")
        count = 0
        for p in players:
            if p["team"] and count < 10:
                jersey_str = f"#{p['jersey_number']}" if p["jersey_number"] else "(no #)"
                print(f"  {jersey_str} {p['name']} - {p['team']}")
                count += 1
        
        save_to_csv(players)
    else:
        print("\nNo players found from API.")


if __name__ == "__main__":
    main()
