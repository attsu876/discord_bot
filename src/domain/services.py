"""
ドメインサービス: メッセージ分析ロジック
"""
from typing import List
from datetime import datetime, timedelta
from .entities import Message, Channel, Alert, User


class MessageAnalyzer:
    """メッセージ分析サービス"""
    
    @staticmethod
    def detect_unanswered_questions(channel: Channel, messages: List[Message]) -> List[Alert]:
        """未回答の質問を検出"""
        alerts = []
        
        if not messages:
            return alerts
        
        # 最後のメッセージが生徒側からの質問で、その後返信がない場合
        last_message = messages[-1]
        if (last_message.user.is_student_side() and 
            last_message.contains_question_mark() and
            MessageAnalyzer._is_old_enough_for_alert(last_message)):
            
            alert = Alert(
                channel=channel,
                message=last_message,
                alert_type="unanswered_question",
                description=f"生徒からの質問に {MessageAnalyzer._hours_since(last_message)} 時間返信がありません",
                created_at=datetime.now()
            )
            alerts.append(alert)
        
        return alerts
    
    @staticmethod
    def detect_off_topic_conversations(messages: List[Message]) -> List[Alert]:
        """振り返り以外の話題を検出（GPT-4.1で分析）"""
        # この部分は後でOpenAI APIを使って実装
        return []
    
    @staticmethod
    def _is_old_enough_for_alert(message: Message) -> bool:
        """アラートを出すのに十分古いメッセージかどうか"""
        # 2時間以上経過していればアラート対象
        return datetime.now() - message.timestamp > timedelta(hours=2)
    
    @staticmethod
    def _hours_since(message: Message) -> int:
        """メッセージから何時間経過したか"""
        return int((datetime.now() - message.timestamp).total_seconds() / 3600)


class UserRoleClassifier:
    """ユーザーロール分類サービス"""
    
    STAFF_ROLE_NAMES = {
        "admin", "administrator", "support", "mentor", "teacher", 
        "instructor", "ai", "bot", "assistant"
    }
    
    @classmethod
    def classify_user_roles(cls, discord_roles: List[str]) -> List[str]:
        """Discordのロール名からユーザータイプを分類"""
        user_roles = []
        
        for role_name in discord_roles:
            role_lower = role_name.lower()
            
            if any(staff_role in role_lower for staff_role in cls.STAFF_ROLE_NAMES):
                if "admin" in role_lower:
                    user_roles.append("admin")
                elif "support" in role_lower:
                    user_roles.append("support")
                elif "mentor" in role_lower or "teacher" in role_lower:
                    user_roles.append("mentor")
                elif "ai" in role_lower or "bot" in role_lower:
                    user_roles.append("ai_assistant")
            else:
                # デフォルトは生徒
                if "parent" in role_lower:
                    user_roles.append("parent")
                else:
                    user_roles.append("student")
        
        return user_roles if user_roles else ["student"]