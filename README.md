# CFL Player Identification

AI-powered system to identify Canadian Football League (CFL) players from images using computer vision and web search.

## Overview

This application uses a multi-agent approach to identify CFL players in images:
- **Agent 1 (Vision)**: Analyzes images to extract team name and jersey number
- **Agent 2 (Web Search)**: Searches the web to find player names based on team and number
- **Database Verification**: Validates results against a CFL player database

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- AWS credentials with Bedrock access
- SerpAPI key for web search

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd player-identification
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   SERP_API_KEY=your_serpapi_key_here
   AWS_PROFILE=your_aws_profile
   AWS_REGION=us-east-1
   ```

4. **Run the application**
   ```bash
   uv run streamlit run app.py
   ```

## Usage

### Streamlit Web Application

The main entry point is `app.py`, a Streamlit web application.

```bash
# Normal mode (INFO level logging)
uv run streamlit run app.py

# Verbose mode (DEBUG level logging) - shows detailed agent responses
uv run streamlit run app.py -- --verbose
```

**In the web interface:**
1. Paste an image URL
2. Click "Identify Players"
3. View identified players with confidence scores
4. See token usage telemetry

### Logging Levels

- **INFO** (default): Shows important progress, results, and telemetry
- **DEBUG** (verbose mode): Shows detailed debugging information:
  - Raw agent responses (before JSON parsing)
  - Web search queries and results
  - Team name normalization
  - Detailed parsing information
  - Complete token usage for each agent call

## Architecture & Workflow

### Data Flow

```
Image URL
    ↓
Download Image
    ↓
Agent 1 (Vision Model - AWS Bedrock Claude Sonnet)
    ↓ Extracts: team name, jersey number, confidence levels
JSON Response
    ↓
Agent 2 (Web Search via SerpAPI)
    ↓ Searches: "CFL [team] jersey number [#] player name"
JSON Response (player name, confidence, sources)
    ↓
Filter High-Confidence Players (2+ high-confidence fields)
    ↓ Normalizes team names (e.g., "Alouettes" → "Montreal Alouettes")
Verify Against Database (cfl_players.json)
    ↓
Display Results + Token Telemetry
```

### Components

**Core Files:**
- `app.py` - Streamlit web application (main entry point)
- `utils.py` - Agent orchestration, vision analysis, web search
- `main.py` - Filtering and database verification functions
- `prompt.py` - System prompts for both agents

**Configuration:**
- `.env` - Environment variables (API keys, AWS config)
- `cfl_players.json` - Player database (team → number → name mapping)

**Documentation:**
- `JSON_STRUCTURE.md` - Complete data structure documentation
- `TROUBLESHOOTING.md` - Debugging JSON parsing issues
- `TEAM_NAME_FIX.md` - Team name normalization details

### Multi-Agent System

**Agent 1: Vision Analysis**
- Model: AWS Bedrock Claude Sonnet (vision-capable)
- Input: Image path
- Output: Team name, jersey number, confidence levels
- Tool: `image_reader` (Strands tool)

**Agent 2: Player Name Search**
- Model: AWS Bedrock Claude Sonnet
- Input: Team name, jersey number
- Output: Player name, confidence, reasoning, sources
- Tool: `web_search_tool` (SerpAPI via custom tool)

### Confidence Filtering

Players are only included if they have **2 or more high-confidence fields**:
- Jersey number confidence: high
- Team confidence: high
- Player name confidence: high

### Team Name Normalization

The system automatically normalizes team names to match the database:
- "Alouettes" → "Montreal Alouettes"
- "Roughriders" → "Saskatchewan Roughriders"
- "Stampeders" → "Calgary Stampeders"
- etc.

See `TEAM_NAME_FIX.md` for complete mapping.


## Telemetry & Token Usage

The application tracks token usage for both agents:

```
Agent 1 (Vision):  Input: 1,250 tokens | Output: 450 tokens
Agent 2 (Search):  Input: 850 tokens  | Output: 120 tokens
Total:             Input: 2,100 tokens | Output: 570 tokens
```

This helps you:
- Monitor AWS Bedrock costs
- Optimize prompt efficiency
- Track agent performance

## Example Output

### Successful Identification

**Input:** Image of Davis Alexander wearing #10 for Montreal Alouettes

**Output:**
```json
{
  "player_name": "Davis Alexander",
  "player_team": "Montreal Alouettes",
  "player_number": "10"
}
```

**Token Usage:**
- Agent 1: 1,234 input / 425 output tokens
- Agent 2: 812 input / 98 output tokens

## Sample Data Structures

### Agent 1 Vision Response

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
      "visual_evidence": [
        "Jersey number 7 clearly visible",
        "Saskatchewan Roughriders team name and logo on jersey"
      ],
      "bounding_box": {
        "description": "center foreground"
      },
      "overall_confidence": "high"
    }
  ],
  "context": {
    "game_situation": "Offensive play",
    "stadium": "Unknown",
    "approximate_date": "Unknown"
  }
}
```

### Agent 2 Web Search Response

```json
{
  "player_name": "Trevor Harris",
  "confidence": "high",
  "reasoning": "Multiple authoritative sources confirm Trevor Harris as #7 for Saskatchewan Roughriders",
  "sources": [
    "https://www.cfl.ca/players/trevor-harris/",
    "https://en.wikipedia.org/wiki/Trevor_Harris"
  ]
}
```

## Troubleshooting

### AWS Credentials

If you encounter AWS authentication issues:

```bash
# Clear conflicting environment variables
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN

# Use AWS profile from .env
export AWS_PROFILE=your_profile_name
```

### JSON Parsing Errors

If Agent 2 fails to parse responses, run in verbose mode:

```bash
uv run streamlit run app.py -- --verbose
```

This will show the raw LLM response. Common issues:
- LLM wraps JSON in markdown code blocks (automatically handled)
- LLM adds explanatory text (automatically extracted)
- Web search returns no results (check SERP_API_KEY)

See `TROUBLESHOOTING.md` for detailed debugging guide.

### Team Name Mismatches

If players aren't being verified, the team name might not match the database:
- Vision model returns: "Alouettes"
- Database expects: "Montreal Alouettes"

The system automatically normalizes these. See `TEAM_NAME_FIX.md` for details.

## Sample Test Image

```
https://res.cloudinary.com/dbmataac4/image/upload/v1765486287/ghgewenoaznomnmsutrv.jpg
```

## Documentation

- **`JSON_STRUCTURE.md`** - Complete data structures and flow
- **`TROUBLESHOOTING.md`** - Debugging JSON parsing issues
- **`TEAM_NAME_FIX.md`** - Team name normalization details

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: AWS Bedrock (Claude Sonnet with vision)
- **Agent Framework**: Strands Agents SDK
- **Web Search**: SerpAPI
- **Package Manager**: uv
- **Python**: 3.11+

## License

[Your license here]

---

**Built for CFL Player Identification Hackathon**