"""
ドメインモデル: メッセージエンティティ
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum


class UserRole(Enum):
    """ユーザーロール"""
    ADMIN = "admin"
    SUPPORT = "support"
    MENTOR = "mentor"
    AI_ASSISTANT = "ai_assistant"
    STUDENT = "student"
    PARENT = "parent"


@dataclass
class User:
    """ユーザーエンティティ"""
    id: str
    username: str
    display_name: str
    roles: List[UserRole]
    
    def is_staff(self) -> bool:
        """運営側かどうかを判定"""
        staff_roles = {UserRole.ADMIN, UserRole.SUPPORT, UserRole.MENTOR, UserRole.AI_ASSISTANT}
        return any(role in staff_roles for role in self.roles)
    
    def is_student_side(self) -> bool:
        """生徒側かどうかを判定"""
        return not self.is_staff()


@dataclass
class Message:
    """メッセージエンティティ"""
    id: str
    channel_id: str
    channel_name: str
    user: User
    content: str
    timestamp: datetime
    reactions: List[str]
    is_question: bool = False
    thread_id: Optional[str] = None
    
    def contains_question_mark(self) -> bool:
        """質問マークを含むかどうか"""
        return "？" in self.content or "?" in self.content


@dataclass
class Channel:
    """チャンネルエンティティ"""
    id: str
    name: str
    is_lesson_channel: bool
    last_message: Optional[Message] = None
    
    def needs_staff_response(self) -> bool:
        """スタッフの返信が必要かどうか"""
        if not self.last_message:
            return False
        
        # 最後のメッセージが生徒側からの質問の場合
        return (self.last_message.user.is_student_side() and 
                self.last_message.contains_question_mark())


@dataclass
class Alert:
    """アラートエンティティ"""
    channel: Channel
    message: Message
    alert_type: str
    description: str
    created_at: datetime