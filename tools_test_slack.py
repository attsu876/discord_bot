import asyncio
import os
import tempfile

from config.settings import Settings
from src.infrastructure.slack_client import SlackNotificationService


async def main():
    # Slack接続テスト
    slack = SlackNotificationService(Settings.SLACK_BOT_TOKEN or "", Settings.SLACK_NOTIFICATION_CHANNEL)
    ok = await slack.test_connection()
    print("Slack OK" if ok else "Slack NG")


if __name__ == "__main__":
    asyncio.run(main())