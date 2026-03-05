"""ユースケース入力モデル"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class DailyCollectionInput:
    """日次収集ユースケースの入力

    Attributes:
        target_date: 収集対象日
        output_dir: Markdownレポートの出力先ディレクトリ
        enable_ai_summary: AI要約を有効にするか
    """

    target_date: date
    output_dir: Path
    enable_ai_summary: bool = True


@dataclass(frozen=True)
class WeeklyReportInput:
    """週次レポートユースケースの入力

    Attributes:
        end_date: 期間終了日
        days_back: 遡る日数（デフォルト7日）
        output_dir: Markdownレポートの出力先ディレクトリ
        top_n: 上位N件を抽出
    """

    end_date: date
    days_back: int = 7
    output_dir: Path = Path("output/weekly")
    top_n: int = 20

    @property
    def start_date(self) -> date:
        """期間開始日を計算"""
        from datetime import timedelta
        return self.end_date - timedelta(days=self.days_back - 1)
