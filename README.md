# Discord Lesson Log Analyzer

高校生以上の生徒向けのDiscordレッスンチャンネルのやり取りログを収集し、Slackへ通知するシステム

## プロジェクト概要

- 各レッスンチャンネルでの生徒と先生の会話を記録
- ログを分析し、フォローが必要な会話や問題のあるやり取りを検出
- Slack専用チャンネルでアラート通知

## 主な機能

### ログ収集
- 各レッスンチャンネルのメッセージとリアクションを記録
- チャンネルの増減に自動対応

### アラート機能
- 先生の返信が途切れている会話を検出
- 生徒からの質問に返信がない場合を通知
- 振り返り以外の会話トピックを検出

### データ出力
- チャンネルごとにスプレッドシートを作成してログを保存

### ユーザー分類
- ロール(アドミン、サポート、メンター、AIアシスタント vs 生徒、保護者)で運営側とユーザー側を区別

## 技術スタック

- Python 3.8+
- discord.py
- OpenAI API (GPT-4.1)
- Slack SDK
- pandas (スプレッドシート作成)

## セットアップ

1. 依存関係のインストール（ローカル実行）
```bash
pip install -r requirements.txt
```

2. 環境変数の設定
```
DISCORD_BOT_TOKEN=your_discord_token
SLACK_BOT_TOKEN=your_slack_token
OPENAI_API_KEY=your_openai_key
```

3. 設定ファイルの編集
`config/settings.py` で対象チャンネルやSlack通知先を設定

4. 実行（ローカル）
```bash
python main.py
```

## Dockerで実行

Windows PowerShell での例：

```powershell
# 初回のみ：出力とデータ用のフォルダを作成
New-Item -ItemType Directory -Force -Path .\data | Out-Null
New-Item -ItemType Directory -Force -Path .\output | Out-Null

# .env を用意（.env.example をコピーして値を設定）
Copy-Item .env.example .env -Force

# ビルド＆起動
docker compose build
docker compose up -d

# ログ確認
docker compose logs -f
```

コンテナは `DATABASE_PATH=/app/data/lesson_logs.db` を使用します。 `./data` と `./output` がボリュームにマウントされ、DBとエクスポート結果をホスト側で確認できます。

## アーキテクチャ

DDD（ドメイン駆動設計）のアプローチを採用：

- **Domain Layer**: ビジネスロジックの核心部分
- **Application Layer**: ユースケースの実装
- **Infrastructure Layer**: 外部システム（Discord, Slack, OpenAI）との接続
- **Interface Layer**: アプリケーションの入口点

## 開発チーム

- **伊藤**: 技術サポート
- **枝**: メイン開発担当
- **山浦**: 要件定義

## ライセンス

MIT License