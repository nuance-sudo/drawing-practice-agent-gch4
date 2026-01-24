# タスク：お手本画像URL更新失敗の修正

- [x] 現状の調査と原因特定
    - [x] `packages/functions/complete_task/main.py` のコード確認
    - [x] `packages/functions/generate_image/main.py` のコード確認
- [x] 修正案の作成
- [x] 実装
    - [x] コレクション名の修正（`tasks` -> `review_tasks`）
- [x] 検証
    - [x] ログによる確認またはデプロイ後の動作確認
- [x] デプロイ
    - [x] `deploy_functions.sh` の実行

- [x] 追加要望：画像生成リトライ処理の実装
    - [x] 実装プランの作成
    - [x] `packages/functions/generate_image/main.py` へのリトライロジック追加
- [/] 追加要望：プロンプトへの分析結果反映の確認・修正
    - [x] 分析結果（analysis）のデータ構造確認
    - [x] `packages/functions/generate_image/main.py` の `create_generation_prompt` 修正
- [x] 追加要望：ステータス更新フローの修正（お手本画像生成後に完了とする）
    - [x] 実装プランの作成
    - [x] `packages/agent/src/api/reviews.py` のステータス更新ロジック修正
- [x] 全体のデプロイ
    - [x] Cloud Functions のデプロイ
    - [x] Agent Service のデプロイ
- [x] 最終検証
