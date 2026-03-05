"""要約・スコアリングのProtocol定義"""

from __future__ import annotations

from typing import Protocol

from domain.article import Article
from domain.theme import Theme


class SummaryResult:
    """要約・スコアリング結果"""

    def __init__(
        self,
        ai_summary: str,
        importance_score: int,
        score_reason: str,
    ):
        self.ai_summary = ai_summary
        self.importance_score = importance_score
        self.score_reason = score_reason


class Summarizer(Protocol):
    """記事を要約しスコアリングする抽象

    契約:
    - summarize_articleは単一記事を要約・スコアリングする
    - importance_scoreは1-5の整数（5が最も重要）
    - API通信失敗は例外を送出してよい
    - 要約が生成できない場合も例外を送出してよい
    """

    def summarize_article(
        self,
        article: Article,
        theme: Theme,
    ) -> SummaryResult:
        """記事を要約しスコアリング

        Args:
            article: 要約対象の記事
            theme: 記事のテーマ（重要度基準を含む）

        Returns:
            要約・スコアリング結果
        """
        ...
