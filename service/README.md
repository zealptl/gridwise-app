# GridWise Service - Backend API

FastAPI backend service for GridWise F1 Fantasy application.

## Technology Stack

- **Python:** 3.11+
- **Package Manager:** `uv` (fast Python package installer)
- **Web Framework:** FastAPI 0.109+
- **ASGI Server:** Uvicorn with standard extras
- **Database:** MongoDB with Motor (async) + Beanie ODM
- **Validation:** Pydantic v2
- **Testing:** pytest + pytest-asyncio + httpx
- **Code Quality:** ruff (linter + formatter), mypy (type checker)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- uv package manager
- MongoDB (for database features)

### Installation

1. Install dependencies:
```bash
cd service/
uv sync
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the development server:
```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs (Swagger UI): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc

## Development Commands

### Run Server
```bash
# Development mode with auto-reload
uv run uvicorn app.main:app --reload

# Custom port
uv run uvicorn app.main:app --reload --port 8001
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_api/test_health.py
```

### Code Quality
```bash
# Lint code
uv run ruff check app/

# Format code
uv run ruff format app/

# Type check
uv run mypy app/
```

### Dependency Management
```bash
# Add a dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update all dependencies
uv sync

# Show installed packages
uv pip list
```

## Project Structure

```
service/
├── app/                    # Application code
│   ├── main.py            # FastAPI app entry point
│   ├── config.py          # Settings management
│   ├── database.py        # DB connection
│   ├── models/            # Beanie documents (DB models)
│   ├── schemas/           # Pydantic schemas (API contracts)
│   ├── routers/           # API route handlers
│   └── services/          # Business logic
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── seed_data/             # Seed data files
└── pyproject.toml         # Project config & dependencies
```

## API Endpoints

### Health & Info
- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

### Version 1 API (Planned)
- `GET /api/v1/drivers` - List all drivers
- `GET /api/v1/constructors` - List all constructors
- `GET /api/v1/teams` - Team management
- `GET /api/v1/rules` - Scoring rules

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `MONGODB_URL` - MongoDB connection string
- `MONGODB_DB_NAME` - Database name
- `API_V1_PREFIX` - API version prefix
- `BACKEND_CORS_ORIGINS` - Allowed CORS origins

## License

Proprietary - GridWise F1 Fantasy
