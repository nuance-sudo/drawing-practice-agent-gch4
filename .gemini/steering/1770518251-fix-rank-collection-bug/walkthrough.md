# Walkthrough: Issue #79 ランクコレクションバグ修正

## 概要

Cloud Function `process_review/main.py`がユーザーランクを取得・更新する際に間違ったFirestoreコレクション（`user_ranks`）を参照していたバグを修正。正しいコレクション（`users`）を使用するように変更。

## 変更サマリー

| ファイル | 変更内容 |
|---------|---------|
| `packages/functions/process_review/main.py` | `get_user_rank`、`update_user_rank`を修正、`_rank_value_to_label`を追加 |

## 主要な変更点

### バグの根本原因

Cloud Functionが以下の誤りを持っていた：
- **コレクション**: `user_ranks` (誤) → `users` (正)
- **フィールド**: `current_rank` (文字列) → `rank` (整数値)
- **変換**: 整数→ラベル変換なし

### 修正内容

1. **`_rank_value_to_label`関数追加**: 整数値（1-15）をラベル（"10級"〜"師範"）に変換
2. **`get_user_rank`関数修正**: `users`コレクションの`rank`フィールドを参照
3. **`update_user_rank`関数修正**: 正しいデータ構造で更新、ランク昇格ロジック追加

## テスト・検証

- [x] Python構文チェック
- [ ] Cloud Functionデプロイ後の動作確認

## 関連Issue

- #79

## 次のステップ

- Cloud Functionをデプロイして動作確認
- `/git-commit`でコミット・PR作成
