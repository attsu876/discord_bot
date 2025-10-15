import asyncio

from config.settings import Settings
from src.infrastructure.discord_client import DiscordClient, DiscordCommands
from src.infrastructure.database import (
    DatabaseManager, SQLiteMessageRepository, SQLiteUserRepository, SQLiteAlertRepository
)
from src.infrastructure.slack_client import SlackNotificationService
from src.infrastructure.spreadsheet import ExcelSpreadsheetService
from src.application.services import LogCollectionService


async def main():
    # DB init
    db_manager = DatabaseManager(Settings.DATABASE_PATH)
    await db_manager.initialize_database()

    # services
    message_repo = SQLiteMessageRepository(Settings.DATABASE_PATH)
    user_repo = SQLiteUserRepository(Settings.DATABASE_PATH)
    alert_repo = SQLiteAlertRepository(Settings.DATABASE_PATH)
    spreadsheet_service = ExcelSpreadsheetService()
    slack_service = SlackNotificationService(Settings.SLACK_BOT_TOKEN or "", Settings.SLACK_NOTIFICATION_CHANNEL)

    log_service = LogCollectionService(
        message_repo=message_repo,
        channel_repo=None,  # set later
        user_repo=user_repo,
        alert_repo=alert_repo,
        notification_service=slack_service,
        spreadsheet_service=spreadsheet_service
    )

    bot = DiscordClient(log_collection_service=log_service)
    bot.add_cog(DiscordCommands(bot, log_service))

    # inject channel repo after bot created
    from src.infrastructure.discord_client import DiscordChannelRepository
    log_service.channel_repo = DiscordChannelRepository(bot)

    await bot.start(Settings.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())