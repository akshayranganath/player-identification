# Player Identification

## Objective

The purppose of the project is to identify the player in an image. When multiple players are shown, we should be able to identify at least the primary person shown in the image.

## Usage

### Streamlit Web App

Run the Streamlit web application:

```bash
# Normal mode (INFO level logging)
uv run streamlit run app.py

# Verbose mode (DEBUG level logging)
uv run streamlit run app.py -- --verbose
```

### CLI Application

Run the command-line interface:

```bash
# Normal mode (INFO level logging)
uv run main.py

# Verbose mode (DEBUG level logging)
uv run main.py --verbose
# or shorthand
uv run main.py -v
```

### Logging Levels

- **INFO** (default): Shows important progress and results
- **DEBUG** (verbose): Shows detailed debugging information including:
  - Raw agent responses
  - Web search queries and results
  - Detailed parsing information
  - Token usage for each agent call

## Workflow

1. Take an image
2. Pass it to a vision-based LLM to identify 2 things:
    * Team name
    * Player number from the T-Shirt
3. Once the team and T-Shirt number are identified, use the information to identify the player.


### Player Indentification

To identify a player, we want to support a flexible mechanism. The player information can be in one of the places:

* CSV file
* Database
* Webpage that contains the player information

This information will be passed into the LLM as a tool. The tool supplied will be configurable and part of the `.env` file.


## Troubleshooting

If you run into issues, make sure to run the following.

```
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
unset AWS_PROFILE  # optional, we'll explicitly pass it anyway
```

This will ensure other AWS picks up the right 

sample url: https://res.cloudinary.com/dbmataac4/image/upload/v1765486287/ghgewenoaznomnmsutrv.jpg


Sample JSON from LLM

```json
{
  "image_analysis": {
    "total_players_visible": 4,
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
      "position": {
        "value": "Quarterback",
        "confidence": "medium"
      },
      "visual_evidence": [
        "Jersey number 7 clearly visible",
        "Saskatchewan Roughriders team name and logo on jersey",
        "Standing upright in typical quarterback stance"
      ],
      "bounding_box": {
        "description": "center foreground"
      },
      "overall_confidence": "high"
    },
    {
      "player_id": 2,
      "team": {
        "name": "Saskatchewan Roughriders",
        "colors_visible": ["green", "white"],
        "confidence": "high"
      },
      "position": {
        "value": "Offensive Lineman",
        "confidence": "medium"
      },
      "visual_evidence": [
        "Wearing Saskatchewan Roughriders uniform",
        "Large frame typical of offensive lineman",
        "In stance blocking for the quarterback"
      ],
      "distinctive_features": null,
      "bounding_box": {
        "description": "left foreground"
      },
      "overall_confidence": "medium"
    },
    {
      "player_id": 3,
      "team": {
        "name": "Opposing Team",
        "colors_visible": ["red", "white"],
        "confidence": "high"
      },
      "position": {
        "value": "Defensive Lineman",
        "confidence": "medium"
      },
      "visual_evidence": [
        "Different uniform colors from Saskatchewan players",
        "Crouched stance facing offensive line"
      ],
      "bounding_box": {
        "description": "bottom center"
      },
      "overall_confidence": "medium"
    },
    {
      "player_id": 4,
      "team": {
        "name": "Opposing Team",
        "colors_visible": ["red", "white"],
        "confidence": "high"
      },
      "position": {
        "value": "Linebacker",
        "confidence": "low"
      },
      "visual_evidence": [
        "Wearing same uniform as player 3"
      ],
      "bounding_box": {
        "description": "right foreground"
      },
      "overall_confidence": "low"
    }
  ],
  "context": {
    "game_situation": "Offensive play with quarterback in shotgun formation",
    "stadium": "Unknown",
    "approximate_date": "Unknown",
    "additional_notes": null
  }
}

{
  "image_analysis": {
    "total_players_visible": 4,
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
      "position": {
        "value": "Quarterback",
        "confidence": "medium"
      },
      "visual_evidence": [
        "Jersey number 7 clearly visible",
        "Saskatchewan Roughriders team name and logo on jersey",
        "Standing upright in typical quarterback stance"
      ],
      "bounding_box": {
        "description": "center foreground"
      },
      "overall_confidence": "high"
    },
    {
      "player_id": 2,
      "team": {
        "name": "Saskatchewan Roughriders",
        "colors_visible": ["green", "white"],
        "confidence": "high"
      },
      "position": {
        "value": "Offensive Lineman",
        "confidence": "medium"
      },
      "visual_evidence": [
        "Wearing Saskatchewan Roughriders uniform",
        "Large frame typical of offensive lineman",
        "In stance blocking for the quarterback"
      ],
      "distinctive_features": null,
      "bounding_box": {
        "description": "left foreground"
      },
      "overall_confidence": "medium"
    },
    {
      "player_id": 3,
      "team": {
        "name": "Opposing Team",
        "colors_visible": ["red", "white"],
        "confidence": "high"
      },
      "position": {
        "value": "Defensive Lineman",
        "confidence": "medium"
      },
      "visual_evidence": [
        "Different uniform colors from Saskatchewan players",
        "Crouched stance facing offensive line"
      ],
      "bounding_box": {
        "description": "bottom center"
      },
      "overall_confidence": "medium"
    },
    {
      "player_id": 4,
      "team": {
        "name": "Opposing Team",
        "colors_visible": ["red", "white"],
        "confidence": "high"
      },
      "position": {
        "value": "Linebacker",
        "confidence": "low"
      },
      "visual_evidence": [
        "Wearing same uniform as player 3"
      ],
      "bounding_box": {
        "description": "right foreground"
      },
      "overall_confidence": "low"
    }
  ],
  "context": {
    "game_situation": "Offensive play with quarterback in shotgun formation",
    "stadium": "Unknown",
    "approximate_date": "Unknown",
    "additional_notes": null
  }
}
```