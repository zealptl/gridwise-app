"""Quick Database Explorer

Run this script to explore the GridWise database.
"""

import asyncio

from app.database import close_mongo_connection, connect_to_mongo
from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.rule import Rule
from app.models.user import User


async def explore_database():
    """Explore database contents"""
    print("=" * 70)
    print("GridWise Database Explorer")
    print("=" * 70)

    # Connect
    await connect_to_mongo()

    # Drivers
    print("\n📊 DRIVERS (20 total)")
    print("-" * 70)
    drivers = await Driver.find_all().to_list()

    # Group by team
    teams = {}
    for driver in drivers:
        if driver.team_name not in teams:
            teams[driver.team_name] = []
        teams[driver.team_name].append(driver)

    for team_name, team_drivers in sorted(teams.items()):
        print(f"\n{team_name}:")
        for driver in sorted(team_drivers, key=lambda d: d.price, reverse=True):
            print(f"  • {driver.first_name} {driver.last_name} (#{driver.driver_number}) - {driver.price}M")

    # Constructors
    print("\n\n🏎️  CONSTRUCTORS (10 total)")
    print("-" * 70)
    constructors = await Constructor.find_all().sort("-price").to_list()
    for constructor in constructors:
        print(f"{constructor.name:20} {constructor.full_name:50} {constructor.price}M")

    # Rules
    print("\n\n📋 RULES (7 total)")
    print("-" * 70)
    rules = await Rule.find_all().to_list()
    for rule in rules:
        status = "✅" if rule.is_active else "❌"
        print(f"{status} {rule.name}")
        print(f"   Type: {rule.rule_type.value}")
        print(f"   Severity: {rule.severity.value}")
        print(f"   Description: {rule.description}")
        print(f"   Config: {rule.config}")
        print()

    # Users
    print("\n👤 USERS")
    print("-" * 70)
    users = await User.find_all().to_list()
    for user in users:
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Admin: {user.is_admin}")
        print(f"Active: {user.is_active}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  • Total Drivers: {len(drivers)}")
    print(f"  • Total Constructors: {len(constructors)}")
    print(f"  • Total Rules: {len(rules)}")
    print(f"  • Total Users: {len(users)}")
    print(f"  • Price Range (Drivers): {min(d.price for d in drivers)}M - {max(d.price for d in drivers)}M")
    print(f"  • Price Range (Constructors): {min(c.price for c in constructors)}M - {max(c.price for c in constructors)}M")
    print("=" * 70)

    # Close
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(explore_database())
