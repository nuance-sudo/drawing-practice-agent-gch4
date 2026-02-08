# Walkthrough: Fix Motif Memory Search

## 概要

エージェントがモチーフ別メモリ検索 (`search_memory_by_motif`) を正しく使用するよう修正し、成長トラッキングの精度を改善しました。

## 変更サマリー

| ファイル | 変更内容 |
|---------|---------|
| `packages/agent/dessin_coaching_agent/agent.py` | Agent定義でのインポート・設定調整 |
| `packages/agent/dessin_coaching_agent/prompts.py` | モチーフ別メモリ検索の使用を明示的に指示するプロンプト更新 |
| `packages/agent/dessin_coaching_agent/tools.py` | `analyze_dessin_image`にモチーフベースのメモリ検索ロジック追加、ログ強化 |
| `packages/agent/dessin_coaching_agent/memory_tools.py` | メモリツール関連の調整 |
| `packages/agent/dessin_coaching_agent/callbacks.py` | コールバック関連の調整 |

## 主要な変更点

### プロンプト更新（prompts.py）

エージェントが以下のフローを取るよう明示的に指示:

1. **分析実行**: `analyze_dessin_image` を実行する
2. **モチーフ確定**: 分析結果のタグからモチーフを確定する
3. **メモリ検索**: `search_memory_by_motif(motif, user_id)` を呼び出す
4. **フォールバック**: 0件なら `search_recent_memories(user_id, limit=5)` を呼び出す
5. **比較・評価**: 今回の分析結果と過去データを比較して成長を評価

### 分析ロジック改善（tools.py）

- `analyze_dessin_image` 内でモチーフ確定後、`search_memory_by_motif` を優先的に呼び出すロジックを実装
- モチーフが見つからない場合のフォールバック処理を追加
- `_extract_overall_score_from_fact` 関数を追加し、factテキストからスコア抽出をサポート
- 成長トラッキングの各ステップで詳細なログ出力を追加

### ログ強化

分析フロー全体でログを強化:
- `analyze_dessin_image_start`: 分析開始時のパラメータ
- `effective_user_id_resolved`: ユーザーID解決結果
- `gemini_request_start/done`: Gemini API呼び出し前後
- `analysis_parsed`: 分析結果パース後
- `growth_adjust_start/adjusted`: 成長スコア補正前後

## テスト・検証

- [x] ローカル動作確認
- [x] リント・型チェック
- [x] トレースログで動作確認

## 関連Issue

- #78

## 次のステップ

- デプロイ後、実際の使用ログで成長トラッキングの精度向上を確認
