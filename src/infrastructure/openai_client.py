"""
OpenAI API クライアント実装
"""
from openai import AsyncOpenAI
from typing import List, Dict, Any
import logging
import json

from ..domain.entities import Message, Alert


class OpenAIAnalyzer:
    """OpenAI API を使用したメッセージ分析"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
    
    async def analyze_off_topic_conversation(self, messages: List[Message]) -> List[Alert]:
        """振り返り以外の話題を検出"""
        if not messages:
            return []
        
        try:
            # メッセージを分析用のテキストに変換
            conversation_text = self._format_messages_for_analysis(messages)
            
            # GPT-4.1 で分析
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_analysis_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": f"以下の会話を分析してください：\n\n{conversation_text}"
                    }
                ],
                functions=[
                    {
                        "name": "detect_off_topic",
                        "description": "振り返り以外の話題を検出する",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "off_topic_messages": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "message_id": {"type": "string"},
                                            "reason": {"type": "string"},
                                            "topic_type": {"type": "string"},
                                            "severity": {"type": "string", "enum": ["low", "medium", "high"]}
                                        },
                                        "required": ["message_id", "reason", "topic_type", "severity"]
                                    }
                                }
                            },
                            "required": ["off_topic_messages"]
                        }
                    }
                ],
                function_call="auto"
            )
            
            # 結果を解析してアラートを生成
            return self._process_analysis_result(response, messages)
            
        except Exception as e:
            self.logger.error(f"OpenAI分析エラー: {e}")
            return []
    
    def _format_messages_for_analysis(self, messages: List[Message]) -> str:
        """メッセージを分析用テキストに変換"""
        formatted_messages = []
        
        for msg in messages:
            user_type = "運営" if not msg.user.is_student_side() else "生徒"
            formatted_messages.append(
                f"[{msg.timestamp.strftime('%H:%M')}] {msg.user.display_name}({user_type}): {msg.content}"
            )
        
        return "\n".join(formatted_messages)
    
    def _get_analysis_system_prompt(self) -> str:
        """分析用システムプロンプト"""
        return """
あなたは高校生向けプログラミングレッスンのモニタリングシステムです。
Discord上の会話を分析し、振り返り以外の話題を検出してください。

【検出対象】
1. プログラミング学習以外の雑談
2. 不適切な内容（ネガティブ、ポジティブ問わず）
3. 個人的な悩み相談
4. 学習と関係ない技術的議論
5. その他レッスンの目的から逸脱した内容

【検出しない内容】
- プログラミングに関する質問・回答
- 学習の振り返り
- 課題や宿題に関する議論
- 技術的なトラブルシューティング
- 建設的な学習支援

各メッセージについて、トピックのタイプ（雑談、不適切、相談、技術議論、その他）と
重要度（low/medium/high）を判定してください。
"""
    
    def _process_analysis_result(self, response, messages: List[Message]) -> List[Alert]:
        """分析結果を処理してアラートを生成"""
        alerts = []
        
        if not response.choices[0].message.function_call:
            return alerts
        
        try:
            function_args = json.loads(response.choices[0].message.function_call.arguments)
            off_topic_messages = function_args.get("off_topic_messages", [])
            
            for off_topic_msg in off_topic_messages:
                # メッセージIDに対応するメッセージを検索
                target_message = None
                for msg in messages:
                    if msg.id == off_topic_msg["message_id"]:
                        target_message = msg
                        break
                
                if target_message:
                    from ..domain.entities import Channel  # 遅延インポートで循環依存を回避
                    alert = Alert(
                        channel=Channel(
                            id=target_message.channel_id,
                            name=target_message.channel_name,
                            is_lesson_channel=True
                        ),
                        message=target_message,
                        alert_type="off_topic",
                        description=f"トピック: {off_topic_msg['topic_type']} - {off_topic_msg['reason']}",
                        created_at=target_message.timestamp
                    )
                    alerts.append(alert)
        
        except json.JSONDecodeError as e:
            self.logger.error(f"OpenAI応答の解析エラー: {e}")
        
        return alerts
    
    async def test_connection(self) -> bool:
        """OpenAI接続テスト"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            self.logger.info("OpenAI接続成功")
            return True
        except Exception as e:
            self.logger.error(f"OpenAI接続失敗: {e}")
            return False