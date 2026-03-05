"""通知のProtocol定義"""

from typing import Protocol

from domain.article import Article


class Notifier(Protocol):
    """通知を送信する抽象

    契約:
    - notify_dailyは日次収集結果を通知する
    - notify_weeklyは週次レポートを通知する
    - 通知失敗は例外を送出してよい
    - 記事リストが空の場合も通知を行う（件数0として）
    """

    def notify_daily(self, articles: list[Article], date_str: str) -> None:
        """日次収集結果を通知

        Args:
            articles: 収集した記事リスト
            date_str: 収集日（YYYY-MM-DD形式）
        """
        ...

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
        """
        ...
