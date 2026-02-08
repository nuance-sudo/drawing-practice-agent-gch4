# Build Instructions

## Prerequisites
- **Build Tool**: Node.js 20+, npm
- **Dependencies**: `packages/web` の依存関係
- **Environment Variables**: なし（PWA対応のビルドのみ）
- **System Requirements**: Node.js 20+, npm

## Build Steps

### 1. Install Dependencies
```bash
cd packages/web
npm install
```

### 2. Configure Environment
```bash
# 必要に応じて .env を設定
```

### 3. Build All Units
```bash
npm run build
```

### 4. Verify Build Success
- **Expected Output**: build成功ログが表示される
- **Build Artifacts**: `.next/`
- **Common Warnings**: 既存依存に起因する警告は許容

## Troubleshooting

### Build Fails with Dependency Errors
- **Cause**: `node_modules` 未インストール/依存の不整合
- **Solution**: `npm install` を再実行

### Build Fails with Compilation Errors
- **Cause**: TypeScript/ESLintエラー
- **Solution**: 該当ファイルを修正し再ビルド
