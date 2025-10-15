"""
Slack API クライアント実装
"""
import asyncio
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from typing import Dict, Any
import logging

from ..domain.entities import Alert
from ..domain.repositories import NotificationService


class SlackNotificationService(NotificationService):
    """Slack 通知サービス実装"""
    
    def __init__(self, token: str, channel: str):
        self.client = AsyncWebClient(token=token)
        self.channel = channel
        self.logger = logging.getLogger(__name__)
    
    async def send_alert(self, alert: Alert) -> None:
        """アラートをSlackに送信"""
        try:
            message = self._format_alert_message(alert)
            
            response = await self.client.chat_postMessage(
                channel=self.channel,
                **message
            )
            
            self.logger.info(f"Slackにアラート送信完了: {response['ts']}")
            
        except SlackApiError as e:
            self.logger.error(f"Slack送信エラー: {e.response['error']}")
            raise
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise
    
    def _format_alert_message(self, alert: Alert) -> Dict[str, Any]:
        """アラートメッセージをフォーマット"""
        
        if alert.alert_type == "unanswered_question":
            return self._format_unanswered_question_alert(alert)
        elif alert.alert_type == "off_topic":
            return self._format_off_topic_alert(alert)
        else:
            return self._format_generic_alert(alert)
    
    def _format_unanswered_question_alert(self, alert: Alert) -> Dict[str, Any]:
        """未回答質問アラートをフォーマット"""
        return {
            "text": f"🚨 未回答の質問があります - #{alert.channel.name}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 未回答の質問があります"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*チャンネル:*\n#{alert.channel.name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*投稿者:*\n{alert.message.user.display_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*投稿時刻:*\n{alert.message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*ユーザータイプ:*\n{'生徒側' if alert.message.user.is_student_side() else '運営側'}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*メッセージ内容:*\n```{alert.message.content[:500]}```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"⏰ {alert.description}"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Discordで確認"
                            },
                            "url": f"https://discord.com/channels/{alert.message.channel_id}/{alert.message.id}",
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
    
    def _format_off_topic_alert(self, alert: Alert) -> Dict[str, Any]:
        """オフトピックアラートをフォーマット"""
        return {
            "text": f"📢 振り返り以外の話題を検出 - #{alert.channel.name}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📢 振り返り以外の話題を検出"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*チャンネル:*\n#{alert.channel.name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*投稿者:*\n{alert.message.user.display_name}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*メッセージ内容:*\n```{alert.message.content[:500]}```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"💭 {alert.description}"
                        }
                    ]
                }
            ]
        }
    
    def _format_generic_alert(self, alert: Alert) -> Dict[str, Any]:
        """汎用アラートをフォーマット"""
        return {
            "text": f"⚠️ アラート - #{alert.channel.name}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ *{alert.alert_type}*\n\n{alert.description}\n\nチャンネル: #{alert.channel.name}"
                    }
                }
            ]
        }
    
    async def test_connection(self) -> bool:
        """Slack接続テスト"""
        try:
            response = await self.client.auth_test()
            self.logger.info(f"Slack接続成功: {response['user']}")
            return True
        except Exception as e:
            self.logger.error(f"Slack接続失敗: {e}")
            return False