# Walkthrough: 画像生成リトライ機能の修正

## 概要

画像生成（お手本画像・アノテーション画像）が失敗した際に、リトライボタンが正しく表示されない問題と、リトライAPI呼び出し時の400エラーを修正した。

## 変更サマリー

| ファイル | 変更内容 |
|---------|---------|
| `packages/web/src/components/features/review/FeedbackDisplay.tsx` | `generationFailed`/`annotationFailed` の判定条件に `status === 'failed'` を追加 |
| `packages/web/src/app/(authenticated)/review/page.tsx` | `failed` ステータス時のエラー表示とリトライ導線を追加 |
| `packages/agent/src/api/reviews.py` | リトライAPIのステータスチェックで `failed` も許可 |
| `packages/functions/process_review/main.py` | annotate-image失敗時のFirestoreステータス更新ロジックを追加 |
| `packages/functions/generate_image/main.py` | テスト用強制エラーを削除、画像生成ロジックの改善 |
| `packages/functions/annotate_image/main.py` | アノテーション処理の改善 |
| `packages/agent/dessin_coaching_agent/tools.py` | ツール定義の微修正 |

## 主要な変更点

### 1. フロントエンド：リトライボタンの表示条件修正

`FeedbackDisplay.tsx` で `generationFailed` が `task.status === 'completed'` のみで判定されており、`failed` ステータスのタスクではリトライボタンが表示されなかった。条件に `|| task.status === 'failed'` を追加して修正。

### 2. バックエンドAPI：リトライエンドポイントのステータスチェック修正

`reviews.py` のリトライエンドポイントが `completed` のみ許可しており、`failed` ステータスのタスクに対してリトライを拒否（400 Bad Request）していた。`retryable_statuses` として `completed` と `failed` の両方を許可するよう修正。

### 3. Cloud Function：annotation失敗時のハンドリング追加

`process_review/main.py` で annotate-image Cloud Function の呼び出し結果が `None` の場合に、Firestore のステータスを `failed` に更新するロジックを追加（generate-image と同じパターン）。

### 4. テスト用コードの削除

`generate_image/main.py` から意図的にエラーを発生させるテストコード（`raise ImageGenerationError`）を削除。

## テスト・検証

- [x] Firestoreでタスクステータスが `failed` に更新されることを確認
- [x] フロントエンドでエラー表示とリトライボタンが表示されることを確認
- [x] Cloud Run APIサーバーのデプロイ・動作確認
- [x] Cloud Functions（generate-image, process-review）のデプロイ
- [x] リトライAPI呼び出しの400エラー解消確認

## デプロイ済みサービス

| サービス | リビジョン |
|---------|-----------|
| Cloud Run (dessin-coaching-agent) | `dessin-coaching-agent-00030-qj9` |
| Cloud Function (generate-image) | `generate-image-00017-yuw` |
| Cloud Function (process-review) | `process-review-00011-bid` |
