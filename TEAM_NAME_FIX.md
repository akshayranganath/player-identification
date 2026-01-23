# Team Name Normalization Fix

## Problem Identified

The vision model (Agent 1) returned **"Alouettes"** but the database has **"Montreal Alouettes"**.

This caused the verification to fail because:
1. Filter passed player with team="Alouettes"
2. Database lookup failed because "Alouettes" ≠ "Montreal Alouettes"
3. Player was skipped even though it was correctly identified

## Solution Implemented

Added a **team name normalization** system that:
1. Maps short names to full database names
2. Handles case-insensitive matching
3. Logs all normalizations for debugging

### Team Name Mapping

```python
TEAM_NAME_MAPPING = {
    # Full names
    "BC Lions": "BC Lions",
    "Calgary Stampeders": "Calgary Stampeders",
    "Edmonton Elks": "Edmonton Elks",
    "Hamilton Tiger-Cats": "Hamilton Tiger-Cats",
    "Montreal Alouettes": "Montreal Alouettes",
    "Ottawa Redblacks": "Ottawa Redblacks",
    "Saskatchewan Roughriders": "Saskatchewan Roughriders",
    "Toronto Argonauts": "Toronto Argonauts",
    "Winnipeg Blue Bombers": "Winnipeg Blue Bombers",
    
    # Short names
    "Lions": "BC Lions",
    "Stampeders": "Calgary Stampeders",
    "Elks": "Edmonton Elks",
    "Tiger-Cats": "Hamilton Tiger-Cats",
    "Alouettes": "Montreal Alouettes",  # ← Fixes your issue!
    "Redblacks": "Ottawa Redblacks",
    "Roughriders": "Saskatchewan Roughriders",
    "Argonauts": "Toronto Argonauts",
    "Blue Bombers": "Winnipeg Blue Bombers",
    
    # City names only
    "Calgary": "Calgary Stampeders",
    "Edmonton": "Edmonton Elks",
    "Hamilton": "Hamilton Tiger-Cats",
    "Montreal": "Montreal Alouettes",
    "Ottawa": "Ottawa Redblacks",
    "Saskatchewan": "Saskatchewan Roughriders",
    "Toronto": "Toronto Argonauts",
    "Winnipeg": "Winnipeg Blue Bombers",
}
```

## Changes Made

### 1. Added `normalize_team_name()` function
- Handles exact matches
- Handles case-insensitive matches
- Logs warnings for unknown team names
- Returns original name if no match found

### 2. Applied normalization in `filter_high_confidence_players()`
- Normalizes team name when high confidence is detected
- Normalizes team name when filling in from lower confidence data
- Team names are normalized BEFORE being passed to verification

### 3. Enhanced logging throughout
- DEBUG level: Shows raw player JSON, normalization steps
- INFO level: Shows filtered players, verified players
- WARNING level: Shows missing teams/numbers in database

## Testing Your Case

For your player data:
```json
{
  "team": {
    "name": "Alouettes",  // Vision model returned this
    "confidence": "high"
  },
  "jersey_number": {
    "value": 10,
    "confidence": "high"
  },
  "player_name": {
    "value": "Davis Alexander",
    "confidence": "high"
  }
}
```

**Before fix:**
- Filter: team="Alouettes" ✅
- Verify: lookup "Alouettes" in database ❌ (not found)
- Result: Player skipped ❌

**After fix:**
- Filter: team="Alouettes" → normalized to "Montreal Alouettes" ✅
- Verify: lookup "Montreal Alouettes" in database ✅
- Result: Player verified ✅

## Logging Output

With the fix, you'll now see:
```
INFO - Normalized team name: 'Alouettes' -> 'Montreal Alouettes'
INFO - Filtered player (high_confidence_count=3): {
  'player_name': 'Davis Alexander',
  'player_team': 'Montreal Alouettes',
  'player_number': '10'
}
INFO - Verified player in database: {
  'player_name': 'Davis Alexander',
  'player_team': 'Montreal Alouettes',
  'player_number': '10'
}
```

## Benefits

1. **Robust**: Handles various team name formats from vision model
2. **Extensible**: Easy to add new team name aliases
3. **Debuggable**: Clear logging shows what's happening
4. **Safe**: Returns original name if no match (doesn't break unknowns)

## Run It Again

Now run your test again:
```bash
uv run streamlit run app.py
```

The player should now be successfully identified and verified! 🎉
