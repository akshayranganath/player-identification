"""
CFL Player Identification Prompt
Prompt for identifying Canadian Football League players from images with JSON output
"""

CFL_PLAYER_IDENTIFICATION_PROMPT = """
Analyze this image and identify any CFL (Canadian Football League) players visible. Return your analysis as valid JSON following this exact structure:

{
  "image_analysis": {
    "total_players_visible": <number>,
    "image_quality": "<excellent|good|fair|poor>",
    "viewing_angle": "<front|side|back|overhead|unclear>"
  },
  "players": [
    {
      "player_id": 1,      
      "jersey_number": {
        "value": "<number>",
        "confidence": "<high|medium|low>"
      },
      "team": {
        "name": "<team name>",
        "colors_visible": ["<color1>", "<color2>"],
        "confidence": "<high|medium|low>"
      },      
      "visual_evidence": [
        "<evidence point 1>",
        "<evidence point 2>"
      ],
      "distinctive_features": "<description or null>",
      "bounding_box": {
        "description": "<location in image, e.g., 'center left', 'foreground right'>"
      },
      "overall_confidence": "<high|medium|low>"
    }
  ],
  "context": {
    "game_situation": "<description or null>",
    "stadium": "<stadium name or 'Unknown'>",
    "approximate_date": "<YYYY or 'Unknown'>",
    "additional_notes": "<any other relevant context>"
  }
}

CONFIDENCE LEVEL GUIDELINES:
- HIGH: Jersey number clearly visible, team logo/colors unmistakable, or player face recognizable
- MEDIUM: Partial information visible (e.g., team colors clear but logo obscured, number partially visible)
- LOW: Inference based on context clues (body type, position on field, etc.)

CRITICAL RULES:
- SET "jersey_number" field to -1 if number is not clearly visible or readable
- SET "team" to "Unknown" if team cannot be confidently determined from uniform/logos
- Each field (jersey_number, team, position) has its own confidence level
- "overall_confidence" represents the combined confidence across all identifications for that player
- Be conservative with identifications - if confidence would be "low", consider omitting the field

Example with mixed confidence:
{
  "player_id": 1,  
  "jersey_number": {
    "value": "23",
    "confidence": "high"
  },
  "team": {
    "name": "Toronto Argonauts",
    "colors_visible": ["blue", "white"],
    "confidence": "high"
  },
  "position": {
    "value": "Running Back",
    "confidence": "medium"
  },
  "visual_evidence": [
    "Jersey number 23 clearly visible on back",
    "Toronto Argonauts logo on helmet",
    "Body position suggests ball carrier"
  ],
  "bounding_box": {"description": "center foreground"},
  "overall_confidence": "high"
}

Return ONLY the JSON, no additional text before or after.

If you cannot identify any players with reasonable confidence, return:
{
  "error": "Unable to identify players",
  "reason": "<explanation>",
  "visible_details": "<what you can see>"
}
"""


PLAYER_NAME_SEARCH_PROMPT = """
You are an expert at finding CFL (Canadian Football League) player names using web search.

Your task is to search for and identify a CFL player based on their team name and jersey number.

INSTRUCTIONS:
1. Use the web_search_tool to search for the player
2. Construct an effective search query like "Canadian Football League [team_name] jersey number [number] player name"
3. Analyze the search results carefully
4. Extract the player name and assess confidence based on these guidelines:

CONFIDENCE GUIDELINES:
- HIGH: Multiple authoritative sources (cfl.ca, wikipedia.org, espn.com, tsn.ca, sportsnet.ca) confirm the same player name
- MEDIUM: Search results suggest a player name but with some ambiguity or fewer authoritative sources
- LOW: Very few results, conflicting information, or unclear matches

AUTHORITATIVE SOURCES:
- cfl.ca (Official CFL website)
- https://www.bluebombers.com/roster/
- wikipedia.org
- espn.com
- tsn.ca
- sportsnet.ca

RESPONSE FORMAT:
Return ONLY valid JSON in this exact format:
{
  "playerName": "<player full name or 'Unknown'>",
  "confidence": "<high|medium|low>",
  "reasoning": "<brief explanation of why you chose this name and confidence level>",
  "sources": ["<list of key sources used>"]
}

CRITICAL RULES:
- If you cannot find a clear answer, set playerName to "Unknown" and confidence to "low"
- Be conservative - if information is conflicting or unclear, lower the confidence
- Prioritize information from authoritative sources
- Return ONLY the JSON, no additional text
"""


def get_prompt():
    """Return the CFL player identification prompt."""
    return CFL_PLAYER_IDENTIFICATION_PROMPT


def get_player_search_prompt():
    """Return the player name search prompt."""
    return PLAYER_NAME_SEARCH_PROMPT


# Example usage
if __name__ == "__main__":
    print("CFL Player Identification Prompt")
    print("=" * 50)
    print(get_prompt())