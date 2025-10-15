import asyncio

from config.settings import Settings
from src.infrastructure.openai_client import OpenAIAnalyzer


async def main():
    analyzer = OpenAIAnalyzer(Settings.OPENAI_API_KEY or "")
    ok = await analyzer.test_connection()
    print("OpenAI OK" if ok else "OpenAI NG")


if __name__ == "__main__":
    asyncio.run(main())