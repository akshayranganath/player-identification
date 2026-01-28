# CFL Player Identification

AI-powered system to identify Canadian Football League (CFL) players from images using computer vision and web search.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Usage](#usage)
- [Testing](#testing)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Tech Stack](#tech-stack)
- [Troubleshooting](#troubleshooting)

---

## Overview

This application uses a multi-agent AI system to identify CFL players from images:

- **Agent 1 (Vision)**: Analyzes images using AWS Bedrock Claude Sonnet to extract team names and jersey numbers
- **Agent 2 (Web Search)**: Searches the web via SerpAPI to find player names based on extracted information
- **Database Verification**: Validates results against a comprehensive CFL player database

### Key Features

✅ **Production-Ready Architecture** - Modular, testable, maintainable codebase  
✅ **Multi-Agent AI System** - Vision analysis + web search orchestration  
✅ **Comprehensive Testing** - Unit, integration, and E2E test suites  
✅ **Docker Support** - Containerized deployment with Docker Compose  
✅ **CI/CD Pipeline** - Automated testing and quality checks  
✅ **Structured Logging** - JSON logging for production monitoring  
✅ **Type Safety** - Pydantic models and type hints throughout  
✅ **Security** - Input validation, secret management, git hooks  

---

## Quick Start

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** package manager
- **AWS credentials** with Bedrock access (Claude Sonnet)
- **SerpAPI key** for web search

### Installation

**1. Clone the repository**
```bash
git clone <repository-url>
cd player-identification
```

**2. Install dependencies**
```bash
# Install all dependencies including dev tools
uv sync --extra dev

# Or for production only
uv sync
```

**3. Configure environment**
```bash
# Copy the template
cp .env.example .env

# Edit with your credentials
nano .env

# Secure the file (Unix/Mac)
chmod 600 .env

# Install git hooks to prevent accidental .env commits
bash scripts/setup_git_hooks.sh
```

**4. Run the application**
```bash
# Start Streamlit web app
uv run streamlit run app.py

# Or with verbose logging (shows detailed agent responses)
uv run streamlit run app.py -- --verbose
```

Access the app at: **http://localhost:8501**

---

## Architecture

### High-Level Overview

```
┌─────────────────┐
│   Streamlit UI  │  (Presentation Layer)
└────────┬────────┘
         │
┌────────▼────────────────────────────────┐
│   PlayerIdentificationService           │  (Service Layer)
│   - Orchestrates workflow               │
│   - Handles business logic              │
└────┬──────────────────────────┬─────────┘
     │                          │
┌────▼────────┐        ┌────────▼──────┐
│ VisionAgent │        │ SearchAgent   │  (Agent Layer)
│ (Bedrock)   │        │ (SerpAPI)     │
└─────────────┘        └───────────────┘
         │                      │
         └──────────┬───────────┘
                    │
         ┌──────────▼──────────┐
         │ PlayerRepository    │  (Repository Layer)
         │ (cfl_players.json)  │
         └─────────────────────┘
```

### Project Structure

```
player-identification/
├── src/                          # Application code
│   ├── core/                     # Core configuration and constants
│   │   ├── config.py            # Pydantic Settings configuration
│   │   ├── constants.py         # Global constants
│   │   ├── exceptions.py        # Custom exception hierarchy
│   │   └── logging_config.py   # Structured logging setup
│   ├── agents/                   # AI agents
│   │   ├── base.py              # Base agent class
│   │   ├── vision_agent.py      # Image analysis (Agent 1)
│   │   └── search_agent.py      # Player name search (Agent 2)
│   ├── services/                 # Business logic
│   │   ├── player_service.py    # Player identification workflow
│   │   └── image_service.py     # Image handling
│   ├── repositories/             # Data access
│   │   └── player_repository.py # Player database access
│   ├── models/                   # Data models
│   │   ├── player.py            # Player, team, jersey models
│   │   └── telemetry.py         # Token usage tracking
│   ├── tools/                    # External integrations
│   │   └── web_search.py        # SerpAPI integration
│   └── utils/                    # Utilities
│       ├── validators.py        # Input validation
│       ├── team_normalizer.py   # Team name normalization
│       ├── json_parser.py       # Robust JSON parsing
│       ├── retry.py             # Retry with backoff
│       └── circuit_breaker.py   # Circuit breaker pattern
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── conftest.py              # Pytest fixtures
├── infrastructure/               # Deployment
│   ├── docker/                  # Docker configs
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── terraform/               # IaC for AWS
│   └── k8s/                     # Kubernetes manifests
├── docs/                         # Documentation
│   ├── architecture.md          # Detailed architecture
│   ├── deployment.md            # Deployment guide
│   ├── MIGRATION_GUIDE.md       # Migration from old structure
│   └── REFACTORING_SUMMARY.md   # What changed
├── scripts/                      # Utility scripts
│   └── setup_git_hooks.sh       # Git hook installer
├── app.py                        # Streamlit entry point
├── prompt.py                     # AI agent prompts
├── .env.example                  # Environment template
└── pyproject.toml               # Dependencies
```

### Design Patterns

- **Layered Architecture**: Clear separation of presentation, service, agent, repository layers
- **Repository Pattern**: Abstracted data access
- **Service Layer Pattern**: Business logic orchestration
- **Dependency Injection**: Loose coupling between components
- **Circuit Breaker**: Fault tolerance for external services
- **Retry with Backoff**: Resilience against transient failures

---

## Usage

### Web Interface

1. **Start the application**:
   ```bash
   uv run streamlit run app.py
   ```

2. **In your browser** (http://localhost:8501):
   - Paste an image URL containing a CFL player
   - Click "Identify Players"
   - View identified players with confidence scores
   - See token usage telemetry

### Sample Image URL
```
https://res.cloudinary.com/dbmataac4/image/upload/v1765486287/ghgewenoaznomnmsutrv.jpg
```

### Logging Levels

**INFO (default)**: Important progress, results, telemetry
```bash
uv run streamlit run app.py
```

**DEBUG (verbose)**: Detailed debugging information
```bash
uv run streamlit run app.py -- --verbose
```

Debug mode shows:
- Raw agent responses (before JSON parsing)
- Web search queries and results
- Team name normalization steps
- Complete token usage for each agent call

### Example Output

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
```
Agent 1 (Vision):  Input: 1,234 | Output: 425 tokens
Agent 2 (Search):  Input: 812   | Output: 98 tokens
Total:             Input: 2,046 | Output: 523 tokens
```

---

## Testing

### Run Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=src --cov-report=html

# Run specific test suite
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v

# Run specific test file
uv run pytest tests/unit/test_team_normalizer.py -v

# Run with verbose output
uv run pytest tests/ -v -s
```

### Code Quality

```bash
# Linting
uv run ruff check src/ tests/
uv run black --check src/ tests/
uv run isort --check-only src/ tests/

# Type checking
uv run mypy src/

# Security scanning
uv run bandit -r src/
uv run safety check
```

### Test Structure

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test full workflows (vision → search → verification)
- **Fixtures**: Reusable test data and mocks in `tests/conftest.py`

---

## Deployment

### Docker (Recommended)

**Using Docker Compose:**
```bash
# Start all services (app + redis)
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# View logs
docker-compose -f infrastructure/docker/docker-compose.yml logs -f

# Stop services
docker-compose -f infrastructure/docker/docker-compose.yml down
```

**Using Docker CLI:**
```bash
# Build image
docker build -f infrastructure/docker/Dockerfile -t cfl-player-id:latest .

# Run container
docker run -p 8501:8501 --env-file .env cfl-player-id:latest
```

### AWS ECS Deployment

See detailed guide: **[docs/deployment.md](docs/deployment.md)**

Includes:
- Infrastructure as Code (Terraform)
- CI/CD pipeline setup
- Environment-specific configurations
- Monitoring and logging setup

### Traditional Server

```bash
# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with production values

# Run with production settings
ENVIRONMENT=production uv run streamlit run app.py
```

---

## Configuration

### Environment Variables

Create a `.env` file (use `.env.example` as template):

**Required:**
```env
# SerpAPI for web search
SERP_API_KEY=your_serpapi_key_here

# AWS Bedrock access
AWS_PROFILE=your_aws_profile
AWS_REGION=us-east-1
```

**Optional:**
```env
# Application
ENVIRONMENT=development          # development, staging, production
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=console               # console or json

# Image Processing
MAX_IMAGE_SIZE_MB=10
SUPPORTED_IMAGE_FORMATS=jpg,jpeg,png,webp

# Rate Limiting
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=2.0
CIRCUIT_BREAKER_THRESHOLD=5

# Database
PLAYER_DB_PATH=data/db/cfl_players.json
```

### Security Best Practices

**Protect your `.env` file:**
```bash
# Set restrictive permissions
chmod 600 .env

# Install git hooks to prevent commits
bash scripts/setup_git_hooks.sh

# Verify it's in .gitignore
git check-ignore .env
```

**Never commit:**
- `.env` files with real credentials
- AWS access keys
- API keys
- Any secrets

**Use `.env.example` for:**
- Documentation of required variables
- Safe-to-commit template
- Onboarding new developers

---

## Documentation

### Core Documentation

- **[docs/architecture.md](docs/architecture.md)** - Detailed system design, patterns, and data flow
- **[docs/deployment.md](docs/deployment.md)** - Deployment options and procedures
- **[docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)** - Migrating from old structure
- **[docs/REFACTORING_SUMMARY.md](docs/REFACTORING_SUMMARY.md)** - Complete refactoring summary

### Legacy Documentation

- **[docs/JSON_STRUCTURE.md](docs/JSON_STRUCTURE.md)** - Agent response data structures
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Debugging JSON parsing issues
- **[docs/TEAM_NAME_FIX.md](docs/TEAM_NAME_FIX.md)** - Team name normalization details

---

## Tech Stack

### Core Technologies

- **Frontend**: Streamlit 1.52+
- **Language**: Python 3.12+
- **Package Manager**: uv (fast, modern alternative to pip/poetry)

### AI & Agents

- **LLM**: AWS Bedrock (Claude Sonnet with vision capabilities)
- **Agent Framework**: Strands Agents SDK
- **Web Search**: SerpAPI (Google Search API)

### Configuration & Validation

- **Settings**: Pydantic Settings 2.5+
- **Validation**: Pydantic models throughout
- **Environment**: python-dotenv

### Infrastructure

- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **IaC**: Terraform (AWS)
- **Orchestration**: Kubernetes (optional)

### Development Tools

- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Linting**: ruff, black, isort
- **Type Checking**: mypy
- **Security**: bandit, safety

### Optional Performance

- **Caching**: Redis (optional)
- **Async I/O**: aiofiles, httpx (optional)
- **Monitoring**: structlog, sentry-sdk (optional)

---

## Troubleshooting

### Common Issues

#### Configuration Errors

**Problem**: `ValidationError` on startup

**Solution**:
```bash
# Verify your .env file exists
cat .env

# Validate configuration
uv run python -m src.core.config

# Check file permissions
ls -la .env  # Should be -rw------- (600)
```

#### AWS Authentication

**Problem**: `NoCredentialsError` or authentication failures

**Solution**:
```bash
# Clear conflicting environment variables
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN

# Use AWS profile from .env
export AWS_PROFILE=your_profile_name

# Verify profile works
aws bedrock list-foundation-models --region us-east-1
```

#### JSON Parsing Errors

**Problem**: Agent returns unparseable JSON

**Solution**:
```bash
# Run in verbose mode to see raw responses
uv run streamlit run app.py -- --verbose
```

Common causes:
- LLM wraps JSON in markdown code blocks (automatically handled)
- LLM adds explanatory text (automatically extracted)
- Web search returns no results (check `SERP_API_KEY`)

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed debugging.

#### Team Name Mismatches

**Problem**: Players not verified against database

**Cause**: Vision model returns "Alouettes" but database expects "Montreal Alouettes"

**Solution**: Team name normalization is automatic. See [docs/TEAM_NAME_FIX.md](docs/TEAM_NAME_FIX.md) for mapping details.

#### Import Errors

**Problem**: `ModuleNotFoundError` or import issues

**Solution**:
```bash
# Reinstall dependencies
uv sync --reinstall

# Verify Python version
python --version  # Should be 3.12+

# Check uv installation
uv --version
```

### Getting Help

1. **Check logs**: Run with `--verbose` flag for detailed output
2. **Review docs**: See `docs/` folder for comprehensive guides
3. **Validate setup**: Run tests to verify installation
4. **Check issues**: See GitHub issues for known problems

---

## Migration from Old Structure

If you're upgrading from the original hackathon code, see the comprehensive migration guide:

**[docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)**

Includes:
- Code mapping (old → new file structure)
- Breaking changes
- Step-by-step migration procedure
- Testing checklist

---

## Development

### Common Commands

```bash
# Install dependencies with dev tools
uv sync --extra dev

# Run application locally
uv run streamlit run app.py

# Run tests
uv run pytest tests/ -v

# Code formatting
uv run black src/ tests/
uv run isort src/ tests/

# Linting
uv run ruff check src/ tests/

# Type checking
uv run mypy src/

# Security scanning
uv run bandit -r src/
uv run safety check

# Update dependencies
uv sync --upgrade
```

### Contributing

1. Install git hooks: `bash scripts/setup_git_hooks.sh`
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run quality checks: `uv run pytest && uv run ruff check`
5. Commit and push
6. CI pipeline will run automatically

---

## License

[Your license here]

---

## Acknowledgments

**Built for CFL Player Identification Hackathon**

Powered by:
- AWS Bedrock (Claude Sonnet)
- Strands Agents SDK
- SerpAPI

---

## Contact & Support

- **Documentation**: See `docs/` folder
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Deployment**: [docs/deployment.md](docs/deployment.md)
