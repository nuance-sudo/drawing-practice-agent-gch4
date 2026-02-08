# Integration Test Instructions

## Purpose
PWA対応による統合影響は限定的なため、軽量な動作確認を実施。

## Test Scenarios

### Scenario 1: PWAアセット配信
- **Description**: `manifest.webmanifest` と `sw.js` が配信されること
- **Setup**: `npm run dev` で起動
- **Test Steps**:
  1. ブラウザで `/manifest.webmanifest` にアクセス
  2. ブラウザで `/sw.js` にアクセス
- **Expected Results**: 200で取得できる
- **Cleanup**: 開発サーバー停止

### Scenario 2: インストール可能表示
- **Description**: ブラウザの標準PWAインストール導線が表示される
- **Setup**: HTTPS環境（Firebase Hosting想定）
- **Test Steps**:
  1. スマホブラウザでアプリにアクセス
  2. インストール導線を確認
- **Expected Results**: ホーム画面に追加できる
- **Cleanup**: なし

## Setup Integration Test Environment

### 1. Start Required Services
```bash
cd packages/web
npm run dev
```

### 2. Configure Service Endpoints
```bash
# ローカル確認のみ
```

## Run Integration Tests

### 1. Execute Integration Test Suite
```bash
# 手動確認
```

### 2. Verify Service Interactions
- **Test Scenarios**: PWAアセット配信、インストール導線
- **Expected Results**: いずれも確認できる
- **Logs Location**: ブラウザ開発者ツール

### 3. Cleanup
```bash
# Ctrl+C で停止
```
