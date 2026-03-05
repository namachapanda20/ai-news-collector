"""テーマエンティティ"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """ニュース収集テーマを表すドメインエンティティ

    Attributes:
        name: テーマ名
        priority: 優先度（1が最高）
        max_articles: 収集する最大記事数
        keywords: 検索キーワードのリスト
        importance_criteria: 重要度判定基準（AIへのプロンプト）
    """

    name: str
    priority: int
    max_articles: int
    keywords: list[str]
    importance_criteria: str

    def __post_init__(self) -> None:
        if self.priority < 1:
            raise ValueError("priorityは1以上である必要があります")
        if self.max_articles < 1:
            raise ValueError("max_articlesは1以上である必要があります")
        if not self.keywords:
            raise ValueError("keywordsは1つ以上必要です")
