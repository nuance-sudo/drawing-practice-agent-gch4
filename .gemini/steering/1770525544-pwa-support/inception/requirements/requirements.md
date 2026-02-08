# Requirements

## Intent Analysis Summary
- **User request**: 現在のアプリをPWA対応する
- **Request type**: Enhancement（既存機能の拡張）
- **Scope estimate**: 複数コンポーネント（`packages/web` + `firebase.json`）
- **Complexity estimate**: Simple

## Functional Requirements
1. PWAの基本要件（Web App Manifest と Service Worker）を提供する
2. インストール可能状態にする（ブラウザ標準誘導のみ）
3. 既存アイコンを流用してPWAアイコンを設定する
4. プッシュ通知は実装しない
5. Firebase Hostingで配信する前提で最小の設定調整を行う

## Non-Functional Requirements
1. オフライン対応は不要（最小PWA）
2. セキュリティヘッダーは `next.config.ts` で推奨設定を追加
3. スマホでの確認をもって完了とする（Lighthouse必須ではない）

## User Scenarios
1. ユーザーがブラウザの標準誘導からホーム画面に追加できる
2. ホーム画面からアプリが起動できる

## Out of Scope
- オフラインキャッシュや画像キャッシュの実装
- Push通知（FCM含む）
- 新規アイコンの生成

## Dependencies / Constraints
- HostingはFirebaseを前提とする
- 既存の `public/icon.png` を利用する
