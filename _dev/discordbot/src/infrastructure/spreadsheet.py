"""
スプレッドシート出力サービス実装
"""
import pandas as pd
from typing import List
import os
from datetime import datetime

from ..domain.entities import Message
from ..domain.repositories import SpreadsheetService


class ExcelSpreadsheetService(SpreadsheetService):
    """Excel スプレッドシートサービス実装"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    async def export_channel_logs(self, channel_id: str, messages: List[Message]) -> str:
        """チャンネルログをスプレッドシートに出力"""
        if not messages:
            return ""
        
        # データフレーム用のデータを準備
        data = []
        for msg in messages:
            data.append({
                'メッセージID': msg.id,
                'チャンネル名': msg.channel_name,
                '投稿者名': msg.user.display_name,
                'ユーザー名': msg.user.username,
                'ユーザータイプ': '運営' if not msg.user.is_student_side() else '生徒',
                'ロール': ', '.join([role.value for role in msg.user.roles]),
                'メッセージ内容': msg.content,
                '投稿日時': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                '質問フラグ': '質問' if msg.is_question else '',
                'リアクション': ', '.join(msg.reactions),
                'スレッドID': msg.thread_id or ''
            })
        
        # データフレームを作成
        df = pd.DataFrame(data)
        
        # ファイル名を生成
        channel_name = messages[0].channel_name if messages else 'unknown'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{channel_name}_logs_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        # Excelファイルとして保存
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='メッセージログ', index=False)
            
            # ワークシートを取得してフォーマット
            worksheet = writer.sheets['メッセージログ']
            
            # 列幅を調整
            column_widths = {
                'A': 15,  # メッセージID
                'B': 20,  # チャンネル名
                'C': 15,  # 投稿者名
                'D': 15,  # ユーザー名
                'E': 10,  # ユーザータイプ
                'F': 20,  # ロール
                'G': 50,  # メッセージ内容
                'H': 20,  # 投稿日時
                'I': 10,  # 質問フラグ
                'J': 15,  # リアクション
                'K': 15   # スレッドID
            }
            
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            # ヘッダーの書式設定
            from openpyxl.styles import Font, PatternFill
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
        
        return filepath


class CSVSpreadsheetService(SpreadsheetService):
    """CSV スプレッドシートサービス実装"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    async def export_channel_logs(self, channel_id: str, messages: List[Message]) -> str:
        """チャンネルログをCSVに出力"""
        if not messages:
            return ""
        
        # データフレーム用のデータを準備
        data = []
        for msg in messages:
            data.append({
                'message_id': msg.id,
                'channel_name': msg.channel_name,
                'display_name': msg.user.display_name,
                'username': msg.user.username,
                'user_type': 'staff' if not msg.user.is_student_side() else 'student',
                'roles': ', '.join([role.value for role in msg.user.roles]),
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'is_question': msg.is_question,
                'reactions': ', '.join(msg.reactions),
                'thread_id': msg.thread_id or ''
            })
        
        # データフレームを作成
        df = pd.DataFrame(data)
        
        # ファイル名を生成
        channel_name = messages[0].channel_name if messages else 'unknown'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{channel_name}_logs_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        # CSVファイルとして保存（UTF-8 BOM付き）
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath