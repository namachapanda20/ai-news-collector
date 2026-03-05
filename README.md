# AI News Collector

AIニュースを自動収集し、AI要約・重要度スコアリングを行い、Slackに通知するシステム

## 機能

### 日次収集
- **テーマベースの収集**: YAML設定ファイルでテーマと検索キーワードを管理
- **AI要約・スコアリング**: Claude CLI（claudeコマンド）で記事を要約し、1-5の重要度スコアを付与
- **データ蓄積**: JSON形式で日次データを保存
- **Slack通知**: 収集結果をSlackに通知

### 週次レポート
- **記事集約**: 過去7日分（設定可能）の記事を集約
- **重要度ランキング**: スコア順にソート、上位20件を抽出
- **週次サマリー**: Slackへ週次レポートを配信

### テーマ（デフォルト設定）
- **AI時事ニュース**: AI/人工知能、生成AI、機械学習の最新ニュース
- **AIエージェント活用**: AIエージェントの実用例・活用事例
- **データ×AI**: データ分析・データ基盤とAIの組み合わせ
- **アソビュー関連**: アソビュー株式会社の記事

## ディレクトリ構成

```
ai-news-collector/
├── main.py                     # エントリーポイント（境界層）
├── config/
│   └── themes.yaml             # テーマ設定
├── usecases/                   # ユースケース層
│   ├── inputs.py               # 入力モデル
│   ├── daily_collector.py      # 日次収集
│   └── weekly_reporter.py      # 週次レポート
├── interfaces/                 # 抽象（Protocol）
│   ├── news_source.py
│   ├── summarizer.py
│   ├── notifier.py
│   └── article_store.py
├── domain/                     # ドメインモデル
│   ├── article.py              # 記事エンティティ
│   └── theme.py                # テーマエンティティ
├── sources/
│   └── google_news_rss.py      # Google News取得
├── summarizers/
│   └── claude_summarizer.py    # Claude CLI要約
├── notifiers/
│   └── slack_notifier.py       # Slack通知
├── stores/
│   └── json_file_store.py      # JSON蓄積
├── transformers/
│   ├── markdown_formatter.py
│   └── slack_block_formatter.py
├── repositories/
│   └── theme_repository.py     # テーマ読み込み
├── .github/workflows/
│   ├── daily-collect.yml       # 日次（毎朝9時JST）
│   └── weekly-report.yml       # 週次（毎週月曜9時JST）
├── data/articles/              # 日次データ蓄積
└── output/                     # レポート出力
    └── weekly/                 # 週次レポート
```

## セットアップ

### 1. 依存関係のインストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# パッケージのインストール
pip install -r requirements.txt
```

### 2. Claude CLI（AI要約に必要）

AI要約機能を使用する場合は、Claude CLIがインストールされている必要があります。

```bash
# Claude CLIのインストール（npmを使用）
npm install -g @anthropic-ai/claude-code

# 認証
claude auth login
```

### 3. 環境変数の設定

```bash
cp .env.example .env
# .env を編集
```

| 環境変数 | 説明 | 必須 |
|----------|------|------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | Slack通知時 |

## 使い方

### 日次収集

```bash
# 日次収集（AI要約あり）※Claude CLIが必要
python main.py daily

# AI要約なしで実行
python main.py daily --no-ai-summary

# Slack通知なしで実行
python main.py daily --no-slack

# 特定の日付で実行
python main.py daily --date 2026-03-01

# 全オプション
python main.py daily --no-ai-summary --no-slack --date 2026-03-01
```

### 週次レポート

```bash
# 週次レポート（過去7日分）
python main.py weekly

# 2週間前のレポート生成
python main.py weekly --weeks-back 2

# 過去14日分を集計
python main.py weekly --days 14

# 上位10件のみ抽出
python main.py weekly --top-n 10

# Slack通知なし
python main.py weekly --no-slack
```

### 出力ファイル

| ファイル | 説明 |
|----------|------|
| `data/articles/YYYY-MM-DD.json` | 日次収集データ（JSON） |
| `output/YYYY-MM-DD.md` | 日次レポート（Markdown） |
| `output/weekly/weekly_YYYY-MM-DD_YYYY-MM-DD.md` | 週次レポート（Markdown） |

## テーマ設定（config/themes.yaml）

テーマごとにキーワードと重要度判定基準を設定できます。

```yaml
themes:
  - name: "AI時事ニュース"
    priority: 1              # 優先度（1が最高）
    max_articles: 10         # 収集する最大記事数
    keywords:                # 検索キーワード
      - "AI 人工知能 最新"
      - "生成AI ChatGPT Claude"
    importance_criteria: |   # 重要度判定基準（Claude CLIへのプロンプト）
      以下の観点で重要度を1-5で判定してください:
      高スコア(4-5): 技術的ブレイクスルー、大手企業の発表
      中スコア(3): 興味深いが限定的
      低スコア(1-2): 一般的なニュース
```

## 定期実行（GitHub Actions）

### スケジュール

| ワークフロー | 実行タイミング | AI要約 |
|-------------|---------------|--------|
| `daily-collect.yml` | 毎朝9:00 (JST) | スキップ |
| `weekly-report.yml` | 毎週月曜9:00 (JST) | - |

**注意**: GitHub ActionsではClaude CLIが使えないため、AI要約は自動的にスキップされます。
AI要約が必要な場合は、ローカルで `python main.py daily` を実行してください。

### 手動実行

1. GitHub → Actions
2. "Daily AI News Collection" または "Weekly AI News Report" を選択
3. "Run workflow" をクリック
4. オプションを設定して実行

### Secretsの設定

GitHub リポジトリの Settings → Secrets and variables → Actions で設定:

| Name | Value | 必須 |
|------|-------|------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | Slack通知時 |

## 検証方法

### ローカルテスト

```bash
# 1. AI要約なし・Slack通知なしで日次収集
python main.py daily --no-ai-summary --no-slack

# 2. データが保存されることを確認
ls data/articles/
cat data/articles/$(date +%Y-%m-%d).json | head -50

# 3. AI要約ありで実行（Claude CLIが必要）
python main.py daily --no-slack

# 4. Slack通知テスト
export SLACK_WEBHOOK_URL=https://hooks.slack.com/xxx
python main.py daily --no-ai-summary

# 5. 週次レポートテスト
python main.py weekly --no-slack
```

## アーキテクチャ

クリーンアーキテクチャに基づいた設計:

- **Presentation層** (`main.py`): 境界層として依存関係を組み立て
- **UseCase層** (`usecases/`): ビジネスロジック
- **Interface層** (`interfaces/`): Protocol定義
- **Domain層** (`domain/`): エンティティ定義
- **Infrastructure層** (`sources/`, `stores/`, `notifiers/`): 具体実装

依存の方向:
```
main.py → UseCase → Interface ← Infrastructure
                 → Domain
```

## ライセンス

MIT License
