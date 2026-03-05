"""JSON形式で記事を蓄積するStore"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from domain.article import Article


class JsonFileStore:
    """JSON形式で記事を蓄積

    ArticleStore Protocolを実装
    ファイル形式: data/articles/YYYY-MM-DD.json
    """

    def __init__(self, data_dir: Path):
        """
        Args:
            data_dir: データ保存ディレクトリ（例: data/articles）
        """
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def save_articles(self, articles: list[Article], target_date: date) -> None:
        """記事を保存

        Args:
            articles: 保存する記事リスト
            target_date: 保存対象の日付
        """
        filepath = self._get_filepath(target_date)

        data = {
            "date": target_date.isoformat(),
            "count": len(articles),
            "articles": [article.to_dict() for article in articles],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[INFO] 記事を保存しました: {filepath} ({len(articles)}件)")

    def load_articles(self, target_date: date) -> list[Article]:
        """指定日の記事を取得

        Args:
            target_date: 取得対象の日付

        Returns:
            記事リスト（データがない場合は空リスト）
        """
        filepath = self._get_filepath(target_date)

        if not filepath.exists():
            return []

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            articles = [Article.from_dict(a) for a in data.get("articles", [])]
            return articles

        except (json.JSONDecodeError, KeyError) as e:
            print(f"[WARN] JSONファイル読み込みエラー ({filepath}): {e}")
            return []

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
        all_articles: list[Article] = []
        current_date = start_date

        while current_date <= end_date:
            day_articles = self.load_articles(current_date)
            all_articles.extend(day_articles)
            current_date += timedelta(days=1)

        return all_articles

    def _get_filepath(self, target_date: date) -> Path:
        """日付からファイルパスを生成"""
        return self._data_dir / f"{target_date.isoformat()}.json"

    def list_available_dates(self) -> list[date]:
        """保存されているデータの日付一覧を取得

        Returns:
            日付のリスト（昇順）
        """
        dates: list[date] = []

        for filepath in self._data_dir.glob("*.json"):
            try:
                date_str = filepath.stem  # YYYY-MM-DD
                d = date.fromisoformat(date_str)
                dates.append(d)
            except ValueError:
                continue

        dates.sort()
        return dates
