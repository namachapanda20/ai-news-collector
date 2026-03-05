"""日次ニュース収集ユースケース"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from domain.article import Article
from domain.theme import Theme
from interfaces.article_store import ArticleStore
from interfaces.news_source import NewsSource
from interfaces.notifier import Notifier
from interfaces.summarizer import Summarizer
from transformers.markdown_formatter import MarkdownFormatter
from usecases.inputs import DailyCollectionInput


@dataclass
class DailyCollector:
    """日次ニュース収集ユースケース

    テーマごとにニュースを収集し、AI要約・スコアリングを行い、
    JSON形式で蓄積、Markdown出力、Slack通知を行う。
    """

    # 道具（境界層で注入）
    news_source: NewsSource
    summarizer: Summarizer
    article_store: ArticleStore
    notifier: Notifier
    markdown_formatter: MarkdownFormatter
    themes: list[Theme]

    def run(self, input_data: DailyCollectionInput) -> list[Article]:
        """日次収集を実行

        Args:
            input_data: 入力パラメータ

        Returns:
            収集・処理した記事リスト
        """
        print("=" * 50)
        print("日次ニュース収集 開始")
        print(f"対象日: {input_data.target_date}")
        print(f"AI要約: {'有効' if input_data.enable_ai_summary else '無効'}")
        print("=" * 50)

        all_articles: list[Article] = []

        # テーマごとにニュースを収集
        for theme in self.themes:
            print(f"\n[INFO] テーマ '{theme.name}' を収集中...")
            articles = self._collect_for_theme(theme, input_data.enable_ai_summary)
            all_articles.extend(articles)
            print(f"[INFO] テーマ '{theme.name}': {len(articles)}件")

        print(f"\n[INFO] 総収集件数: {len(all_articles)}件")

        # JSON保存
        self.article_store.save_articles(all_articles, input_data.target_date)

        # Markdownレポート生成
        date_str = input_data.target_date.isoformat()
        self._save_markdown_report(all_articles, date_str, input_data.output_dir)

        # Slack通知
        self.notifier.notify_daily(all_articles, date_str)

        print("=" * 50)
        print("日次ニュース収集 完了")
        print("=" * 50)

        return all_articles

    def _collect_for_theme(
        self,
        theme: Theme,
        enable_ai_summary: bool,
    ) -> list[Article]:
        """テーマの記事を収集・処理"""
        # ニュース取得
        articles = self.news_source.fetch_articles(theme)

        if not enable_ai_summary:
            return articles

        # AI要約・スコアリング
        processed_articles: list[Article] = []
        for article in articles:
            try:
                result = self.summarizer.summarize_article(article, theme)
                processed_article = article.with_ai_analysis(
                    ai_summary=result.ai_summary,
                    importance_score=result.importance_score,
                    score_reason=result.score_reason,
                )
                processed_articles.append(processed_article)
                print(f"  - [{result.importance_score}/5] {article.title[:40]}...")
            except Exception as e:
                print(f"  - [ERROR] 要約失敗: {article.title[:40]}... ({e})")
                processed_articles.append(article)

        return processed_articles

    def _save_markdown_report(
        self,
        articles: list[Article],
        date_str: str,
        output_dir: Path,
    ) -> None:
        """Markdownレポートを保存"""
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{date_str}.md"

        content = self.markdown_formatter.format_daily_report(articles, date_str)
        filepath.write_text(content, encoding="utf-8")

        print(f"[INFO] Markdownレポートを保存: {filepath}")
