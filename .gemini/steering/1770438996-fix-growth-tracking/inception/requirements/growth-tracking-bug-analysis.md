# 成長トラッキング機能 - 現状分析

## 概要

本ドキュメントは、成長トラッキング機能の現状と問題点、および解決策を説明します。

---

## 現在の問題

### 症状

デッサン分析結果の成長トラッキングが常に「初回提出」と判定される。

```json
{
  "growth": {
    "is_first_submission": true,
    "comparison_note": "同一モチーフの過去データがまだありません"
  }
}
```

### 根本原因

**2つの問題が重複:**

| # | 問題 | 原因 |
|---|------|------|
| 1 | スコープ不一致 | 古いAgent Engineでは`scope={user_id, session_id}`で保存しているが、検索時は`{user_id}`のみで検索 |
| 2 | モチーフフィルタなし | 分析前にメモリ取得するため、モチーフが不明でフィルタできない |

---

## Memory Bank APIの仕様

### スコープのexact match

Memory Bank APIは**スコープをexact match**で検索します。

```
保存時: scope = {"user_id": "ABC", "session_id": "123"}
検索時: scope = {"user_id": "ABC"}
→ 一致しない（session_idの有無が異なる）
```

### 参考ドキュメント

- [メモリを生成する](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories?hl=ja)
- [メモリを取得する](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/fetch-memories?hl=ja)

---

## 解決策

### 戦略

| 項目 | 設定 | 理由 |
|------|------|------|
| **スコープ** | `{"user_id": "..."}` のみ | 同一ユーザーの全メモリを取得可能に |
| **フィルタ** | メタデータの`motif`でフィルタ | モチーフ別の成長比較を可能に |

### 処理フロー変更

**Before（現在）:**
```
1. メモリ取得（フィルタなし）← モチーフ不明
2. 画像分析（成長情報含む）
3. メモリ保存
```

**After（新）:**
```
1. 画像分析（成長情報なし）
2. 分析結果からモチーフ取得
3. モチーフでフィルタしたメモリ取得  ← 正しいフィルタ
4. 成長スコア補正
5. メモリ保存
```

---

## 必要な作業

### 1. Agent Engine再デプロイ（進行中）

最新コードを反映し、scopeに`session_id`を含めない。

```bash
uv run adk deploy agent_engine \
  --project=drawing-practice-agent \
  --region=us-central1 \
  --agent_engine_id={AGENT_ENGINE_ID} \
  ...
```

### 2. tools.py修正

- 分析前のメモリ取得を削除
- 分析後に`search_memory_by_motif`でモチーフ別メモリ取得
- 取得したメモリで`growth`セクションを補正

---

## 関連コード

| ファイル | 役割 |
|----------|------|
| `callbacks.py` | メモリ保存（scope設定） |
| `memory_tools.py` | メモリ検索（フィルタ） |
| `tools.py` | 画像分析（成長トラッキング） |

---

## 検証計画

1. 新しいレビューを投稿（例: りんご）
2. Memory Bankで`motif=りんご`のメモリが保存されることを確認
3. 同じモチーフで2回目のレビューを投稿
4. 成長トラッキングが過去データを参照していることを確認
