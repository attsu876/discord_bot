"""
Discord API クライアント実装
"""
import discord
from discord.ext import commands
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging

from ..domain.entities import Channel, Message, User, UserRole
from ..domain.repositories import MessageRepository, ChannelRepository, UserRepository


class DiscordClient(commands.Bot):
    """Discord クライアント"""
    
    def __init__(self, log_collection_service, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(command_prefix='!', intents=intents, **kwargs)
        self.log_collection_service = log_collection_service
        self.logger = logging.getLogger(__name__)
    
    async def on_ready(self):
        """Bot準備完了時"""
        self.logger.info(f'{self.user} がログインしました')
        print(f'{self.user} がログインしました')
        
        # 起動時に既存メッセージを収集
        await self.collect_existing_messages()
    
    async def on_message(self, message: discord.Message):
        """新しいメッセージ受信時"""
        # Bot自身のメッセージは無視
        if message.author == self.user:
            return
        
        # レッスンチャンネルのみ処理
        if not self._is_lesson_channel(message.channel):
            return
        
        # メッセージデータを準備
        message_data = await self._prepare_message_data(message)
        
        # アプリケーションサービスに処理を委譲
        await self.log_collection_service.process_new_message(message_data)
        
        # コマンド処理
        await self.process_commands(message)
    
    async def collect_existing_messages(self):
        """既存メッセージを収集"""
        self.logger.info("既存メッセージの収集を開始します")
        
        for guild in self.guilds:
            lesson_channels = [ch for ch in guild.channels 
                             if isinstance(ch, discord.TextChannel) and self._is_lesson_channel(ch)]
            
            for channel in lesson_channels:
                try:
                    self.logger.info(f"チャンネル {channel.name} からメッセージを収集中...")
                    
                    async for message in channel.history(limit=100):
                        if message.author == self.user:
                            continue
                        
                        message_data = await self._prepare_message_data(message)
                        await self.log_collection_service.process_new_message(message_data)
                    
                    # レート制限を考慮
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"チャンネル {channel.name} の処理中にエラー: {e}")
        
        self.logger.info("既存メッセージの収集が完了しました")
    
    def _is_lesson_channel(self, channel) -> bool:
        """レッスンチャンネルかどうかを判定"""
        if not isinstance(channel, discord.TextChannel):
            return False
        
        # チャンネル名に "lesson" が含まれるかチェック
        lesson_keywords = ["lesson", "レッスン", "授業", "class"]
        return any(keyword in channel.name.lower() for keyword in lesson_keywords)
    
    async def _prepare_message_data(self, message: discord.Message) -> Dict[str, Any]:
        """メッセージデータを準備"""
        # ユーザーのロール情報を取得
        roles = []
        if hasattr(message.author, 'roles'):
            roles = [role.name for role in message.author.roles if role.name != '@everyone']
        
        return {
            'id': str(message.id),
            'channel_id': str(message.channel.id),
            'channel_name': message.channel.name,
            'content': message.content,
            'timestamp': message.created_at.isoformat(),
            'reactions': [str(reaction.emoji) for reaction in message.reactions],
            'author': {
                'id': str(message.author.id),
                'username': message.author.name,
                'display_name': message.author.display_name,
                'roles': roles
            }
        }


class DiscordChannelRepository(ChannelRepository):
    """Discord チャンネルリポジトリ実装"""
    
    def __init__(self, discord_client: DiscordClient):
        self.client = discord_client
    
    async def get_lesson_channels(self) -> List[Channel]:
        """レッスンチャンネル一覧を取得"""
        channels = []
        
        for guild in self.client.guilds:
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel) and self.client._is_lesson_channel(channel):
                    channels.append(Channel(
                        id=str(channel.id),
                        name=channel.name,
                        is_lesson_channel=True
                    ))
        
        return channels
    
    async def get_channel(self, channel_id: str) -> Optional[Channel]:
        """チャンネル情報を取得"""
        discord_channel = self.client.get_channel(int(channel_id))
        
        if not discord_channel or not isinstance(discord_channel, discord.TextChannel):
            return None
        
        return Channel(
            id=str(discord_channel.id),
            name=discord_channel.name,
            is_lesson_channel=self.client._is_lesson_channel(discord_channel)
        )


# Commands
class DiscordCommands(commands.Cog):
    """Discord コマンド"""
    
    def __init__(self, bot: DiscordClient, log_collection_service):
        self.bot = bot
        self.log_collection_service = log_collection_service
    
    @commands.command(name='export_logs')
    @commands.has_permissions(administrator=True)
    async def export_logs(self, ctx, channel_id: str = None):
        """ログをエクスポート"""
        target_channel_id = channel_id or str(ctx.channel.id)
        
        try:
            file_path = await self.log_collection_service.export_channel_logs(target_channel_id)
            await ctx.send(f"ログをエクスポートしました: {file_path}")
        except Exception as e:
            await ctx.send(f"エクスポート中にエラーが発生しました: {e}")
    
    @commands.command(name='analyze_now')
    @commands.has_permissions(administrator=True)
    async def analyze_now(self, ctx):
        """手動でメッセージ分析を実行"""
        try:
            await self.log_collection_service.collect_and_analyze_messages()
            await ctx.send("分析が完了しました")
        except Exception as e:
            await ctx.send(f"分析中にエラーが発生しました: {e}")