"""
アプリケーションサービス: メッセージログ収集ユースケース
"""
from typing import List
from datetime import datetime
from ..domain.entities import Message, Channel, Alert, User, UserRole
from ..domain.services import MessageAnalyzer, UserRoleClassifier
from ..domain.repositories import (
    MessageRepository, ChannelRepository, UserRepository, 
    AlertRepository, NotificationService, SpreadsheetService
)


class LogCollectionService:
    """ログ収集サービス"""
    
    def __init__(
        self,
        message_repo: MessageRepository,
        channel_repo: ChannelRepository,
        user_repo: UserRepository,
        alert_repo: AlertRepository,
        notification_service: NotificationService,
        spreadsheet_service: SpreadsheetService
    ):
        self.message_repo = message_repo
        self.channel_repo = channel_repo
        self.user_repo = user_repo
        self.alert_repo = alert_repo
        self.notification_service = notification_service
        self.spreadsheet_service = spreadsheet_service
    
    async def collect_and_analyze_messages(self) -> None:
        """メッセージを収集・分析してアラートを生成"""
        # 1. レッスンチャンネル一覧を取得
        channels = await self.channel_repo.get_lesson_channels()
        
        for channel in channels:
            # 2. 各チャンネルの最近のメッセージを取得
            messages = await self.message_repo.get_recent_messages(channel.id, hours=24)
            
            if not messages:
                continue
            
            # 3. メッセージを分析してアラートを生成
            alerts = MessageAnalyzer.detect_unanswered_questions(channel, messages)
            
            # 4. アラートを保存・通知
            for alert in alerts:
                await self.alert_repo.save_alert(alert)
                await self.notification_service.send_alert(alert)
    
    async def process_new_message(self, discord_message_data: dict) -> None:
        """新しいメッセージを処理"""
        # 1. ユーザー情報を取得・分類
        user = await self._get_or_create_user(discord_message_data['author'])
        
        # 2. メッセージエンティティを作成
        message = Message(
            id=discord_message_data['id'],
            channel_id=discord_message_data['channel_id'],
            channel_name=discord_message_data.get('channel_name', ''),
            user=user,
            content=discord_message_data['content'],
            timestamp=datetime.fromisoformat(discord_message_data['timestamp']),
            reactions=discord_message_data.get('reactions', []),
            is_question=discord_message_data['content'].endswith('？') or discord_message_data['content'].endswith('?')
        )
        
        # 3. メッセージを保存
        await self.message_repo.save_message(message)
        
        # 4. 必要に応じて即座にアラート分析
        channel = await self.channel_repo.get_channel(message.channel_id)
        if channel and channel.is_lesson_channel:
            recent_messages = await self.message_repo.get_recent_messages(channel.id, hours=6)
            alerts = MessageAnalyzer.detect_unanswered_questions(channel, recent_messages)
            
            for alert in alerts:
                await self.alert_repo.save_alert(alert)
                await self.notification_service.send_alert(alert)
    
    async def export_channel_logs(self, channel_id: str) -> str:
        """チャンネルログをスプレッドシートにエクスポート"""
        messages = await self.message_repo.get_channel_messages(channel_id, limit=1000)
        return await self.spreadsheet_service.export_channel_logs(channel_id, messages)
    
    async def _get_or_create_user(self, author_data: dict) -> User:
        """ユーザーを取得または作成"""
        user_id = author_data['id']
        existing_user = await self.user_repo.get_user(user_id)
        
        if existing_user:
            return existing_user
        
        # 新しいユーザーを作成
        role_names = author_data.get('roles', [])
        classified_roles = UserRoleClassifier.classify_user_roles(role_names)
        
        user_roles = []
        for role_name in classified_roles:
            try:
                user_roles.append(UserRole(role_name))
            except ValueError:
                user_roles.append(UserRole.STUDENT)  # デフォルト
        
        user = User(
            id=user_id,
            username=author_data['username'],
            display_name=author_data.get('display_name', author_data['username']),
            roles=user_roles
        )
        
        await self.user_repo.save_user(user)
        return user