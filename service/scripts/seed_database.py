"""Database Seeding Script

This script seeds the MongoDB database with initial data for the 2026 F1 season.
"""

import asyncio
import json
from pathlib import Path

from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo
from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.rule import Rule
from app.models.user import User


async def seed_database():
    """Seed database with initial data"""
    print("=" * 60)
    print("GridWise Database Seeding")
    print("=" * 60)

    # Connect to database
    print("\n1. Connecting to MongoDB...")
    await connect_to_mongo()

    # Load seed data directory
    seed_dir = Path(__file__).parent.parent / "seed_data"
    print(f"   Seed data directory: {seed_dir}")

    # Seed drivers
    print("\n2. Seeding drivers...")
    with open(seed_dir / "drivers_2026.json") as f:
        drivers_data = json.load(f)

    print(f"   Loading {len(drivers_data)} drivers...")
    for driver_data in drivers_data:
        driver = Driver(**driver_data)
        await driver.insert()
        print(f"   ✓ {driver.first_name} {driver.last_name} ({driver.team_name}) - {driver.price}M")

    # Seed constructors
    print("\n3. Seeding constructors...")
    with open(seed_dir / "constructors_2026.json") as f:
        constructors_data = json.load(f)

    print(f"   Loading {len(constructors_data)} constructors...")
    for constructor_data in constructors_data:
        constructor = Constructor(**constructor_data)
        await constructor.insert()
        print(f"   ✓ {constructor.name} ({constructor.full_name}) - {constructor.price}M")

    # Seed rules
    print("\n4. Seeding rules...")
    with open(seed_dir / "rules_initial.json") as f:
        rules_data = json.load(f)

    print(f"   Loading {len(rules_data)} rules...")
    for rule_data in rules_data:
        rule = Rule(**rule_data)
        await rule.insert()
        print(f"   ✓ {rule.name} (Type: {rule.rule_type})")

    # Create default admin user
    print("\n5. Creating default admin user...")
    admin_user = User(
        username="admin",
        email="admin@gridwise.local",
        is_active=True,
        is_admin=True,
    )
    await admin_user.insert()
    print(f"   ✓ Created user: {admin_user.username} ({admin_user.email})")

    # Close connection
    print("\n6. Closing connection...")
    await close_mongo_connection()

    # Summary
    print("\n" + "=" * 60)
    print("Database seeding complete!")
    print("=" * 60)
    print(f"✓ Drivers seeded: {len(drivers_data)}")
    print(f"✓ Constructors seeded: {len(constructors_data)}")
    print(f"✓ Rules seeded: {len(rules_data)}")
    print(f"✓ Users created: 1")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
