# JSON Structure Documentation

This document describes the consistent JSON structures used throughout the CFL Player Identification application.

## Data Flow Overview

```
Image → Agent 1 (Vision) → Agent 2 (Web Search) → Filter → Verify → Display
```

---

## 1. Agent 1 Output (Vision Analysis)

**File:** `utils.py` → `agent_1_extract_team_and_jersey()`

```json
{
  "image_analysis": {
    "total_players_visible": 2,
    "image_quality": "good",
    "viewing_angle": "front"
  },
  "players": [
    {
      "player_id": 1,
      "jersey_number": {
        "value": "7",
        "confidence": "high"
      },
      "team": {
        "name": "Saskatchewan Roughriders",
        "colors_visible": ["green", "white"],
        "confidence": "high"
      },
      "visual_evidence": ["..."],
      "bounding_box": {
        "description": "center foreground"
      },
      "overall_confidence": "high"
    }
  ],
  "context": {
    "game_situation": "...",
    "stadium": "Unknown",
    "approximate_date": "Unknown",
    "additional_notes": null
  }
}
```

---

## 2. Agent 2 Output (Player Name Search)

**File:** `utils.py` → `agent_2_find_player_name()`

**Format:** Returns a dictionary with snake_case keys

```json
{
  "player_name": "Trevor Harris",
  "confidence": "high",
  "reasoning": "Multiple authoritative sources confirm this player",
  "sources": ["cfl.ca", "wikipedia.org"]
}
```

**Error Format:**
```json
{
  "player_name": "Unknown",
  "confidence": "low",
  "error": "Search failed: reason",
  "reasoning": "An error occurred during the search",
  "sources": []
}
```

---

## 3. Combined Player Object (After Agent 2)

**File:** `utils.py` → `process_player_identification()`

Agent 2's response is merged into the player object:

```json
{
  "player_id": 1,
  "jersey_number": {
    "value": "7",
    "confidence": "high"
  },
  "team": {
    "name": "Saskatchewan Roughriders",
    "colors_visible": ["green", "white"],
    "confidence": "high"
  },
  "player_name": {
    "value": "Trevor Harris",
    "confidence": "high"
  },
  "web_search": {
    "player_name": "Trevor Harris",
    "confidence": "high",
    "reasoning": "...",
    "sources": ["..."]
  },
  "visual_evidence": ["..."],
  "bounding_box": {"description": "center foreground"},
  "overall_confidence": "high"
}
```

---

## 4. Filtered Player Output

**File:** `main.py` → `filter_high_confidence_players()`

Returns flattened structure with only high-confidence players (2+ high-confidence fields).

**Important:** Team names are normalized at this stage to match database format.

```json
[
  {
    "player_name": "Trevor Harris",
    "player_team": "Saskatchewan Roughriders",  // Normalized (e.g., "Roughriders" → "Saskatchewan Roughriders")
    "player_number": "7"
  }
]
```

### Team Name Normalization

The filter applies `normalize_team_name()` to handle vision model variations:
- "Alouettes" → "Montreal Alouettes"
- "Roughriders" → "Saskatchewan Roughriders"
- "Stampeders" → "Calgary Stampeders"
- etc.

This ensures database lookups succeed in the verification step.

---

## 5. Verified Player Output

**File:** `main.py` → `verify_players_in_database()`

Same structure as filtered, but verified against database:

```json
[
  {
    "player_name": "Trevor Harris",
    "player_team": "Saskatchewan Roughriders",
    "player_number": "7"
  }
]
```

---

## 6. Telemetry Structure

**File:** `utils.py` → `process_player_identification()` (second return value)

```json
{
  "agent_1": {
    "input_tokens": 1250,
    "output_tokens": 450
  },
  "agent_2": {
    "input_tokens": 850,
    "output_tokens": 120
  },
  "total": {
    "input_tokens": 2100,
    "output_tokens": 570
  }
}
```

---

## Naming Conventions

### Python Code (snake_case)
- `player_name`
- `player_team`
- `player_number`
- `jersey_number`
- `input_tokens`
- `output_tokens`

### JSON Field Names (snake_case)
All JSON structures use **snake_case** for consistency with Python conventions:
- `player_name` (not `playerName`)
- `jersey_number` (not `jerseyNumber`)
- `input_tokens` (not `inputTokens`)

This provides a consistent interface between the LLM responses and Python code.
