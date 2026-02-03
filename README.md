# AI News Collector

AIニュースを自動収集してSlackに通知するシステム

## 機能

- **AI時事ニュース**: AI/人工知能、生成AI、機械学習の最新ニュース
- **AIエージェント活用**: AIエージェントの実用例・活用事例
- **データ×AI**: データ分析・データ基盤とAIの組み合わせ
- **アソビュー関連**: アソビュー株式会社の記事（別セクション）

## セットアップ

### 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 環境変数の設定

```bash
cp .env.example .env
# .env を編集して SLACK_WEBHOOK_URL を設定
```

## 使い方

### ローカル実行

```bash
# Slack通知あり
python ai_news_collector.py

# Slack通知なし（ファイル保存のみ）
python ai_news_collector.py --no-slack
```

### 出力

`output/YYYY-MM-DD.md` にMarkdown形式のレポートが保存されます。

## 定期実行（GitHub Actions）

毎朝9:00 (JST) に自動実行されます。

### 手動実行

1. GitHub → Actions → "Collect AI News"
2. "Run workflow" をクリック

### Secretsの設定

| Name | Value |
|------|-------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
