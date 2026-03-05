"""Markdown形式へのフォーマット変換"""

from __future__ import annotations

from datetime import datetime

from domain.article import Article


class MarkdownFormatter:
    """記事をMarkdown形式に変換"""

    def format_daily_report(
        self,
        articles: list[Article],
        date_str: str,
    ) -> str:
        """日次レポートをMarkdown形式で生成

        Args:
            articles: 記事リスト
            date_str: 日付（YYYY-MM-DD形式）

        Returns:
            Markdown文字列
        """
        lines = [
            f"# AIニュース収集レポート ({date_str})",
            "",
            f"収集日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"収集件数: {len(articles)}件",
            "",
            "---",
            "",
        ]

        if not articles:
            lines.append("該当する記事が見つかりませんでした。")
            return "\n".join(lines)

        # テーマごとにグループ化
        themes = self._group_by_theme(articles)

        for theme_name, theme_articles in themes.items():
            lines.append(f"## {theme_name}")
            lines.append("")

            # 重要度順にソート
            sorted_articles = sorted(
                theme_articles,
                key=lambda a: a.importance_score or 0,
                reverse=True,
            )

            for article in sorted_articles:
                lines.extend(self._format_article(article))

        lines.extend([
            "---",
            "",
            "*このレポートはAIニュース収集システムにより自動生成されました。*",
        ])

        return "\n".join(lines)

    def format_weekly_report(
        self,
        articles: list[Article],
        start_date: str,
        end_date: str,
        top_n: int = 20,
    ) -> str:
        """週次レポートをMarkdown形式で生成

        Args:
            articles: 記事リスト（重要度順ソート済み想定）
            start_date: 期間開始日（YYYY-MM-DD形式）
            end_date: 期間終了日（YYYY-MM-DD形式）
            top_n: 上位N件を表示

        Returns:
            Markdown文字列
        """
        lines = [
            f"# 週間AIニュースサマリー",
            f"## 期間: {start_date} 〜 {end_date}",
            "",
            f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"総記事数: {len(articles)}件（上位{top_n}件を表示）",
            "",
            "---",
            "",
            "## 重要度上位の記事",
            "",
        ]

        if not articles:
            lines.append("該当する記事が見つかりませんでした。")
            return "\n".join(lines)

        # 上位N件を表示
        top_articles = articles[:top_n]

        for i, article in enumerate(top_articles, 1):
            score = article.importance_score or 0
            score_stars = "★" * score + "☆" * (5 - score)

            lines.append(f"### {i}. {article.title}")
            lines.append("")
            lines.append(f"**重要度**: {score_stars} ({score}/5)")
            lines.append(f"**テーマ**: {article.theme_name}")
            lines.append(f"**ソース**: {article.source}")
            lines.append(f"**URL**: {article.url}")
            lines.append("")

            if article.ai_summary:
                lines.append(f"> {article.ai_summary}")
                lines.append("")

            if article.score_reason:
                lines.append(f"*スコア理由: {article.score_reason}*")
                lines.append("")

        lines.extend([
            "---",
            "",
            "## テーマ別内訳",
            "",
        ])

        # テーマ別の件数
        themes = self._group_by_theme(articles)
        for theme_name, theme_articles in themes.items():
            avg_score = (
                sum(a.importance_score or 0 for a in theme_articles)
                / len(theme_articles)
                if theme_articles
                else 0
            )
            lines.append(f"- **{theme_name}**: {len(theme_articles)}件 (平均スコア: {avg_score:.1f})")

        lines.extend([
            "",
            "---",
            "",
            "*このレポートはAIニュース収集システムにより自動生成されました。*",
        ])

        return "\n".join(lines)

    def _format_article(self, article: Article) -> list[str]:
        """単一記事をフォーマット"""
        lines = []
        score = article.importance_score or 0
        score_stars = "★" * score + "☆" * (5 - score)

        lines.append(f"### {article.title}")
        lines.append("")
        lines.append(f"- **URL**: {article.url}")
        lines.append(f"- **ソース**: {article.source}")
        lines.append(f"- **重要度**: {score_stars} ({score}/5)")

        if article.published_at:
            lines.append(f"- **公開日**: {article.published_at}")

        lines.append("")

        if article.ai_summary:
            lines.append(f"> {article.ai_summary}")
            lines.append("")

        if article.score_reason:
            lines.append(f"*スコア理由: {article.score_reason}*")
            lines.append("")

        return lines

    def _group_by_theme(self, articles: list[Article]) -> dict[str, list[Article]]:
        """テーマごとにグループ化"""
        themes: dict[str, list[Article]] = {}
        for article in articles:
            if article.theme_name not in themes:
                themes[article.theme_name] = []
            themes[article.theme_name].append(article)
        return themes
