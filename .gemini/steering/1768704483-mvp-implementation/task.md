# MVP実装 タスクリスト

## 概要

お絵描き採点エージェントのMVP構築タスク一覧。

---

## ステップ1: エージェント基盤構築

- [ ] pyproject.toml 作成
- [ ] Dockerfile 作成
- [ ] src/main.py（FastAPIエントリーポイント）作成
- [ ] src/config.py（設定）作成
- [ ] src/agent.py（ADKエージェント基本構造）作成
- [ ] ローカル起動確認

---

## ステップ2: Geminiによるデッサン分析機能

- [ ] src/services/gemini_service.py 作成
- [ ] デッサン分析プロンプト作成
- [ ] src/models/task.py（タスクモデル）作成
- [ ] src/models/feedback.py（フィードバックモデル）作成
- [ ] 分析機能のテスト

---

## ステップ3: タスク管理機能

- [ ] src/services/task_service.py 作成
- [ ] Firestore連携実装
- [ ] タスクCRUD API作成
- [ ] タスク管理のテスト

---

## ステップ4: ウェブアプリ基盤構築

- [ ] Vite + React + TypeScript 初期化
- [ ] Tailwind CSS 設定
- [ ] 基本レイアウト作成
- [ ] ローカル起動確認

---

## ステップ5: 画像アップロード機能

- [ ] ImageUpload.tsx コンポーネント作成
- [ ] バックエンド: POST /reviews エンドポイント作成
- [ ] 画像アップロードのテスト

---

## ステップ6: ポーリングによるタスク監視

- [ ] SWR による API ポーリング実装
- [ ] TaskList.tsx コンポーネント作成
- [ ] FeedbackDisplay.tsx コンポーネント作成
- [ ] ポーリングのテスト

---

## ステップ7: 統合テスト・動作確認

- [ ] End-to-End フロー確認
- [ ] エラーハンドリング確認
- [ ] ドキュメント更新
