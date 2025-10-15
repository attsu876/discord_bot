"""
ドメインリポジトリインターフェース
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Message, Channel, User, Alert


class MessageRepository(ABC):
    """メッセージリポジトリインターフェース"""
    
    @abstractmethod
    async def save_message(self, message: Message) -> None:
        """メッセージを保存"""
        pass
    
    @abstractmethod
    async def get_channel_messages(self, channel_id: str, limit: int = 100) -> List[Message]:
        """チャンネルのメッセージを取得"""
        pass
    
    @abstractmethod
    async def get_recent_messages(self, channel_id: str, hours: int = 24) -> List[Message]:
        """最近のメッセージを取得"""
        pass


class ChannelRepository(ABC):
    """チャンネルリポジトリインターフェース"""
    
    @abstractmethod
    async def get_lesson_channels(self) -> List[Channel]:
        """レッスンチャンネル一覧を取得"""
        pass
    
    @abstractmethod
    async def get_channel(self, channel_id: str) -> Optional[Channel]:
        """チャンネル情報を取得"""
        pass


class UserRepository(ABC):
    """ユーザーリポジトリインターフェース"""
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        """ユーザー情報を取得"""
        pass
    
    @abstractmethod
    async def save_user(self, user: User) -> None:
        """ユーザー情報を保存"""
        pass


class AlertRepository(ABC):
    """アラートリポジトリインターフェース"""
    
    @abstractmethod
    async def save_alert(self, alert: Alert) -> None:
        """アラートを保存"""
        pass
    
    @abstractmethod
    async def get_unresolved_alerts(self) -> List[Alert]:
        """未解決のアラートを取得"""
        pass


class NotificationService(ABC):
    """通知サービスインターフェース"""
    
    @abstractmethod
    async def send_alert(self, alert: Alert) -> None:
        """アラートを送信"""
        pass


class SpreadsheetService(ABC):
    """スプレッドシートサービスインターフェース"""
    
    @abstractmethod
    async def export_channel_logs(self, channel_id: str, messages: List[Message]) -> str:
        """チャンネルログをスプレッドシートに出力"""
        pass