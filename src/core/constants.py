"""
Global Constants

This module contains global constants used throughout the application.
"""

# ==============================================================================
# CFL TEAM NAMES
# ==============================================================================

# Full official team names
CFL_TEAMS = [
    "BC Lions",
    "Calgary Stampeders",
    "Edmonton Elks",
    "Hamilton Tiger-Cats",
    "Montreal Alouettes",
    "Ottawa Redblacks",
    "Saskatchewan Roughriders",
    "Toronto Argonauts",
    "Winnipeg Blue Bombers",
]

# Team name normalization mapping (short name -> full name)
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
    
    # Alternative names (city only)
    "Calgary": "Calgary Stampeders",
    "Edmonton": "Edmonton Elks",
    "Hamilton": "Hamilton Tiger-Cats",
    "Montreal": "Montreal Alouettes",
    "Ottawa": "Ottawa Redblacks",
    "Saskatchewan": "Saskatchewan Roughriders",
    "Toronto": "Toronto Argonauts",
    "Winnipeg": "Winnipeg Blue Bombers",
}

# ==============================================================================
# IMAGE VALIDATION
# ==============================================================================

# Allowed image file extensions
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]

# Maximum image size in megabytes
DEFAULT_MAX_IMAGE_SIZE_MB = 10

# ==============================================================================
# CONFIDENCE LEVELS
# ==============================================================================

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

VALID_CONFIDENCE_LEVELS = [CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW]

# Minimum number of high-confidence fields required for player inclusion
MIN_HIGH_CONFIDENCE_FIELDS = 2

# ==============================================================================
# AGENT CONFIGURATION
# ==============================================================================

# Default timeout for agent execution (seconds)
DEFAULT_AGENT_TIMEOUT = 30

# Default number of retries for agent operations
DEFAULT_AGENT_RETRIES = 3

# ==============================================================================
# WEB SEARCH
# ==============================================================================

# Default number of search results to retrieve
DEFAULT_SEARCH_RESULTS = 10

# Authoritative sources for CFL player information
AUTHORITATIVE_SOURCES = [
    "cfl.ca",
    "bluebombers.com",
    "bclions.com",
    "stampeders.com",
    "esks.com",
    "ticats.ca",
    "montrealalouettes.com",
    "ottawaredblacks.com",
    "riderville.com",
    "argonauts.ca",
    "wikipedia.org",
    "espn.com",
    "tsn.ca",
    "sportsnet.ca",
]

# ==============================================================================
# TELEMETRY
# ==============================================================================

# Token usage field names
TOKEN_INPUT = "inputTokens"
TOKEN_OUTPUT = "outputTokens"

# ==============================================================================
# HTTP
# ==============================================================================

# Default request timeout (seconds)
DEFAULT_REQUEST_TIMEOUT = 30

# User agent for HTTP requests
DEFAULT_USER_AGENT = "CFL-Player-Identification/1.0"
