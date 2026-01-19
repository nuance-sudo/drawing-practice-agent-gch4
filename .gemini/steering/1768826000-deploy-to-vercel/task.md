# タスク: Firebase Authentication セットアップ

## 依存関係の更新
- [x] `packages/web`: `npm install firebase`
- [x] `packages/agent`: `pyproject.toml` に `firebase-admin` 追加
- [x] `packages/web`: Cleanup `next-auth`, `jose` dependencies

## Firebase設定 (Setup)
- [x] Project Creation (`drawing-practice-agent`) [Manual/User]
- [x] Create Web App via MCP
- [x] Get `firebaseConfig` via MCP
- [x] Update `.env.local` via Agent
- [x] GitHub Provider Setup in Console (Client ID/Secret)

## フロントエンド実装 (`packages/web`)
- [x] `src/lib/firebase.ts` 作成
- [x] `src/stores/auth-store.ts` 作成
- [x] ログインUIの実装 (`LoginButton`, `AuthProvider`)
- [x] Cleanup Legacy Auth code (`api/auth`, `lib/auth.ts`)

## バックエンド実装 (`packages/agent`)
- [x] `firebase-admin` 初期化処理
- [x] `dependencies.py` 更新

## デプロイ (Target: Firebase Hosting)
- [x] Initialize Firebase Hosting (`firebase init hosting`)
- [x] Build and Deploy (`firebase deploy --only hosting`)
- [x] Verify Hosting URL (`https://drawing-practice-agent.web.app`)
- [x] Cleanup Vercel artifacts

## 検証
- [x] GitHub Login (Verified)
