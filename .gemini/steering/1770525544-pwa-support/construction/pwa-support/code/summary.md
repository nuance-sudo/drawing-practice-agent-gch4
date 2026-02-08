# PWA対応 サマリー

## 変更概要
- PWA用のmanifestと最小Service Workerを追加
- PWAメタデータとSW登録をレイアウトに追加
- 推奨セキュリティヘッダーをNext.js設定に追加
- Firebase HostingでSW/manifestのヘッダーを最小調整
- READMEにPWA確認手順を追記

## 追加ファイル
- `packages/web/src/app/manifest.ts`
- `packages/web/public/sw.js`

## 変更ファイル
- `packages/web/src/app/layout.tsx`
- `packages/web/next.config.ts`
- `firebase.json`
- `README.md`
