#!/usr/bin/env python3
"""
AIニュース収集システム - エントリーポイント（境界層）

責務:
- コマンドライン引数の解析
- 環境変数・設定の読み込み
- 依存関係の解決（各層のインスタンス生成と注入）
- 実行戦略の選択
- 実行と結果ハンドリング
"""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from domain.theme import Theme
from repositories.theme_repository import ThemeRepository
from sources.google_news_rss import GoogleNewsRSSSource
from stores.json_file_store import JsonFileStore
from summarizers.claude_summarizer import ClaudeCLISummarizer, NoOpSummarizer
from notifiers.slack_notifier import SlackWebhookNotifier, NoOpNotifier
from transformers.markdown_formatter import MarkdownFormatter
from transformers.slack_block_formatter import SlackBlockFormatter
from usecases.daily_collector import DailyCollector
from usecases.weekly_reporter import WeeklyReporter
from usecases.inputs import DailyCollectionInput, WeeklyReportInput


# デフォルト設定
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "themes.yaml"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "articles"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_WEEKLY_OUTPUT_DIR = PROJECT_ROOT / "output" / "weekly"


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="AIニュース収集システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 日次収集（AI要約あり）
  python main.py daily

  # 日次収集（AI要約なし）
  python main.py daily --no-ai-summary

  # 日次収集（Slack通知なし）
  python main.py daily --no-slack

  # 週次レポート
  python main.py weekly

  # 2週間前のレポート生成
  python main.py weekly --weeks-back 2

環境変数:
  SLACK_WEBHOOK_URL  : Slack Webhook URL（通知に必要）

前提条件:
  AI要約を使用する場合は、Claude CLI（claudeコマンド）が
  インストールされている必要があります。
""",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # daily コマンド
    daily_parser = subparsers.add_parser("daily", help="日次ニュース収集")
    daily_parser.add_argument(
        "--no-ai-summary",
        action="store_true",
        help="AI要約をスキップ",
    )
    daily_parser.add_argument(
        "--no-slack",
        action="store_true",
        help="Slack通知をスキップ",
    )
    daily_parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="収集対象日（YYYY-MM-DD形式、デフォルト: 今日）",
    )
    daily_parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Markdown出力先ディレクトリ（デフォルト: {DEFAULT_OUTPUT_DIR}）",
    )

    # weekly コマンド
    weekly_parser = subparsers.add_parser("weekly", help="週次レポート生成")
    weekly_parser.add_argument(
        "--no-slack",
        action="store_true",
        help="Slack通知をスキップ",
    )
    weekly_parser.add_argument(
        "--weeks-back",
        type=int,
        default=0,
        help="何週間前のレポートを生成するか（デフォルト: 0=今週）",
    )
    weekly_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="集計日数（デフォルト: 7日）",
    )
    weekly_parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="上位N件を抽出（デフォルト: 20）",
    )
    weekly_parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_WEEKLY_OUTPUT_DIR,
        help=f"週次レポート出力先（デフォルト: {DEFAULT_WEEKLY_OUTPUT_DIR}）",
    )

    return parser.parse_args()


def load_themes() -> list[Theme]:
    """テーマ設定を読み込み"""
    repo = ThemeRepository(DEFAULT_CONFIG_PATH)
    return repo.load_all()


def build_daily_collector(
    themes: list[Theme],
    enable_ai_summary: bool,
    enable_slack: bool,
) -> DailyCollector:
    """日次収集ユースケースを構築（依存関係の注入）"""
    # NewsSource
    news_source = GoogleNewsRSSSource(
        rate_limit_delay=0.5,
        num_results_per_keyword=3,
    )

    # Summarizer（Claude CLIを使用）
    if enable_ai_summary:
        summarizer = ClaudeCLISummarizer(timeout=60)
    else:
        summarizer = NoOpSummarizer()

    # ArticleStore
    article_store = JsonFileStore(DEFAULT_DATA_DIR)

    # Notifier
    if enable_slack:
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("[WARN] SLACK_WEBHOOK_URLが未設定のため、Slack通知をスキップします")
            notifier = NoOpNotifier()
        else:
            notifier = SlackWebhookNotifier(
                webhook_url=webhook_url,
                formatter=SlackBlockFormatter(),
            )
    else:
        notifier = NoOpNotifier()

    # Formatter
    markdown_formatter = MarkdownFormatter()

    return DailyCollector(
        news_source=news_source,
        summarizer=summarizer,
        article_store=article_store,
        notifier=notifier,
        markdown_formatter=markdown_formatter,
        themes=themes,
    )


def build_weekly_reporter(enable_slack: bool) -> WeeklyReporter:
    """週次レポートユースケースを構築（依存関係の注入）"""
    # ArticleStore
    article_store = JsonFileStore(DEFAULT_DATA_DIR)

    # Notifier
    if enable_slack:
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("[WARN] SLACK_WEBHOOK_URLが未設定のため、Slack通知をスキップします")
            notifier = NoOpNotifier()
        else:
            notifier = SlackWebhookNotifier(
                webhook_url=webhook_url,
                formatter=SlackBlockFormatter(),
            )
    else:
        notifier = NoOpNotifier()

    # Formatter
    markdown_formatter = MarkdownFormatter()

    return WeeklyReporter(
        article_store=article_store,
        notifier=notifier,
        markdown_formatter=markdown_formatter,
    )


def run_daily(args: argparse.Namespace) -> None:
    """日次収集を実行"""
    # テーマ読み込み
    themes = load_themes()
    print(f"[INFO] {len(themes)}件のテーマを読み込みました")

    # 対象日を決定
    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = date.today()

    # 入力モデル構築
    input_data = DailyCollectionInput(
        target_date=target_date,
        output_dir=args.output_dir,
        enable_ai_summary=not args.no_ai_summary,
    )

    # ユースケース構築
    collector = build_daily_collector(
        themes=themes,
        enable_ai_summary=input_data.enable_ai_summary,
        enable_slack=not args.no_slack,
    )

    # 実行
    collector.run(input_data)


def run_weekly(args: argparse.Namespace) -> None:
    """週次レポートを実行"""
    # 期間を計算
    end_date = date.today() - timedelta(weeks=args.weeks_back)
    # 週の終わり（日曜日）に調整
    days_until_sunday = (6 - end_date.weekday()) % 7
    if args.weeks_back > 0:
        # 過去の週の場合は、その週の日曜日
        end_date = end_date + timedelta(days=days_until_sunday)
    # 今週の場合は今日を終了日とする

    # 入力モデル構築
    input_data = WeeklyReportInput(
        end_date=end_date,
        days_back=args.days,
        output_dir=args.output_dir,
        top_n=args.top_n,
    )

    # ユースケース構築
    reporter = build_weekly_reporter(enable_slack=not args.no_slack)

    # 実行
    reporter.run(input_data)


def main() -> None:
    """メインエントリーポイント"""
    args = parse_args()

    try:
        if args.command == "daily":
            run_daily(args)
        elif args.command == "weekly":
            run_weekly(args)
    except FileNotFoundError as e:
        print(f"[ERROR] ファイルが見つかりません: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 実行エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
