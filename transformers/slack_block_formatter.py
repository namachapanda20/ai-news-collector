"""Slack Block Kit形式へのフォーマット変換"""

from __future__ import annotations

from domain.article import Article


class SlackBlockFormatter:
    """記事をSlack Block Kit形式に変換"""

    def __init__(self, max_title_length: int = 80):
        """
        Args:
            max_title_length: タイトルの最大文字数
        """
        self._max_title_length = max_title_length

    def format_daily_notification(
        self,
        articles: list[Article],
        date_str: str,
    ) -> dict:
        """日次通知用のBlock Kitメッセージを生成

        Args:
            articles: 記事リスト
            date_str: 日付（YYYY-MM-DD形式）

        Returns:
            Slack Block Kit形式の辞書
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"AIニュース ({date_str})",
                    "emoji": True,
                },
            },
            {"type": "divider"},
        ]

        if not articles:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "本日は該当する記事が見つかりませんでした。",
                },
            })
        else:
            # テーマごとにグループ化
            themes = self._group_by_theme(articles)

            for theme_name, theme_articles in themes.items():
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{theme_name}*",
                    },
                })

                # 重要度順にソートして上位3件
                sorted_articles = sorted(
                    theme_articles,
                    key=lambda a: a.importance_score or 0,
                    reverse=True,
                )[:3]

                for article in sorted_articles:
                    blocks.append(self._format_article_block(article))

        # フッター
        blocks.extend([
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"収集件数: {len(articles)}件 | 自動収集",
                    }
                ],
            },
        ])

        return {"blocks": blocks}

    def format_weekly_notification(
        self,
        articles: list[Article],
        start_date: str,
        end_date: str,
        top_n: int = 10,
    ) -> dict:
        """週次通知用のBlock Kitメッセージを生成

        Args:
            articles: 記事リスト（重要度順ソート済み想定）
            start_date: 期間開始日
            end_date: 期間終了日
            top_n: 上位N件を表示

        Returns:
            Slack Block Kit形式の辞書
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"週間AIニュースサマリー",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*期間*: {start_date} 〜 {end_date}\n*総記事数*: {len(articles)}件",
                },
            },
            {"type": "divider"},
        ]

        if not articles:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "該当する記事が見つかりませんでした。",
                },
            })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*重要度上位{top_n}件*",
                },
            })

            # 上位N件を表示
            for i, article in enumerate(articles[:top_n], 1):
                score = article.importance_score or 0
                score_indicator = "🔴" if score >= 4 else "🟡" if score >= 3 else "⚪"

                title = self._truncate(article.title)
                text = f"{i}. {score_indicator} <{article.url}|{title}>\n"
                text += f"   _{article.theme_name}_ | スコア: {score}/5"

                if article.ai_summary:
                    summary = self._truncate(article.ai_summary, 100)
                    text += f"\n   > {summary}"

                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text,
                    },
                })

        # フッター
        blocks.extend([
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "週次自動レポート | AIニュース収集システム",
                    }
                ],
            },
        ])

        return {"blocks": blocks}

    def _format_article_block(self, article: Article) -> dict:
        """単一記事のブロックを生成"""
        score = article.importance_score or 0
        score_indicator = "🔴" if score >= 4 else "🟡" if score >= 3 else "⚪"

        title = self._truncate(article.title)
        text = f"{score_indicator} <{article.url}|{title}>\n"
        text += f"  _{article.source}_ | スコア: {score}/5"

        if article.ai_summary:
            summary = self._truncate(article.ai_summary, 80)
            text += f"\n  > {summary}"

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        }

    def _truncate(self, text: str, max_length: int | None = None) -> str:
        """テキストを指定の長さに切り詰める"""
        max_len = max_length or self._max_title_length
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def _group_by_theme(self, articles: list[Article]) -> dict[str, list[Article]]:
        """テーマごとにグループ化"""
        themes: dict[str, list[Article]] = {}
        for article in articles:
            if article.theme_name not in themes:
                themes[article.theme_name] = []
            themes[article.theme_name].append(article)
        return themes
