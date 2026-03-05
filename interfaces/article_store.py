"""記事蓄積のProtocol定義"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from domain.article import Article


class ArticleStore(Protocol):
    """記事を蓄積・取得する抽象

    契約:
    - save_articlesは指定日の記事を保存する
    - 同一日に複数回保存した場合は上書き
    - load_articlesは指定日の記事を取得する
    - 指定日のデータがない場合は空のリストを返す（例外ではない）
    - load_articles_rangeは期間内の全記事を取得する
    - ストレージアクセス失敗は例外を送出してよい
    """

    def save_articles(self, articles: list[Article], target_date: date) -> None:
        """記事を保存

        Args:
            articles: 保存する記事リスト
            target_date: 保存対象の日付
        """
        ...

    def load_articles(self, target_date: date) -> list[Article]:
        """指定日の記事を取得

        Args:
            target_date: 取得対象の日付

        Returns:
            記事リスト（データがない場合は空リスト）
        """
        ...

    def load_articles_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[Article]:
        """期間内の記事を取得

        Args:
            start_date: 期間開始日（含む）
            end_date: 期間終了日（含む）

        Returns:
            期間内の全記事リスト
        """
        ...
