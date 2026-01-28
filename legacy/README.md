# Legacy Code

This folder contains the original hackathon code for reference purposes.

## Files

### `main.py`
Original CLI entry point and utility functions including:
- `download_image()` - Image downloading
- `load_player_data()` - Database loading
- `filter_high_confidence_players()` - Player filtering logic
- `verify_players_in_database()` - Database verification
- `normalize_team_name()` - Team name normalization
- CLI interface with argparse

**Status:** ❌ **Deprecated** - Replaced by modular architecture in `src/`

**New equivalents:**
- Image handling → `src/services/image_service.py`
- Player filtering → `src/services/player_service.py`
- Database access → `src/repositories/player_repository.py`
- Team normalization → `src/utils/team_normalizer.py`

### `utils.py`
Original agent orchestration and tools:
- `process_player_identification()` - Main workflow
- `agent_1_extract_team_and_jersey()` - Vision agent (Agent 1)
- `agent_2_find_player_name()` - Search agent (Agent 2)
- `web_search_tool()` - SerpAPI integration
- Token telemetry extraction

**Status:** ❌ **Deprecated** - Replaced by modular agents in `src/agents/`

**New equivalents:**
- Agent orchestration → `src/services/player_service.py`
- Vision agent → `src/agents/vision_agent.py`
- Search agent → `src/agents/search_agent.py`
- Web search tool → `src/tools/web_search.py`
- Base agent → `src/agents/base.py`

## Why These Were Moved

The original code worked well for a hackathon but had several limitations:

### Issues with Original Code
- ❌ **Monolithic**: All logic in 2 large files (410+ lines each)
- ❌ **Hard to test**: Tightly coupled components
- ❌ **No separation of concerns**: Business logic mixed with I/O
- ❌ **Limited error handling**: Basic try/catch without custom exceptions
- ❌ **No retry logic**: Transient failures caused complete failure
- ❌ **Hardcoded values**: Magic numbers and strings scattered throughout
- ❌ **Global state**: Configuration via environment variables without validation

### Improvements in New Architecture
- ✅ **Modular**: Clear separation into agents, services, repositories, utilities
- ✅ **Testable**: Each component can be tested independently
- ✅ **SOLID principles**: Single responsibility, dependency injection
- ✅ **Robust error handling**: Custom exception hierarchy
- ✅ **Resilience**: Retry logic, circuit breakers
- ✅ **Configuration management**: Type-safe Pydantic settings
- ✅ **Production-ready**: Logging, monitoring, security

## How to Use New Code

### Running the Application
```bash
# Use the updated app.py (now uses src/ modules)
uv run streamlit run app.py
```

### Importing New Modules
```python
# OLD (deprecated)
from main import filter_high_confidence_players
from utils import process_player_identification

# NEW (use this)
from src.services.player_service import PlayerIdentificationService
from src.agents.vision_agent import VisionAgent
from src.agents.search_agent import SearchAgent
```

## Migration Guide

For detailed migration instructions, see:
- **[docs/MIGRATION_GUIDE.md](../docs/MIGRATION_GUIDE.md)** - Step-by-step migration
- **[docs/architecture.md](../docs/architecture.md)** - New architecture overview
- **[docs/REFACTORING_SUMMARY.md](../docs/REFACTORING_SUMMARY.md)** - What changed

## When to Reference This Code

✅ **Good reasons to look here:**
- Understanding the original implementation
- Comparing old vs new approaches
- Historical reference for git commits
- Learning what patterns to avoid

❌ **Bad reasons:**
- Building new features (use `src/` instead)
- Fixing bugs (fix in `src/` instead)
- Copy-pasting code (refactored version is better)

## Deleting This Folder

Once you're confident the new architecture works, you can safely delete this folder. The code is preserved in git history:

```bash
# To see old code in git history
git log --all --full-history -- legacy/main.py
git log --all --full-history -- legacy/utils.py

# To restore if needed
git checkout <commit-hash> -- legacy/main.py
```

---

**Date Moved:** January 28, 2026  
**Reason:** Production refactoring completed  
**Status:** Reference only - do not use for new development
