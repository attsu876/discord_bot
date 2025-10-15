import asyncio

from src.infrastructure.database import DatabaseManager
from config.settings import Settings


async def main():
    db = DatabaseManager(Settings.DATABASE_PATH)
    await db.initialize_database()
    print("DB initialized")


if __name__ == "__main__":
    asyncio.run(main())