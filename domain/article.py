"""記事エンティティ"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import hashlib


@dataclass(frozen=True)
class Article:
    """ニュース記事を表すドメインエンティティ

    Attributes:
        id: 記事の一意識別子（URLから生成）
        title: 記事タイトル
        url: 記事のURL
        source: 記事のソース（メディア名）
        theme_name: 収集時のテーマ名
        collected_at: 収集日時
        published_at: 公開日時（取得できた場合）
        summary: 記事の要約（RSSから取得したもの）
        ai_summary: AIによる要約（Claude APIで生成）
        importance_score: 重要度スコア（1-5）
        score_reason: スコア判定理由
    """

    title: str
    url: str
    source: str
    theme_name: str
    collected_at: datetime
    id: str = field(default="")
    published_at: str | None = None
    summary: str | None = None
    ai_summary: str | None = None
    importance_score: int | None = None
    score_reason: str | None = None

    def __post_init__(self) -> None:
        # frozen=Trueの場合、object.__setattr__を使用
        if not self.id:
            object.__setattr__(self, "id", self._generate_id())

    def _generate_id(self) -> str:
        """URLからIDを生成"""
        return hashlib.sha256(self.url.encode()).hexdigest()[:16]

    def with_ai_analysis(
        self,
        ai_summary: str,
        importance_score: int,
        score_reason: str,
    ) -> "Article":
        """AI分析結果を付与した新しいArticleを返す"""
        return Article(
            id=self.id,
            title=self.title,
            url=self.url,
            source=self.source,
            theme_name=self.theme_name,
            collected_at=self.collected_at,
            published_at=self.published_at,
            summary=self.summary,
            ai_summary=ai_summary,
            importance_score=importance_score,
            score_reason=score_reason,
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換（JSON保存用）"""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "theme_name": self.theme_name,
            "collected_at": self.collected_at.isoformat(),
            "published_at": self.published_at,
            "summary": self.summary,
            "ai_summary": self.ai_summary,
            "importance_score": self.importance_score,
            "score_reason": self.score_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Article":
        """辞書から復元"""
        collected_at = data["collected_at"]
        if isinstance(collected_at, str):
            collected_at = datetime.fromisoformat(collected_at)

        return cls(
            id=data.get("id", ""),
            title=data["title"],
            url=data["url"],
            source=data["source"],
            theme_name=data["theme_name"],
            collected_at=collected_at,
            published_at=data.get("published_at"),
            summary=data.get("summary"),
            ai_summary=data.get("ai_summary"),
            importance_score=data.get("importance_score"),
            score_reason=data.get("score_reason"),
        )
