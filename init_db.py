import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db import setup_database

async def main():
    print("Setting up database...")
    await setup_database()
    print("Database setup completed!")

if __name__ == "__main__":
    asyncio.run(main())
