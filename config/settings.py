"""
設定ファイル
"""
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


class Settings:
    """アプリケーション設定"""
    
    # Discord設定
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    # Slack設定
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
    SLACK_NOTIFICATION_CHANNEL = os.getenv('SLACK_NOTIFICATION_CHANNEL', '#lesson-alerts')
    
    # OpenAI設定
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # データベース設定
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///lesson_logs.db')
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'lesson_logs.db')
    
    # ログ設定
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # デバッグモード
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # アラート設定
    UNANSWERED_QUESTION_ALERT_HOURS = int(os.getenv('UNANSWERED_QUESTION_ALERT_HOURS', '2'))
    
    # 出力設定
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    
    # スプレッドシート形式
    SPREADSHEET_FORMAT = os.getenv('SPREADSHEET_FORMAT', 'xlsx')  # xlsx or csv
    
    @classmethod
    def validate(cls):
        """設定値をバリデーション"""
        required_settings = [
            'DISCORD_BOT_TOKEN',
            'SLACK_BOT_TOKEN',
            'OPENAI_API_KEY'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not getattr(cls, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ValueError(f"必要な環境変数が設定されていません: {', '.join(missing_settings)}")
        
        return True


# レッスンチャンネル検出ルール
LESSON_CHANNEL_KEYWORDS = [
    "lesson", "レッスン", "授業", "class", "講義"
]

# スタッフロール名のパターン
STAFF_ROLE_PATTERNS = [
    "admin", "administrator", "support", "mentor", 
    "teacher", "instructor", "ai", "bot", "assistant"
]

# ログ出力フォーマット
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'