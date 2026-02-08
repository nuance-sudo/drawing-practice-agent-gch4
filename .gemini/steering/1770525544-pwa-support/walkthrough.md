# Walkthrough: pwa-support

## 概要
Webアプリに最小PWA対応を追加し、Firebase Hosting向けのヘッダー調整を行いました。

## 変更サマリー
| ファイル | 変更内容 |
|---------|---------|
| `packages/web/src/app/manifest.ts` | Web App Manifestを追加 |
| `packages/web/public/sw.js` | 最小Service Workerを追加 |
| `packages/web/src/app/layout.tsx` | PWAメタデータとSW登録を追加 |
| `packages/web/next.config.ts` | 推奨セキュリティヘッダーを追加 |
| `firebase.json` | SW/manifest配信ヘッダーを追加 |
| `README.md` | PWA確認手順を追記 |
| `.gemini/steering/1770525544-pwa-support/**` | AI-DLC成果物を移動 |

## 主要な変更点

### PWAアセット追加
manifestと最小SWを追加し、既存アイコンを流用する形でPWA化。

### セキュリティ/Hosting調整
Next.jsヘッダーとFirebase HostingヘッダーでSW/manifestの配信を安定化。

### ドキュメント更新
スマホでのインストール確認手順をREADMEに追記。

## テスト・検証
- [x] ローカル動作確認（ユーザー実施）
- [x] リント・型チェック（ユーザー実施）
- [ ] その他の検証項目

## 関連Issue
- #82

## 次のステップ
- Firebase Hostingへのデプロイ実行
