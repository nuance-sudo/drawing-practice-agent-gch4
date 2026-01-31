# 審査履歴ページング機能 + リントエラー修正

## 概要

GitHub Issue [#53](https://github.com/nuance-sudo/drawing-practice-agent-gch4/issues/53) の対応として、審査履歴に9件ずつのページング機能を実装。加えて、既存のリントエラーも修正。

## 変更内容

### ページング機能

| ファイル | 変更内容 |
|----------|----------|
| `TaskGrid.tsx` | 9件ずつ表示 + 「さらに表示」ボタン追加 |
| `page.tsx` | `key`属性でフィルタ変更時リセット |

### リントエラー修正

| ファイル | 修正内容 |
|----------|----------|
| `useRank.ts` | 未使用インポート削除 |
| `useTasks.ts` | eslint-disable追加 |
| `taskStore.ts` | 未使用インポート削除 |

## 検証結果

- ✅ リント：エラー0件
- ✅ ビルド：成功
- ✅ Firebase Hosting デプロイ完了
