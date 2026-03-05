"""Slack Webhookを使用した通知"""

from __future__ import annotations

import requests

from domain.article import Article
from transformers.slack_block_formatter import SlackBlockFormatter


class SlackWebhookNotifier:
    """Slack Webhook経由で通知を送信

    Notifier Protocolを実装
    """

    def __init__(
        self,
        webhook_url: str,
        formatter: SlackBlockFormatter | None = None,
        timeout: int = 30,
    ):
        """
        Args:
            webhook_url: Slack Webhook URL
            formatter: Slack Block Kit形式へのフォーマッター
            timeout: リクエストタイムアウト（秒）
        """
        self._webhook_url = webhook_url
        self._formatter = formatter or SlackBlockFormatter()
        self._timeout = timeout

    def notify_daily(self, articles: list[Article], date_str: str) -> None:
        """日次収集結果を通知

        Args:
            articles: 収集した記事リスト
            date_str: 収集日（YYYY-MM-DD形式）

        Raises:
            Exception: 通知に失敗した場合
        """
        message = self._formatter.format_daily_notification(articles, date_str)
        self._send(message)
        print(f"[SUCCESS] Slackに日次通知を送信しました ({len(articles)}件)")

    def notify_weekly(
        self,
        articles: list[Article],
        start_date: str,
        end_date: str,
    ) -> None:
        """週次レポートを通知

        Args:
            articles: 週間の記事リスト（重要度順ソート済み）
            start_date: 期間開始日（YYYY-MM-DD形式）
            end_date: 期間終了日（YYYY-MM-DD形式）

        Raises:
            Exception: 通知に失敗した場合
        """
        message = self._formatter.format_weekly_notification(
            articles,
            start_date,
            end_date,
        )
        self._send(message)
        print(f"[SUCCESS] Slackに週次通知を送信しました ({len(articles)}件)")

    def _send(self, message: dict) -> None:
        """メッセージを送信"""
        response = requests.post(
            self._webhook_url,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=self._timeout,
        )

        if response.status_code != 200:
            raise Exception(
                f"Slack送信失敗: {response.status_code} {response.text}"
            )


class NoOpNotifier:
    """何もしないNotifier（通知をスキップする場合に使用）

    Notifier Protocolを実装
    """

    def notify_daily(self, articles: list[Article], date_str: str) -> None:
        """通知をスキップ"""
        print(f"[INFO] Slack通知スキップ（日次: {len(articles)}件）")

    def notify_weekly(
        self,
        articles: list[Article],
        start_date: str,
        end_date: str,
    ) -> None:
        """通知をスキップ"""
        print(f"[INFO] Slack通知スキップ（週次: {len(articles)}件）")
