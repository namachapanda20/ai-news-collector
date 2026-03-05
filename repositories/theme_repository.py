"""テーマ設定を読み込むRepository"""

from __future__ import annotations

from pathlib import Path

import yaml

from domain.theme import Theme


class ThemeRepository:
    """YAMLファイルからテーマ設定を読み込むRepository"""

    def __init__(self, config_path: Path):
        """
        Args:
            config_path: themes.yamlのパス
        """
        self._config_path = config_path

    def load_all(self) -> list[Theme]:
        """全テーマを読み込み

        Returns:
            テーマのリスト（priority順にソート）

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            yaml.YAMLError: YAML解析エラー
            ValueError: テーマ設定が不正な場合
        """
        if not self._config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self._config_path}")

        with open(self._config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config or "themes" not in config:
            raise ValueError("themes設定が見つかりません")

        themes = []
        for theme_data in config["themes"]:
            theme = Theme(
                name=theme_data["name"],
                priority=theme_data.get("priority", 99),
                max_articles=theme_data.get("max_articles", 10),
                keywords=theme_data.get("keywords", []),
                importance_criteria=theme_data.get("importance_criteria", ""),
            )
            themes.append(theme)

        # priorityで昇順ソート（1が最高優先）
        themes.sort(key=lambda t: t.priority)

        return themes

    def load_by_name(self, name: str) -> Theme | None:
        """名前でテーマを取得

        Args:
            name: テーマ名

        Returns:
            テーマ（見つからない場合はNone）
        """
        themes = self.load_all()
        for theme in themes:
            if theme.name == name:
                return theme
        return None
