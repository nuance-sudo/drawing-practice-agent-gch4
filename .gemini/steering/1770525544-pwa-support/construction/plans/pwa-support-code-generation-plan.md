# Code Generation Plan - pwa-support

## Unit Context
- **Unit Name**: pwa-support
- **Stories Implemented**:
  - PWAの基本要件（manifest + service worker）を提供する
  - インストール可能状態にする（ブラウザ標準誘導のみ）
  - 既存アイコンを流用してPWAアイコンを設定する
  - Firebase Hostingで配信する前提で最小の設定調整を行う
- **Dependencies**: なし
- **Interfaces/Contracts**: なし
- **Database Entities**: なし

## Code Generation Steps

### Step 1: Workspace & Existing Structure Review
- [x] `aidlc-docs/aidlc-state.md` からワークスペースルートを確認
- [x] `aidlc-docs/inception/reverse-engineering/code-structure.md` を確認
- [x] `packages/web` の既存構成と `public/` を確認
- [x] 既存の `firebase.json` を確認

### Step 2: Web App Manifest
- [x] `packages/web/src/app/manifest.ts` を追加（PWAメタデータ）
- [x] `name`, `short_name`, `description`, `start_url`, `display`, `background_color`, `theme_color`, `icons` を設定
- [x] 既存アイコン（`public/icon.png` 等）を参照する設定にする

### Step 3: Service Worker (Minimal)
- [x] `packages/web/public/sw.js` を追加
- [x] push通知・オフラインキャッシュは実装しない
- [x] 最小構成（イベントリスナーのみ or 何もしないダミー）で登録可能にする

### Step 4: PWA Metadata / Icons
- [x] `packages/web/src/app/layout.tsx` を確認し、必要なら `theme-color` などを追加
- [x] `apple-touch-icon` / `icon` の配置が `public/` にあることを前提に設定

### Step 5: Security Headers
- [x] `packages/web/next.config.ts` に推奨ヘッダーを追加
- [x] `sw.js` への `Cache-Control` など必要ヘッダーを設定

### Step 6: Firebase Hosting Adjustment
- [x] `firebase.json` を確認し、`/sw.js` と `/manifest.webmanifest` の配信/ヘッダーが正しいことを保証
- [x] 必要なrewritesやheadersを最小構成で追加

### Step 7: Documentation Updates
- [x] `README.md` にPWA利用/確認手順（スマホ確認）を追記

## Deliverables
- **Modified**: `packages/web/next.config.ts`, `packages/web/src/app/layout.tsx`, `firebase.json`, `README.md`
- **Created**: `packages/web/src/app/manifest.ts`, `packages/web/public/sw.js`

## Notes
- オフライン対応は実装しない
- Push通知は実装しない
