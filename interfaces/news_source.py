"""ニュースソースのProtocol定義"""

from typing import Protocol

from domain.article import Article
from domain.theme import Theme


class NewsSource(Protocol):
    """ニュースを取得するソースの抽象

    契約:
    - fetch_articlesはテーマに基づいて記事を取得する
    - 記事が見つからない場合は空のリストを返す（例外ではない）
    - 通信失敗は例外を送出してよい（呼び出し元で捕捉）
    - 返却される記事はai_summary, importance_scoreが未設定（None）
    - 重複排除は実装側の責務
    """

    def fetch_articles(self, theme: Theme) -> list[Article]:
        """テーマに基づいて記事を取得

        Args:
            theme: 収集対象のテーマ

        Returns:
            取得した記事のリスト（ai_summary等は未設定）
        """
        ...
