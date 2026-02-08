# Phase 1.1: Database Setup & Seed Data

## Overview
Set up MongoDB connection, create database schemas, and populate with 2026 F1 season seed data.

**User Story:** N/A (Infrastructure)
**Epic:** Foundation
**Estimated Effort:** 4-6 hours

---

## Objectives

1. ✅ Configure MongoDB connection with Motor (async driver)
2. ✅ Define all database schemas using Beanie ODM
3. ✅ Create seed data for 2026 F1 season (20 drivers, 10 constructors)
4. ✅ Write database seeding script
5. ✅ Add database connection lifecycle management

---

## Database Schema Definitions

### Collections to Create

1. **drivers** - F1 drivers with pricing
2. **constructors** - F1 teams with pricing
3. **rules** - Game rules configuration
4. **teams** - User fantasy teams
5. **users** - User accounts (basic, for MVP single user)

---

## Files to Create/Modify

### 1. `service/app/config.py`
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "gridwise_mvp"

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "GridWise API"
    VERSION: str = "0.1.0"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 2. `service/app/database.py`
```python
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.driver import Driver
from app.models.constructor import Constructor
from app.models.rule import Rule
from app.models.team import FantasyTeam
from app.models.user import User

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB and initialize Beanie"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=db.client[settings.MONGODB_DB_NAME],
        document_models=[
            Driver,
            Constructor,
            Rule,
            FantasyTeam,
            User
        ]
    )
    print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")

async def close_mongo_connection():
    """Close MongoDB connection"""
    db.client.close()
    print("Closed MongoDB connection")

async def get_database():
    """Get database instance"""
    return db.client[settings.MONGODB_DB_NAME]
```

### 3. `service/app/models/driver.py`
```python
from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime
from uuid import uuid4

class Driver(Document):
    driver_id: str = Field(default_factory=lambda: str(uuid4()))
    first_name: str
    last_name: str
    team_name: str  # Constructor they drive for
    nationality: str
    driver_number: int
    price: float  # In millions (M)
    status: str = "active"  # active, inactive, reserve

    # Price history for tracking
    price_history: list[dict] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "drivers"
        indexes = [
            "driver_id",
            "team_name",
            "status"
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "drv-123",
                "first_name": "Max",
                "last_name": "Verstappen",
                "team_name": "Red Bull Racing",
                "nationality": "Dutch",
                "driver_number": 1,
                "price": 30.5,
                "status": "active"
            }
        }
```

### 4. `service/app/models/constructor.py`
```python
from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime
from uuid import uuid4

class Constructor(Document):
    constructor_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    full_name: str
    nationality: str
    price: float  # In millions (M)
    status: str = "active"  # active, inactive

    # Price history
    price_history: list[dict] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "constructors"
        indexes = [
            "constructor_id",
            "status"
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "constructor_id": "con-123",
                "name": "Red Bull",
                "full_name": "Oracle Red Bull Racing",
                "nationality": "Austrian",
                "price": 28.0,
                "status": "active"
            }
        }
```

### 5. `service/app/models/user.py`
```python
from beanie import Document
from pydantic import Field
from datetime import datetime
from uuid import uuid4

class User(Document):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    email: str

    # For MVP - single user mode, no password needed
    is_active: bool = True
    is_admin: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            "user_id",
            "username",
            "email"
        ]
```

### 6. `service/seed_data/drivers_2026.json`
Create seed data for 20 drivers across 10 teams.

### 7. `service/seed_data/constructors_2026.json`
Create seed data for 10 constructors.

### 8. `service/seed_data/rules_initial.json`
Create all 7 F1 Fantasy rules as defined in the plan.

### 9. `service/scripts/seed_database.py`
```python
import asyncio
import json
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.models.driver import Driver
from app.models.constructor import Constructor
from app.models.rule import Rule
from app.models.user import User

async def seed_database():
    """Seed database with initial data"""

    # Connect to database
    await connect_to_mongo()

    # Load seed data
    seed_dir = Path(__file__).parent.parent / "seed_data"

    # Seed drivers
    with open(seed_dir / "drivers_2026.json") as f:
        drivers_data = json.load(f)

    print(f"Seeding {len(drivers_data)} drivers...")
    for driver_data in drivers_data:
        driver = Driver(**driver_data)
        await driver.insert()

    # Seed constructors
    with open(seed_dir / "constructors_2026.json") as f:
        constructors_data = json.load(f)

    print(f"Seeding {len(constructors_data)} constructors...")
    for constructor_data in constructors_data:
        constructor = Constructor(**constructor_data)
        await constructor.insert()

    # Seed rules
    with open(seed_dir / "rules_initial.json") as f:
        rules_data = json.load(f)

    print(f"Seeding {len(rules_data)} rules...")
    for rule_data in rules_data:
        rule = Rule(**rule_data)
        await rule.insert()

    # Create default admin user
    admin_user = User(
        username="admin",
        email="admin@gridwise.local",
        is_active=True,
        is_admin=True
    )
    await admin_user.insert()
    print("Created admin user")

    # Close connection
    await close_mongo_connection()
    print("Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_database())
```

### 10. `service/requirements.txt`
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
motor==3.3.2
beanie==1.24.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

### 11. `service/.env.example`
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=gridwise_mvp
API_V1_PREFIX=/api/v1
PROJECT_NAME=GridWise API
VERSION=0.1.0
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

---

## Seed Data Specifications

### Drivers (20 total)
- **Red Bull Racing:** Max Verstappen (30.5M), Sergio Perez (26.0M)
- **Ferrari:** Charles Leclerc (29.0M), Carlos Sainz (25.5M)
- **Mercedes:** Lewis Hamilton (28.5M), George Russell (24.0M)
- **McLaren:** Lando Norris (27.0M), Oscar Piastri (22.5M)
- **Aston Martin:** Fernando Alonso (24.5M), Lance Stroll (18.0M)
- **Alpine:** Pierre Gasly (21.0M), Esteban Ocon (19.5M)
- **Williams:** Alex Albon (20.0M), Logan Sargeant (15.0M)
- **RB:** Yuki Tsunoda (18.5M), Daniel Ricciardo (17.5M)
- **Kick Sauber:** Valtteri Bottas (17.0M), Zhou Guanyu (15.5M)
- **Haas:** Nico Hulkenberg (19.0M), Kevin Magnussen (16.0M)

### Constructors (10 total)
- Red Bull Racing (28.0M)
- Ferrari (26.5M)
- Mercedes (25.0M)
- McLaren (23.5M)
- Aston Martin (21.0M)
- Alpine (18.5M)
- Williams (16.0M)
- RB (15.5M)
- Kick Sauber (14.0M)
- Haas (15.0M)

### Rules (7 total)
All rules as defined in the main plan with proper JSON structure.

---

## Implementation Steps

### Step 1: Install Dependencies
```bash
cd service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Start MongoDB
```bash
# Using Docker
docker run -d -p 27017:27017 --name gridwise-mongo mongo:latest

# OR using local MongoDB
brew services start mongodb-community  # macOS
```

### Step 3: Create Environment File
```bash
cp .env.example .env
# Edit .env if needed
```

### Step 4: Create All Model Files
Create all Beanie document models as specified above.

### Step 5: Create Seed Data Files
Create JSON files with all drivers, constructors, and rules.

### Step 6: Run Database Seeding
```bash
python scripts/seed_database.py
```

### Step 7: Verify Data
```bash
# Connect to MongoDB and verify
mongosh
use gridwise_mvp
db.drivers.countDocuments()  # Should return 20
db.constructors.countDocuments()  # Should return 10
db.rules.countDocuments()  # Should return 7
db.users.countDocuments()  # Should return 1
```

---

## Verification Checklist

- [ ] MongoDB connection works
- [ ] All 5 collections created
- [ ] 20 drivers seeded successfully
- [ ] 10 constructors seeded successfully
- [ ] 7 rules seeded successfully
- [ ] 1 admin user created
- [ ] All indexes created properly
- [ ] Can query data via MongoDB shell
- [ ] No duplicate driver_id or constructor_id values
- [ ] All prices are realistic (drivers: 15-31M, constructors: 14-28M)

---

## Next Steps

After database setup is complete:
1. Proceed to Phase 1.2: Rule Management (Backend)
2. Build the rule engine and validation logic
3. Create CRUD APIs for rules
