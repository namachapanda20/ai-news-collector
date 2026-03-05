"""Google News RSSからニュースを取得するSource"""

from __future__ import annotations

import html
import time
from datetime import datetime
from urllib.parse import quote

import feedparser
from bs4 import BeautifulSoup
from googlenewsdecoder import new_decoderv1

from domain.article import Article
from domain.theme import Theme


class GoogleNewsRSSSource:
    """Google News RSSフィードからニュースを取得

    NewsSource Protocolを実装
    """

    def __init__(
        self,
        rate_limit_delay: float = 0.5,
        num_results_per_keyword: int = 3,
    ):
        """
        Args:
            rate_limit_delay: キーワード間のリクエスト間隔（秒）
            num_results_per_keyword: キーワードあたりの取得件数
        """
        self._rate_limit_delay = rate_limit_delay
        self._num_results_per_keyword = num_results_per_keyword
        self._collected_urls: set[str] = set()

    def fetch_articles(self, theme: Theme) -> list[Article]:
        """テーマに基づいて記事を取得

        Args:
            theme: 収集対象のテーマ

        Returns:
            取得した記事のリスト
        """
        articles: list[Article] = []

        for keyword in theme.keywords:
            keyword_articles = self._fetch_by_keyword(keyword, theme.name)
            articles.extend(keyword_articles)

            # レート制限対策
            if self._rate_limit_delay > 0:
                time.sleep(self._rate_limit_delay)

            # 最大件数に達したら終了
            if len(articles) >= theme.max_articles:
                break

        # 最大件数でカット
        return articles[: theme.max_articles]

    def _fetch_by_keyword(
        self,
        keyword: str,
        theme_name: str,
    ) -> list[Article]:
        """キーワードで記事を取得"""
        encoded_query = quote(keyword)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"

        articles: list[Article] = []

        try:
            feed = feedparser.parse(url)

            for entry in feed.entries[: self._num_results_per_keyword]:
                # 重複チェック
                if entry.link in self._collected_urls:
                    continue

                # 元記事URLを取得
                original_url = self._resolve_original_url(entry.link)
                if original_url in self._collected_urls:
                    continue

                # 要約を取得（HTMLタグ除去）
                summary = self._extract_summary(entry)

                # 記事を作成
                article = Article(
                    title=html.unescape(entry.title),
                    url=original_url,
                    source=entry.get("source", {}).get("title", "Google News"),
                    theme_name=theme_name,
                    collected_at=datetime.now(),
                    published_at=getattr(entry, "published", None),
                    summary=summary,
                )

                articles.append(article)
                self._collected_urls.add(original_url)

        except Exception as e:
            print(f"[ERROR] Google News取得エラー ({keyword}): {e}")

        return articles

    def _resolve_original_url(self, google_news_url: str) -> str:
        """Google Newsのリダイレクトリンクから元記事のURLを取得"""
        try:
            result = new_decoderv1(google_news_url)
            if result and result.get("decoded_url"):
                return result["decoded_url"]
            return google_news_url
        except Exception as e:
            print(f"[WARN] URL解決失敗 ({google_news_url[:50]}...): {e}")
            return google_news_url

    def _extract_summary(self, entry) -> str:
        """RSSエントリから要約を抽出"""
        if not hasattr(entry, "summary"):
            return ""

        soup = BeautifulSoup(entry.summary, "html.parser")
        text = soup.get_text(strip=True)
        return text[:200] if text else ""

    def reset_collected_urls(self) -> None:
        """収集済みURL一覧をリセット（新しい収集セッション開始時に使用）"""
        self._collected_urls.clear()
