"""
データベース実装（SQLite）
"""
import sqlite3
import aiosqlite
from typing import List, Optional
from datetime import datetime
import json
import logging

from ..domain.entities import Message, User, Alert, Channel, UserRole
from ..domain.repositories import MessageRepository, UserRepository, AlertRepository


class DatabaseManager:
    """データベースマネージャー"""
    
    def __init__(self, db_path: str = "lesson_logs.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    async def initialize_database(self):
        """データベースを初期化"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    roles TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    reactions TEXT,
                    is_question BOOLEAN DEFAULT FALSE,
                    thread_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (message_id) REFERENCES messages (id)
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_channel_timestamp 
                ON messages (channel_id, timestamp)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_created_at 
                ON alerts (created_at)
            """)
            
            await db.commit()
            self.logger.info("データベース初期化完了")


class SQLiteMessageRepository(MessageRepository):
    """SQLite メッセージリポジトリ実装"""
    
    def __init__(self, db_path: str = "lesson_logs.db"):
        self.db_path = db_path
    
    async def save_message(self, message: Message) -> None:
        """メッセージを保存"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO messages 
                (id, channel_id, channel_name, user_id, content, timestamp, reactions, is_question, thread_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.id,
                message.channel_id,
                message.channel_name,
                message.user.id,
                message.content,
                message.timestamp,
                json.dumps(message.reactions),
                message.is_question,
                message.thread_id
            ))
            await db.commit()
    
    async def get_channel_messages(self, channel_id: str, limit: int = 100) -> List[Message]:
        """チャンネルのメッセージを取得"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT m.*, u.username, u.display_name, u.roles
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.channel_id = ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (channel_id, limit))
            
            rows = await cursor.fetchall()
            return [self._row_to_message(row) for row in rows]
    
    async def get_recent_messages(self, channel_id: str, hours: int = 24) -> List[Message]:
        """最近のメッセージを取得"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT m.*, u.username, u.display_name, u.roles
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.channel_id = ? 
                AND m.timestamp > datetime('now', '-{} hours')
                ORDER BY m.timestamp ASC
            """.format(hours), (channel_id,))
            
            rows = await cursor.fetchall()
            return [self._row_to_message(row) for row in rows]
    
    def _row_to_message(self, row) -> Message:
        """データベース行をMessageエンティティに変換"""
        # ユーザーロールをパース
        roles_json = row['roles']
        try:
            role_names = json.loads(roles_json)
            roles = [UserRole(role) for role in role_names if role in [r.value for r in UserRole]]
        except (json.JSONDecodeError, ValueError):
            roles = [UserRole.STUDENT]
        
        user = User(
            id=row['user_id'],
            username=row['username'],
            display_name=row['display_name'],
            roles=roles
        )
        
        # リアクションをパース
        try:
            reactions = json.loads(row['reactions']) if row['reactions'] else []
        except json.JSONDecodeError:
            reactions = []
        
        return Message(
            id=row['id'],
            channel_id=row['channel_id'],
            channel_name=row['channel_name'],
            user=user,
            content=row['content'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            reactions=reactions,
            is_question=bool(row['is_question']),
            thread_id=row['thread_id']
        )


class SQLiteUserRepository(UserRepository):
    """SQLite ユーザーリポジトリ実装"""
    
    def __init__(self, db_path: str = "lesson_logs.db"):
        self.db_path = db_path
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """ユーザー情報を取得"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            # ロール情報をパース
            try:
                role_names = json.loads(row['roles'])
                roles = [UserRole(role) for role in role_names if role in [r.value for r in UserRole]]
            except (json.JSONDecodeError, ValueError):
                roles = [UserRole.STUDENT]
            
            return User(
                id=row['id'],
                username=row['username'],
                display_name=row['display_name'],
                roles=roles
            )
    
    async def save_user(self, user: User) -> None:
        """ユーザー情報を保存"""
        async with aiosqlite.connect(self.db_path) as db:
            roles_json = json.dumps([role.value for role in user.roles])
            
            await db.execute("""
                INSERT OR REPLACE INTO users (id, username, display_name, roles)
                VALUES (?, ?, ?, ?)
            """, (
                user.id,
                user.username,
                user.display_name,
                roles_json
            ))
            await db.commit()


class SQLiteAlertRepository(AlertRepository):
    """SQLite アラートリポジトリ実装"""
    
    def __init__(self, db_path: str = "lesson_logs.db"):
        self.db_path = db_path
    
    async def save_alert(self, alert: Alert) -> None:
        """アラートを保存"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO alerts (channel_id, message_id, alert_type, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                alert.channel.id,
                alert.message.id,
                alert.alert_type,
                alert.description,
                alert.created_at
            ))
            await db.commit()
    
    async def get_unresolved_alerts(self) -> List[Alert]:
        """未解決のアラートを取得"""
        # 簡略化実装
        return []