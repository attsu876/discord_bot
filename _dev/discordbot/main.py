"""
アプリケーションのエントリポイント
"""
import asyncio
import logging

from config.settings import Settings, LOG_FORMAT

from src.infrastructure.database import (
    DatabaseManager, SQLiteMessageRepository, SQLiteUserRepository, SQLiteAlertRepository
)
from src.infrastructure.discord_client import DiscordClient, DiscordCommands, DiscordChannelRepository
from src.infrastructure.slack_client import SlackNotificationService
from src.infrastructure.spreadsheet import ExcelSpreadsheetService, CSVSpreadsheetService
from src.application.services import LogCollectionService


async def main():
    # ログ設定
    logging.basicConfig(level=getattr(logging, Settings.LOG_LEVEL), format=LOG_FORMAT)
    logger = logging.getLogger("main")
    
    # 設定のバリデーション
    try:
        Settings.validate()
    except ValueError as e:
        logger.warning(f"設定警告: {e}")
        logger.warning(".env ファイルを設定してください。Slack/Discord/OpenAI のキーは後日差し替え可能です。")
    
    # データベース初期化
    db_manager = DatabaseManager(db_path=Settings.DATABASE_PATH)
    await db_manager.initialize_database()
    
    # リポジトリとサービスの初期化
    message_repo = SQLiteMessageRepository(db_path=Settings.DATABASE_PATH)
    user_repo = SQLiteUserRepository(db_path=Settings.DATABASE_PATH)
    alert_repo = SQLiteAlertRepository(db_path=Settings.DATABASE_PATH)
    
    if Settings.SPREADSHEET_FORMAT == 'csv':
        spreadsheet_service = CSVSpreadsheetService(output_dir=Settings.OUTPUT_DIR)
    else:
        spreadsheet_service = ExcelSpreadsheetService(output_dir=Settings.OUTPUT_DIR)
    
    slack_service = SlackNotificationService(
        token=Settings.SLACK_BOT_TOKEN or "",
        channel=Settings.SLACK_NOTIFICATION_CHANNEL
    )
    
    # ログ収集サービスを初期化
    log_service = LogCollectionService(
        message_repo=message_repo,
        channel_repo=DiscordChannelRepository(None),  # 後でDiscordClientでセット
        user_repo=user_repo,
        alert_repo=alert_repo,
        notification_service=slack_service,
        spreadsheet_service=spreadsheet_service
    )
    
    # Discordクライアントの初期化
    discord_client = DiscordClient(log_collection_service=log_service)
    
    # DiscordCommands を登録
    discord_client.add_cog(DiscordCommands(discord_client, log_service))
    
    # DiscordChannelRepository にクライアントをセット
    log_service.channel_repo.client = discord_client
    
    # Slack接続テスト（任意）
    await slack_service.test_connection()
    
    # Discordに接続
    if Settings.DISCORD_BOT_TOKEN:
        await discord_client.start(Settings.DISCORD_BOT_TOKEN)
    else:
        logger.error("DISCORD_BOT_TOKEN が未設定のため、Discord接続をスキップします。")


if __name__ == "__main__":
    asyncio.run(main())