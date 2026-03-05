"""Claude CLIを使用した要約・スコアリング"""

from __future__ import annotations

import json
import re
import subprocess

from domain.article import Article
from domain.theme import Theme
from interfaces.summarizer import SummaryResult


class ClaudeCLISummarizer:
    """Claude CLI（claudeコマンド）を使用して記事を要約・スコアリング

    Summarizer Protocolを実装
    """

    def __init__(self, timeout: int = 60):
        """
        Args:
            timeout: CLIコマンドのタイムアウト（秒）
        """
        self._timeout = timeout

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

        Raises:
            Exception: CLI呼び出しに失敗した場合
        """
        prompt = self._build_prompt(article, theme)

        try:
            # Claude CLIを呼び出し
            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )

            if result.returncode != 0:
                print(f"[WARN] Claude CLI エラー: {result.stderr}")
                return self._default_result()

            response_text = result.stdout
            return self._parse_response(response_text)

        except subprocess.TimeoutExpired:
            print(f"[WARN] Claude CLI タイムアウト ({self._timeout}秒)")
            return self._default_result()
        except FileNotFoundError:
            print("[ERROR] claudeコマンドが見つかりません。Claude CLIをインストールしてください。")
            return self._default_result()
        except Exception as e:
            print(f"[WARN] Claude CLI 呼び出しエラー: {e}")
            return self._default_result()

    def _build_prompt(self, article: Article, theme: Theme) -> str:
        """プロンプトを構築"""
        return f"""以下のニュース記事を分析してください。

## 記事情報
- タイトル: {article.title}
- ソース: {article.source}
- URL: {article.url}
- 元の要約: {article.summary or "なし"}

## テーマ: {theme.name}

## 重要度判定基準
{theme.importance_criteria}

## タスク
1. この記事を日本語で2-3文で要約してください
2. 上記の重要度判定基準に基づいて、1-5のスコアを付けてください
3. スコアの理由を1文で説明してください

## 出力形式（JSON）
以下のJSON形式のみで出力してください（説明文は不要）:
```json
{{
  "summary": "記事の要約（2-3文）",
  "score": 3,
  "reason": "スコアの理由（1文）"
}}
```
"""

    def _parse_response(self, response_text: str) -> SummaryResult:
        """CLIレスポンスをパース"""
        # JSONブロックを抽出
        json_match = re.search(r"```json\s*\n?(.*?)\n?```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # ```なしでJSONが直接返された場合、JSONっぽい部分を探す
            json_match = re.search(r'\{[^{}]*"summary"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text

        try:
            data = json.loads(json_str)
            score = int(data.get("score", 3))
            # スコアを1-5に正規化
            score = max(1, min(5, score))

            return SummaryResult(
                ai_summary=data.get("summary", "要約を取得できませんでした"),
                importance_score=score,
                score_reason=data.get("reason", ""),
            )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[WARN] レスポンスのパースに失敗: {e}")
            return self._default_result()

    def _default_result(self) -> SummaryResult:
        """デフォルト結果を返す"""
        return SummaryResult(
            ai_summary="要約の取得に失敗しました",
            importance_score=3,
            score_reason="パースエラー",
        )


class NoOpSummarizer:
    """何もしないSummarizer（AI要約をスキップする場合に使用）

    Summarizer Protocolを実装
    """

    def summarize_article(
        self,
        article: Article,
        theme: Theme,
    ) -> SummaryResult:
        """デフォルト値を返す"""
        return SummaryResult(
            ai_summary=article.summary or "",
            importance_score=3,
            score_reason="AI要約スキップ",
        )
