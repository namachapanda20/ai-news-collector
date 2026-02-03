#!/usr/bin/env python3
"""
AIニュース収集システム
- AI関連の時事ニュース
- AIエージェントの実用例
- データ分析・データ基盤とAI
- アソビュー株式会社の記事
"""

import argparse
import feedparser
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import html
import time
from urllib.parse import quote

# .env ファイルを読み込み
load_dotenv()


class SlackNotifier:
    """Slack Webhook経由で通知を送信するクラス"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def _truncate(self, text: str, max_length: int = 100) -> str:
        """テキストを指定の長さに切り詰める"""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def format_message(
        self, ai_articles: list[dict], asoview_articles: list[dict]
    ) -> dict:
        """Slack用のメッセージをBlock Kit形式で作成"""
        today = datetime.now().strftime("%Y-%m-%d")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"AIニュース ({today})",
                    "emoji": True,
                },
            },
            {"type": "divider"},
        ]

        # AI関連ニュース（カテゴリごと）
        if ai_articles:
            categories = {}
            for article in ai_articles:
                cat = article["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(article)

            for category, articles in categories.items():
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{category}*",
                        },
                    }
                )

                for article in articles[:3]:  # 各カテゴリ最大3件
                    title = self._truncate(article["title"], 80)
                    blocks.append(
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"• <{article['url']}|{title}>\n  _{article['source']}_",
                            },
                        }
                    )

        # アソビュー関連
        if asoview_articles:
            blocks.append({"type": "divider"})
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*アソビュー関連*",
                    },
                }
            )

            for article in asoview_articles[:5]:  # 最大5件
                title = self._truncate(article["title"], 80)
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• <{article['url']}|{title}>\n  _{article['source']}_",
                        },
                    }
                )

        # フッター
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"AI: {len(ai_articles)}件 | アソビュー: {len(asoview_articles)}件 | 自動収集",
                    }
                ],
            }
        )

        return {"blocks": blocks}

    def send(self, ai_articles: list[dict], asoview_articles: list[dict]) -> bool:
        """Slackに通知を送信"""
        if not self.webhook_url:
            print("[WARN] Slack Webhook URLが設定されていません")
            return False

        message = self.format_message(ai_articles, asoview_articles)

        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            if response.status_code == 200:
                print("[SUCCESS] Slackに通知しました")
                return True
            else:
                print(f"[ERROR] Slack送信失敗: {response.status_code} {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR] Slack送信エラー: {e}")
            return False


class AINewsCollector:
    """AIニュースを収集してMarkdownに出力するクラス"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.collected_urls = set()  # 重複排除用
        self.max_articles = 10

    def _get_google_news_rss(self, query: str, num_results: int = 5) -> list[dict]:
        """Google NewsのRSSフィードから記事を取得"""
        encoded_query = quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"

        articles = []
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:num_results]:
                if entry.link in self.collected_urls:
                    continue

                # HTMLタグを除去して要約を取得
                summary = ""
                if hasattr(entry, "summary"):
                    soup = BeautifulSoup(entry.summary, "html.parser")
                    summary = soup.get_text(strip=True)[:200]

                # 公開日時のパース
                pub_date = ""
                if hasattr(entry, "published"):
                    pub_date = entry.published

                articles.append({
                    "title": html.unescape(entry.title),
                    "url": entry.link,
                    "summary": summary if summary else "要約なし",
                    "published": pub_date,
                    "source": entry.get("source", {}).get("title", "Google News"),
                })
                self.collected_urls.add(entry.link)

        except Exception as e:
            print(f"[ERROR] Google News取得エラー ({query}): {e}")

        return articles

    def collect_ai_news(self) -> list[dict]:
        """AI関連の時事ニュースを収集"""
        print("[INFO] AI関連ニュースを収集中...")
        queries = [
            "AI 人工知能 最新",
            "生成AI ChatGPT Claude",
            "機械学習 ディープラーニング",
        ]

        articles = []
        for query in queries:
            results = self._get_google_news_rss(query, num_results=3)
            for article in results:
                article["category"] = "AI時事ニュース"
            articles.extend(results)
            time.sleep(0.5)  # レート制限対策

        return articles

    def collect_ai_agent_news(self) -> list[dict]:
        """AIエージェントの実用例・活用例を収集"""
        print("[INFO] AIエージェント関連ニュースを収集中...")
        queries = [
            "AIエージェント 活用事例",
            "AI自動化 業務効率化",
            "LLM エージェント 実用",
        ]

        articles = []
        for query in queries:
            results = self._get_google_news_rss(query, num_results=2)
            for article in results:
                article["category"] = "AIエージェント活用"
            articles.extend(results)
            time.sleep(0.5)

        return articles

    def collect_data_ai_news(self) -> list[dict]:
        """データ分析・データ基盤とAIの組み合わせニュースを収集"""
        print("[INFO] データ×AI関連ニュースを収集中...")
        queries = [
            "データ分析 AI 活用",
            "データ基盤 機械学習",
            "ビッグデータ AI",
        ]

        articles = []
        for query in queries:
            results = self._get_google_news_rss(query, num_results=2)
            for article in results:
                article["category"] = "データ×AI"
            articles.extend(results)
            time.sleep(0.5)

        return articles

    def collect_asoview_news(self) -> list[dict]:
        """アソビュー株式会社関連の記事を収集"""
        print("[INFO] アソビュー関連ニュースを収集中...")
        queries = [
            "アソビュー株式会社",
            "アソビュー asoview",
        ]

        articles = []
        for query in queries:
            results = self._get_google_news_rss(query, num_results=5)
            for article in results:
                article["category"] = "アソビュー関連"
            articles.extend(results)
            time.sleep(0.5)

        return articles

    def collect_all(self) -> tuple[list[dict], list[dict]]:
        """すべてのニュースを収集（アソビュー関連は別）"""
        # AI関連ニュース
        ai_articles = []
        ai_articles.extend(self.collect_ai_news())
        ai_articles.extend(self.collect_ai_agent_news())
        ai_articles.extend(self.collect_data_ai_news())

        # 合計10件まで制限
        ai_articles = ai_articles[: self.max_articles]

        # アソビュー関連（別枠）
        asoview_articles = self.collect_asoview_news()

        return ai_articles, asoview_articles

    def generate_markdown(
        self, ai_articles: list[dict], asoview_articles: list[dict]
    ) -> str:
        """Markdown形式のレポートを生成"""
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [
            f"# AIニュース収集レポート ({today})",
            "",
            f"収集日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]

        # AI関連ニュースセクション
        lines.append("## AI関連ニュース")
        lines.append("")

        if ai_articles:
            # カテゴリごとにグループ化
            categories = {}
            for article in ai_articles:
                cat = article["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(article)

            for category, articles in categories.items():
                lines.append(f"### {category}")
                lines.append("")
                for article in articles:
                    lines.append(f"#### {article['title']}")
                    lines.append("")
                    lines.append(f"- **URL**: {article['url']}")
                    lines.append(f"- **ソース**: {article['source']}")
                    if article["published"]:
                        lines.append(f"- **公開日**: {article['published']}")
                    lines.append(f"- **要約**: {article['summary']}")
                    lines.append("")
        else:
            lines.append("該当する記事が見つかりませんでした。")
            lines.append("")

        lines.append("---")
        lines.append("")

        # アソビュー関連セクション
        lines.append("## アソビュー株式会社 関連記事")
        lines.append("")

        if asoview_articles:
            for article in asoview_articles:
                lines.append(f"### {article['title']}")
                lines.append("")
                lines.append(f"- **URL**: {article['url']}")
                lines.append(f"- **ソース**: {article['source']}")
                if article["published"]:
                    lines.append(f"- **公開日**: {article['published']}")
                lines.append(f"- **要約**: {article['summary']}")
                lines.append("")
        else:
            lines.append("該当する記事が見つかりませんでした。")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*このレポートはAIニュース収集システムにより自動生成されました。*")

        return "\n".join(lines)

    def save_report(self, content: str) -> Path:
        """レポートをファイルに保存"""
        today = datetime.now().strftime("%Y-%m-%d")
        filepath = self.output_dir / f"{today}.md"
        filepath.write_text(content, encoding="utf-8")
        return filepath

    def run(self) -> Path:
        """ニュース収集を実行"""
        print("=" * 50)
        print("AIニュース収集システム 開始")
        print("=" * 50)

        ai_articles, asoview_articles = self.collect_all()

        print(f"\n[INFO] AI関連ニュース: {len(ai_articles)}件")
        print(f"[INFO] アソビュー関連: {len(asoview_articles)}件")

        markdown = self.generate_markdown(ai_articles, asoview_articles)
        filepath = self.save_report(markdown)

        print(f"\n[SUCCESS] レポートを保存しました: {filepath}")
        print("=" * 50)

        return filepath


def main():
    parser = argparse.ArgumentParser(description="AIニュース収集システム")
    parser.add_argument(
        "--slack-webhook",
        help="Slack Webhook URL (環境変数 SLACK_WEBHOOK_URL でも設定可)",
        default=os.environ.get("SLACK_WEBHOOK_URL"),
    )
    parser.add_argument(
        "--no-slack",
        action="store_true",
        help="Slack通知を無効化",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="出力ディレクトリ (デフォルト: output)",
    )
    args = parser.parse_args()

    # ニュース収集
    collector = AINewsCollector(output_dir=args.output_dir)

    print("=" * 50)
    print("AIニュース収集システム 開始")
    print("=" * 50)

    ai_articles, asoview_articles = collector.collect_all()

    print(f"\n[INFO] AI関連ニュース: {len(ai_articles)}件")
    print(f"[INFO] アソビュー関連: {len(asoview_articles)}件")

    # Markdown保存
    markdown = collector.generate_markdown(ai_articles, asoview_articles)
    filepath = collector.save_report(markdown)
    print(f"\n[SUCCESS] レポートを保存しました: {filepath}")

    # Slack通知
    if not args.no_slack and args.slack_webhook:
        print("\n[INFO] Slackに通知中...")
        notifier = SlackNotifier(args.slack_webhook)
        notifier.send(ai_articles, asoview_articles)
    elif not args.no_slack and not args.slack_webhook:
        print("\n[INFO] Slack通知: スキップ (Webhook URLが未設定)")

    print("=" * 50)

    # プレビュー表示
    print("\n--- レポートプレビュー ---\n")
    content = filepath.read_text(encoding="utf-8")
    preview_lines = content.split("\n")[:30]
    print("\n".join(preview_lines))
    if len(content.split("\n")) > 30:
        print("\n... (以下省略) ...")


if __name__ == "__main__":
    main()
