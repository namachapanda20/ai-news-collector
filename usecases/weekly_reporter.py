"""週次レポートユースケース"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from domain.article import Article
from interfaces.article_store import ArticleStore
from interfaces.notifier import Notifier
from transformers.markdown_formatter import MarkdownFormatter
from usecases.inputs import WeeklyReportInput


@dataclass
class WeeklyReporter:
    """週次レポートユースケース

    過去N日分の記事を集約し、重要度順にソートして
    週次サマリーを生成・通知する。
    """

    # 道具（境界層で注入）
    article_store: ArticleStore
    notifier: Notifier
    markdown_formatter: MarkdownFormatter

    def run(self, input_data: WeeklyReportInput) -> list[Article]:
        """週次レポートを生成

        Args:
            input_data: 入力パラメータ

        Returns:
            重要度順にソートされた記事リスト
        """
        start_date = input_data.start_date
        end_date = input_data.end_date

        print("=" * 50)
        print("週次レポート生成 開始")
        print(f"期間: {start_date} 〜 {end_date}")
        print("=" * 50)

        # 期間内の記事を取得
        all_articles = self.article_store.load_articles_range(start_date, end_date)
        print(f"\n[INFO] 取得記事数: {len(all_articles)}件")

        if not all_articles:
            print("[WARN] 期間内に記事がありません")
            return []

        # 重要度でソート（降順、未スコアは0扱い）
        sorted_articles = sorted(
            all_articles,
            key=lambda a: (a.importance_score or 0, a.collected_at),
            reverse=True,
        )

        # 上位N件を抽出
        top_articles = sorted_articles[: input_data.top_n]

        # 統計情報
        self._print_statistics(all_articles, top_articles)

        # Markdownレポート生成
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        self._save_markdown_report(
            sorted_articles,
            start_str,
            end_str,
            input_data.output_dir,
            input_data.top_n,
        )

        # Slack通知（上位N件のみ）
        self.notifier.notify_weekly(top_articles, start_str, end_str)

        print("=" * 50)
        print("週次レポート生成 完了")
        print("=" * 50)

        return sorted_articles

    def _print_statistics(
        self,
        all_articles: list[Article],
        top_articles: list[Article],
    ) -> None:
        """統計情報を表示"""
        # テーマ別集計
        themes: dict[str, list[Article]] = {}
        for article in all_articles:
            if article.theme_name not in themes:
                themes[article.theme_name] = []
            themes[article.theme_name].append(article)

        print("\n[INFO] テーマ別内訳:")
        for theme_name, articles in themes.items():
            avg_score = (
                sum(a.importance_score or 0 for a in articles) / len(articles)
                if articles
                else 0
            )
            print(f"  - {theme_name}: {len(articles)}件 (平均スコア: {avg_score:.1f})")

        # スコア分布
        score_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 0: 0}
        for article in all_articles:
            score = article.importance_score or 0
            score_counts[score] = score_counts.get(score, 0) + 1

        print("\n[INFO] スコア分布:")
        for score in [5, 4, 3, 2, 1, 0]:
            count = score_counts[score]
            if count > 0:
                label = f"スコア{score}" if score > 0 else "未スコア"
                bar = "█" * count
                print(f"  {label}: {count}件 {bar}")

        # 上位記事プレビュー
        print(f"\n[INFO] 上位{len(top_articles)}件:")
        for i, article in enumerate(top_articles[:5], 1):
            score = article.importance_score or 0
            print(f"  {i}. [{score}/5] {article.title[:50]}...")

    def _save_markdown_report(
        self,
        articles: list[Article],
        start_date: str,
        end_date: str,
        output_dir: Path,
        top_n: int,
    ) -> None:
        """Markdownレポートを保存"""
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"weekly_{start_date}_{end_date}.md"

        content = self.markdown_formatter.format_weekly_report(
            articles,
            start_date,
            end_date,
            top_n,
        )
        filepath.write_text(content, encoding="utf-8")

        print(f"[INFO] 週次Markdownレポートを保存: {filepath}")
