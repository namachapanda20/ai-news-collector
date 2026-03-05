"""Interfaces層: 抽象（Protocol）の定義"""

from interfaces.news_source import NewsSource
from interfaces.summarizer import Summarizer
from interfaces.notifier import Notifier
from interfaces.article_store import ArticleStore

__all__ = ["NewsSource", "Summarizer", "Notifier", "ArticleStore"]
