# MVP実装 要求事項

## 概要

鉛筆デッサンコーチングエージェントのMVP（Minimum Viable Product）を構築する。

## GitHub Issue対応状況

| Issue | タイトル | 内容 |
|-------|----------|------|
| #1 | initial impletion | とりあえず動くまで |
| #5 | マルチモーダルエンベディング機能 | 過去に似たスケッチがないか検索 |
| #6 | ウェブアプリの追加 | React/Vite/Tailwind/Zustandでフロントエンド構築、Vercel連携 |
| #7 | タスク管理の追加 | 非同期判定、ポーリング監視 |
| #11 | エージェントの追加 | ADKを用いた最小規模お絵描きエージェント |

## MVPスコープ

### 必須機能（P0）

1. **ウェブアプリ（フロントエンド）** - Issue #6
   - React + Vite + Tailwind CSS + Zustand + SWR
   - 画像アップロード機能
   - フィードバック表示
   - タスク一覧・ポーリング監視

2. **エージェント（バックエンド）** - Issue #11
   - ADKベースのコーチングエージェント
   - Gemini API（gemini-3-flash-preview）でデッサン分析
   - フィードバック生成

3. **タスク管理** - Issue #7
   - Firestoreでタスク状態管理
   - 非同期処理のタスク化
   - SWRでポーリング監視

4. **API Server**
   - FastAPIでREST API提供
   - 画像アップロード処理
   - タスク取得API

### 補助機能（P1 - MVPの範囲外）

- お手本画像生成（gemini-2.5-flash-image）
- ランク制度
- マルチモーダルエンベディング（Issue #5 - MVPスコープに含めるか要検討）
- プッシュ通知

## 技術スタック

### フロントエンド
- React 19.x
- Vite 7.x
- TypeScript 5.x
- Tailwind CSS 4.x
- Zustand 5.x
- SWR 2.x

### バックエンド
- Python 3.12+
- FastAPI 0.115+
- Google ADK
- Firestore
- Cloud Storage
- Cloud Run

## 受け入れ条件

1. [ ] ローカル環境でフロントエンドが起動できる
2. [ ] ローカル環境でバックエンドが起動できる
3. [ ] 画像をアップロードできる
4. [ ] タスクが作成される
5. [ ] エージェントがデッサンを分析する
6. [ ] フィードバックがウェブアプリに表示される
