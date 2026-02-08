# Phase 0: Backend Project Setup

## Overview
Set up the Python backend project structure with modern tooling using `uv` package manager, FastAPI framework, and development tools.

**Epic:** Foundation
**Estimated Effort:** 2-3 hours

---

## Objectives

1. ✅ Initialize Python project with `uv` package manager
2. ✅ Set up `pyproject.toml` for dependency management
3. ✅ Configure project structure (directories, modules)
4. ✅ Set up development tools (linting, formatting, type checking)
5. ✅ Create environment configuration (.env)
6. ✅ Set up testing framework (pytest)
7. ✅ Create initial FastAPI application skeleton
8. ✅ Verify setup works

---

## Technology Stack

- **Python:** 3.11+
- **Package Manager:** `uv` (fast Python package installer)
- **Web Framework:** FastAPI 0.109+
- **ASGI Server:** Uvicorn with standard extras
- **Database:** MongoDB with Motor (async) + Beanie ODM
- **Validation:** Pydantic v2
- **Testing:** pytest + pytest-asyncio + httpx
- **Code Quality:** ruff (linter + formatter), mypy (type checker)

---

## Project Structure

```
gridwise-app/
├── service/                          # Backend root
│   ├── pyproject.toml               # Project config & dependencies
│   ├── .python-version              # Python version (3.11)
│   ├── .env.example                 # Environment template
│   ├── .env                         # Local environment (gitignored)
│   ├── .gitignore                   # Git ignore rules
│   ├── README.md                    # Backend documentation
│   │
│   ├── app/                         # Application code
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Settings management
│   │   ├── database.py              # DB connection
│   │   │
│   │   ├── models/                  # Beanie documents (DB models)
│   │   │   ├── __init__.py
│   │   │   ├── driver.py
│   │   │   ├── constructor.py
│   │   │   ├── rule.py
│   │   │   ├── team.py
│   │   │   └── user.py
│   │   │
│   │   ├── schemas/                 # Pydantic schemas (API contracts)
│   │   │   ├── __init__.py
│   │   │   ├── driver.py
│   │   │   ├── constructor.py
│   │   │   ├── rule.py
│   │   │   └── team.py
│   │   │
│   │   ├── routers/                 # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── drivers.py
│   │   │   ├── constructors.py
│   │   │   ├── rules.py
│   │   │   └── teams.py
│   │   │
│   │   └── services/                # Business logic
│   │       ├── __init__.py
│   │       ├── team_service.py
│   │       ├── rule_engine.py
│   │       └── rules/               # Rule implementations
│   │           ├── __init__.py
│   │           └── abstract_rule.py
│   │
│   ├── tests/                       # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py              # Pytest fixtures
│   │   ├── test_api/                # API integration tests
│   │   ├── test_services/           # Service unit tests
│   │   └── test_rules/              # Rule engine tests
│   │
│   ├── scripts/                     # Utility scripts
│   │   ├── seed_database.py
│   │   └── reset_database.py
│   │
│   └── seed_data/                   # Seed data files
│       ├── drivers_2026.json
│       ├── constructors_2026.json
│       └── rules_initial.json
```

---

## pyproject.toml Configuration

### Basic Structure

```toml
[project]
name = "gridwise-service"
version = "0.1.0"
description = "GridWise F1 Fantasy API Service"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    # Core dependencies listed here
]

[project.optional-dependencies]
dev = [
    # Development dependencies
]

[tool.uv]
# UV-specific configuration

[tool.ruff]
# Ruff linter/formatter configuration

[tool.mypy]
# MyPy type checker configuration

[tool.pytest.ini_options]
# Pytest configuration
```

### Core Dependencies

```toml
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "motor>=3.3.2",
    "beanie>=1.24.0",
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
]
```

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.0",           # For async test client
    "ruff>=0.1.0",             # Linter + formatter
    "mypy>=1.7.0",             # Type checker
    "pre-commit>=3.5.0",       # Git hooks
]
```

### Tool Configuration

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
]
ignore = []
exclude = [
    ".git",
    ".venv",
    "__pycache__",
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --cov=app --cov-report=term-missing"
```

---

## Setup Steps

### Step 1: Install uv Package Manager

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv

# Verify installation
uv --version
```

### Step 2: Initialize Project

```bash
cd service/

# Create pyproject.toml with basic structure
# (Can be done manually or via uv init)

# Set Python version
echo "3.11" > .python-version
```

### Step 3: Install Dependencies

```bash
# Sync all dependencies (creates virtual env automatically)
uv sync

# Or install specific groups
uv sync --group dev

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

### Step 4: Create Directory Structure

```bash
# Create app directories
mkdir -p app/{models,schemas,routers,services/rules}

# Create test directories
mkdir -p tests/{test_api,test_services,test_rules}

# Create utility directories
mkdir -p scripts seed_data

# Create __init__.py files
touch app/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/routers/__init__.py
touch app/services/__init__.py
touch app/services/rules/__init__.py
touch tests/__init__.py
```

### Step 5: Create Environment Files

```bash
# Create .env.example
cat > .env.example << 'EOF'
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=gridwise_mvp

# API
API_V1_PREFIX=/api/v1
PROJECT_NAME=GridWise API
VERSION=0.1.0

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
EOF

# Copy to .env for local development
cp .env.example .env
```

### Step 6: Create Minimal FastAPI App

Pseudocode for `app/main.py`:

```python
# Import FastAPI, CORS middleware, lifecycle events
# Import database connection functions
# Import settings from config

# Create FastAPI app instance with metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Startup event handler
@app.on_event("startup")
async def startup():
    # Connect to MongoDB
    await connect_to_mongo()

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown():
    # Close MongoDB connection
    await close_mongo_connection()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "GridWise API",
        "version": settings.VERSION,
        "docs": "/docs"
    }
```

### Step 7: Create Config Module

Pseudocode for `app/config.py`:

```python
# Import BaseSettings from pydantic-settings
# Import Optional, List types

class Settings(BaseSettings):
    # MongoDB settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "gridwise_mvp"

    # API settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "GridWise API"
    VERSION: str = "0.1.0"

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [...]

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create singleton instance
settings = Settings()
```

### Step 8: Create Database Module Skeleton

Pseudocode for `app/database.py`:

```python
# Import AsyncIOMotorClient from motor
# Import init_beanie from beanie
# Import settings from config

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def connect_to_mongo():
    # Create MongoDB client
    # Initialize Beanie with document models
    # Print connection success

async def close_mongo_connection():
    # Close MongoDB client
    # Print disconnection message

async def get_database():
    # Return database instance
    return db.client[settings.MONGODB_DB_NAME]
```

### Step 9: Create Pytest Configuration

Create `tests/conftest.py`:

```python
# Pytest fixtures for testing
# - Database setup/teardown
# - Test client
# - Sample data fixtures
```

### Step 10: Create .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# MyPy
.mypy_cache/

# Ruff
.ruff_cache/

# macOS
.DS_Store
EOF
```

---

## Verification Steps

### 1. Verify UV Installation
```bash
uv --version
# Should show uv version
```

### 2. Verify Dependencies Installed
```bash
uv pip list
# Should show fastapi, uvicorn, motor, beanie, pydantic, etc.
```

### 3. Verify App Runs
```bash
uv run uvicorn app.main:app --reload
# Should start server at http://127.0.0.1:8000
# Visit http://127.0.0.1:8000/docs for Swagger UI
```

### 4. Test Health Endpoint
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", "version": "0.1.0"}
```

### 5. Verify Linting Works
```bash
uv run ruff check app/
# Should run without errors on skeleton code
```

### 6. Verify Type Checking Works
```bash
uv run mypy app/
# Should run without errors on skeleton code
```

### 7. Verify Tests Run
```bash
uv run pytest
# Should discover and run tests (even if none exist yet)
```

---

## UV Package Manager Commands Reference

### Dependency Management
```bash
# Add a dependency
uv add fastapi

# Add a dev dependency
uv add --dev pytest

# Remove a dependency
uv remove package-name

# Update all dependencies
uv sync

# Update specific package
uv add --upgrade fastapi
```

### Running Commands
```bash
# Run a command in the virtual environment
uv run python script.py
uv run pytest
uv run uvicorn app.main:app --reload

# Or activate venv and run directly
source .venv/bin/activate
python script.py
```

### Environment Management
```bash
# Create virtual environment
uv venv

# Sync dependencies (creates venv if needed)
uv sync

# Show installed packages
uv pip list

# Show outdated packages
uv pip list --outdated
```

---

## Development Workflow Setup

### Pre-commit Hooks (Optional but Recommended)

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

Install hooks:
```bash
uv run pre-commit install
```

---

## Verification Checklist

- [ ] `uv` package manager installed
- [ ] Python 3.11+ available
- [ ] Project structure created
- [ ] `pyproject.toml` configured
- [ ] Dependencies installed via `uv sync`
- [ ] `.env` file created from `.env.example`
- [ ] FastAPI app skeleton created
- [ ] Config module created
- [ ] Database module skeleton created
- [ ] `.gitignore` configured
- [ ] Server starts successfully
- [ ] `/health` endpoint responds
- [ ] `/docs` Swagger UI accessible
- [ ] `ruff` linter runs without errors
- [ ] `mypy` type checker runs
- [ ] `pytest` test discovery works

---

## Common Issues & Solutions

### Issue: uv command not found
**Solution:** Ensure uv is in PATH or use full path to uv binary

### Issue: MongoDB connection fails on startup
**Solution:** This is expected before MongoDB is installed. The app will start but database operations will fail. Install MongoDB in Phase 1.

### Issue: Import errors
**Solution:** Ensure virtual environment is activated or use `uv run` prefix

### Issue: Port 8000 already in use
**Solution:** Use different port: `uvicorn app.main:app --port 8001`

---

## Next Steps

After Phase 0 is complete:
1. Proceed to Phase 1.1: Database Setup & Seed Data
2. Install and configure MongoDB
3. Create database models
4. Implement seed data script
