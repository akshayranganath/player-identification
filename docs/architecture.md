# Architecture Documentation

## System Overview

The CFL Player Identification system is a modular, production-ready application that uses AI agents to identify players from images.

## High-Level Architecture

```
┌─────────────────┐
│   Streamlit UI  │
│    (app.py)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Player Service Layer   │
│  (src/services/)        │
└────────┬────────────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
┌───────────────┐ ┌──────────┐ ┌──────────────┐
│ Vision Agent  │ │  Search  │ │  Repository  │
│   (Agent 1)   │ │  Agent   │ │    Layer     │
│               │ │ (Agent 2)│ │              │
└───────┬───────┘ └────┬─────┘ └──────┬───────┘
        │              │               │
        ▼              ▼               ▼
┌─────────────┐ ┌────────────┐ ┌──────────────┐
│ AWS Bedrock │ │  SerpAPI   │ │ Player DB    │
│   (Claude)  │ │  (Google)  │ │  (JSON)      │
└─────────────┘ └────────────┘ └──────────────┘
```

## Layer Architecture

### 1. Presentation Layer (`app.py`)
- **Streamlit web interface**
- User input handling
- Results display
- Image URL submission

### 2. Service Layer (`src/services/`)
- **PlayerIdentificationService**: Orchestrates the full identification workflow
- **ImageService**: Handles image downloading and validation
- Coordinates between agents and repositories
- Implements business logic

### 3. Agent Layer (`src/agents/`)
- **Base Agent**: Common functionality for all agents
  - JSON parsing with error recovery
  - Telemetry tracking
  - Error handling
- **Vision Agent**: Extracts team name and jersey number from images
- **Search Agent**: Finds player names using web search

### 4. Repository Layer (`src/repositories/`)
- **PlayerRepository**: Thread-safe access to player database
- Data access abstraction
- Query interface

### 5. Core Layer (`src/core/`)
- **Configuration**: Centralized settings with validation
- **Exceptions**: Custom exception hierarchy
- **Constants**: Global constants and team mappings
- **Logging**: Structured logging configuration

### 6. Utilities Layer (`src/utils/`)
- **Validators**: Input validation functions
- **Team Normalizer**: Team name standardization
- **JSON Parser**: Robust JSON parsing from LLM responses
- **Retry**: Exponential backoff retry logic
- **Circuit Breaker**: Fault tolerance for external services

### 7. Models Layer (`src/models/`)
- **Player**: Data classes for player information
- **Telemetry**: Token usage and performance metrics

### 8. Tools Layer (`src/tools/`)
- **Web Search**: SerpAPI integration
- Extensible for additional tools

## Data Flow

### Player Identification Workflow

```
1. User Input (Image URL)
   ↓
2. Image Service
   - Validate URL
   - Download image
   - Store temporarily
   ↓
3. Vision Agent (Agent 1)
   - Analyze image with AWS Bedrock Claude
   - Extract: team name, jersey number, confidence
   - Return structured JSON
   ↓
4. Search Agent (Agent 2)
   - For each detected player:
     * Search web for player name
     * Use team + jersey number
     * Return player name with confidence
   ↓
5. Filter Layer
   - Keep only high-confidence results
   - Require 2+ high-confidence fields
   - Normalize team names
   ↓
6. Verification Layer
   - Query player repository
   - Match against database
   - Fill in missing names from DB
   ↓
7. Result Display
   - Show verified players
   - Display telemetry (token usage)
   - Cleanup temporary files
```

## Key Design Patterns

### 1. Repository Pattern
- Abstracts data access
- Thread-safe operations
- Easy to swap implementations (JSON → PostgreSQL)

### 2. Service Layer Pattern
- Separates business logic from presentation
- Orchestrates complex workflows
- Testable without UI

### 3. Dependency Injection
- Services receive dependencies via constructor
- Easy mocking for tests
- Flexible configuration

### 4. Circuit Breaker Pattern
- Prevents cascading failures
- Fails fast when external services are down
- Automatic recovery

### 5. Retry with Exponential Backoff
- Handles transient failures
- Configurable retry policies
- Jitter to prevent thundering herd

## Security Architecture

### Secrets Management
- `.env` files for local development
- Environment variables for production
- File permission checks (600)
- Git hooks prevent commits
- Secrets masked in logs

### Input Validation
- URL validation (scheme, domain, extension)
- File size limits
- Sanitization of filenames
- Team name validation
- Jersey number range checks

### Error Handling
- Custom exception hierarchy
- Graceful degradation
- No sensitive data in error messages
- Comprehensive logging

## Configuration Management

### Settings Hierarchy
1. Default values in `Settings` class
2. `.env` file (local development)
3. Environment variables (production)
4. Command-line arguments (if applicable)

### Validation
- Type checking with Pydantic
- Range validation
- Format validation
- Startup validation checks

## Telemetry & Monitoring

### Metrics Collected
- Token usage (input/output) per agent
- Execution duration
- Success/failure rates
- API call counts

### Logging Levels
- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: Confirmation that things are working
- **WARNING**: Indication of potential problems
- **ERROR**: Serious problems that need attention
- **CRITICAL**: System failure

### Structured Logging
- JSON format for production
- Console format for development
- Request ID tracking
- Context propagation

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Individual component testing
- Mocked dependencies
- Fast execution
- High coverage target (80%+)

### Integration Tests (`tests/integration/`)
- Multiple components together
- Real dependencies where possible
- Database interactions
- API integrations

### Test Fixtures
- Sample player data
- Mock responses from agents
- Temporary databases
- Configuration overrides

## Deployment Architecture

### Docker Deployment
```
┌─────────────────────────┐
│     Docker Host         │
│  ┌──────────────────┐  │
│  │  App Container   │  │
│  │  - Streamlit     │  │
│  │  - Python 3.12   │  │
│  │  - uv            │  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │  Redis Cache     │  │
│  │  (Optional)      │  │
│  └──────────────────┘  │
└─────────────────────────┘
```

### Environment-Specific Configs
- **Development**: Debug logging, hot reload
- **Staging**: Production-like, test data
- **Production**: Optimized, monitoring enabled

## Performance Considerations

### Optimization Strategies
1. **Caching**: Cache player database lookups
2. **Connection Pooling**: Reuse HTTP connections
3. **Async Operations**: Parallel processing where possible
4. **Image Size Limits**: Prevent memory issues
5. **Rate Limiting**: Protect external APIs

### Scalability
- Stateless application design
- Horizontal scaling ready
- Database can be moved to PostgreSQL
- Redis for distributed caching

## Future Enhancements

### Phase 2 (Optional)
- RESTful API alongside Streamlit
- Batch processing support
- Real-time video analysis
- Multi-language support
- Advanced caching strategies
- Database migration to PostgreSQL
- Kubernetes deployment
- Advanced monitoring (Prometheus/Grafana)
