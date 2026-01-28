# Migration Guide - From Hackathon to Production

## Overview

This guide explains how to migrate from the original flat structure to the new modular architecture.

## What Changed

### Old Structure
```
player-identification/
├── app.py
├── main.py
├── utils.py
├── prompt.py
├── test.py, test_*.py
└── cfl_players.json
```

### New Structure
```
player-identification/
├── src/
│   ├── core/           # Configuration, exceptions, logging
│   ├── agents/         # Vision & Search agents
│   ├── services/       # Business logic orchestration
│   ├── repositories/   # Data access layer
│   ├── tools/          # External tool integrations
│   ├── models/         # Data models
│   └── utils/          # Utility functions
├── tests/              # Organized test suite
├── infrastructure/     # Docker, CI/CD
├── docs/              # Documentation
├── scripts/           # Utility scripts
└── app.py             # Entry point (updated)
```

## Migration Steps

### Step 1: Backup Current Code

```bash
# Create backup
cp -r . ../player-identification-backup

# Or create git branch
git checkout -b pre-refactor-backup
git add .
git commit -m "Backup before refactoring"
git checkout modular  # Your refactored branch
```

### Step 2: Set Up New Dependencies

```bash
# The refactored code requires additional packages
uv sync --extra dev

# Or just core dependencies
uv sync
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
# (Same values as before, but now validated)

# Set secure permissions
chmod 600 .env

# Install git hooks
bash scripts/setup_git_hooks.sh
```

### Step 4: Update Import Statements

If you have custom scripts importing the old code:

**Old:**
```python
from utils import process_player_identification
from main import filter_high_confidence_players
```

**New:**
```python
from src.agents.vision_agent import VisionAgent
from src.agents.search_agent import SearchAgent  
from src.services.player_service import PlayerIdentificationService
from src.repositories.player_repository import PlayerRepository
from prompt import get_prompt, get_player_search_prompt
```

### Step 5: Update app.py Usage

The old `app.py` called functions directly. The new version uses the service layer.

**Old:**
```python
from utils import process_player_identification
from main import filter_high_confidence_players, verify_players_in_database

result, telemetry = process_player_identification(image_path)
filtered = filter_high_confidence_players(result)
verified = verify_players_in_database(filtered, player_data)
```

**New (handled internally by service):**
```python
from src.services.player_service import PlayerIdentificationService
from src.agents.vision_agent import VisionAgent
from src.agents.search_agent import SearchAgent
from src.repositories.player_repository import PlayerRepository
from prompt import get_prompt, get_player_search_prompt

# Initialize components
vision_agent = VisionAgent(get_prompt())
search_agent = SearchAgent(get_player_search_prompt())
repository = PlayerRepository()

# Create service
service = PlayerIdentificationService(vision_agent, search_agent, repository)

# Use service
verified_players, telemetry = service.identify_players(image_path)
```

## Code Mapping Reference

### Functions → Classes

| Old Function (utils.py) | New Location |
|-------------------------|--------------|
| `process_player_identification()` | `PlayerIdentificationService.identify_players()` |
| `agent_1_extract_team_and_jersey()` | `VisionAgent.execute()` |
| `agent_2_find_player_name()` | `SearchAgent.execute()` |
| `web_search_tool()` | `src/tools/web_search.py::web_search_tool()` |

| Old Function (main.py) | New Location |
|-----------------------|--------------|
| `filter_high_confidence_players()` | `PlayerIdentificationService._filter_high_confidence_players()` |
| `verify_players_in_database()` | `PlayerIdentificationService._verify_players_in_database()` |
| `normalize_team_name()` | `src/utils/team_normalizer.py::normalize_team_name()` |
| `load_player_data()` | `PlayerRepository.__init__()` |
| `download_image()` | `ImageService.download_image()` |

### Configuration

| Old | New |
|-----|-----|
| Direct `os.getenv()` calls | `src/core/config.py::get_settings()` |
| Hardcoded constants | `src/core/constants.py` |
| Manual logging setup | `src/core/logging_config.py::configure_logging()` |

## Testing the Migration

### 1. Run Unit Tests

```bash
# Should all pass
uv run pytest tests/unit/ -v
```

### 2. Test Basic Functionality

```python
# test_migration.py
from src.core.config import get_settings, validate_configuration
from src.repositories.player_repository import PlayerRepository
from src.utils.team_normalizer import normalize_team_name

# Test configuration
validate_configuration()
print("✓ Configuration OK")

# Test repository
repo = PlayerRepository()
player = repo.find_by_team_and_number("Montreal Alouettes", "10")
print(f"✓ Repository OK: Found {player}")

# Test team normalization
normalized = normalize_team_name("Alouettes")
assert normalized == "Montreal Alouettes"
print("✓ Team normalization OK")
```

### 3. Test Streamlit App

```bash
# Run the app
uv run streamlit run app.py

# Test with known image URL
# Verify results match old behavior
```

## Breaking Changes

### 1. Import Paths Changed
- All `src/` imports now required
- Old direct imports no longer work

### 2. Configuration Required
- Must have `.env` file or environment variables
- Configuration validation happens at startup
- Missing config causes immediate failure (fail-fast)

### 3. Error Types Changed
- Old: Generic `Exception`
- New: Custom exceptions from `src/core/exceptions.py`
- Code catching exceptions should update

### 4. Return Types Changed
- Some functions now return data classes instead of dicts
- Telemetry is now a proper `CombinedTelemetry` object
- Players can be `VerifiedPlayer` objects

## Compatibility Mode (Transitional)

If you need temporary backward compatibility:

```python
# src/compat.py (create if needed)
"""Compatibility layer for old code."""

from src.services.player_service import PlayerIdentificationService
from src.agents.vision_agent import VisionAgent
from src.agents.search_agent import SearchAgent
from src.repositories.player_repository import PlayerRepository
from prompt import get_prompt, get_player_search_prompt

# Global service instance (not recommended for production)
_service = None

def get_service():
    global _service
    if _service is None:
        vision_agent = VisionAgent(get_prompt())
        search_agent = SearchAgent(get_player_search_prompt())
        repository = PlayerRepository()
        _service = PlayerIdentificationService(vision_agent, search_agent, repository)
    return _service

# Old-style function for backward compatibility
def process_player_identification(image_path: str):
    """Legacy wrapper function."""
    service = get_service()
    verified_players, telemetry = service.identify_players(image_path)
    
    # Convert to old format
    result = {
        "players": [p.to_dict() for p in verified_players]
    }
    telemetry_dict = telemetry.to_dict()
    
    return result, telemetry_dict
```

## Rollback Plan

If you need to rollback:

```bash
# Option 1: Git
git checkout pre-refactor-backup

# Option 2: From backup
rm -rf src/ tests/ infrastructure/ docs/
cp -r ../player-identification-backup/* .

# Reinstall old dependencies
uv sync
```

## Validation Checklist

After migration, verify:

- [ ] Configuration loads without errors
- [ ] Tests pass
- [ ] Streamlit app starts
- [ ] Image processing works
- [ ] Player identification returns results
- [ ] Telemetry data is collected
- [ ] Logs are written properly
- [ ] Docker build succeeds (if using)
- [ ] CI pipeline passes (if configured)

## Getting Help

If you encounter issues:

1. Check error messages (now more descriptive)
2. Enable verbose logging: `LOG_LEVEL=DEBUG`
3. Review migration guide thoroughly
4. Check the architecture documentation
5. Run tests to identify specific failures

## Next Steps

After successful migration:

1. **Remove old files** (after confirming everything works):
   ```bash
   # Old test files
   rm test.py test_*.py
   
   # Temporary files
   rm temp_image_* downloaded_*
   ```

2. **Update documentation**:
   - Update README.md if needed
   - Document any custom modifications

3. **Set up CI/CD**:
   ```bash
   git push origin modular
   # GitHub Actions will run automatically
   ```

4. **Deploy to production**:
   - Follow deployment guide
   - Test in staging first
   - Monitor closely after deployment

## Benefits of New Architecture

- ✅ **Modular**: Easy to understand and modify
- ✅ **Testable**: Comprehensive test coverage
- ✅ **Maintainable**: Clear separation of concerns
- ✅ **Scalable**: Ready for growth
- ✅ **Secure**: Built-in security best practices
- ✅ **Production-Ready**: Docker, CI/CD, monitoring
- ✅ **Type-Safe**: Pydantic validation
- ✅ **Well-Documented**: Architecture, deployment guides
