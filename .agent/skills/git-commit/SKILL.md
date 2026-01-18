---
name: git-commit
description: コミット、プッシュ、ブランチ作成、PR作成を依頼されたときに使用。mainへの直接コミットは禁止。必ずブランチを作成してコミットする。
---

# Git コミット手順

## 目標
mainブランチを保護しながら、適切なブランチ運用でコミット・PRを作成する。

## 重要なルール

> ⚠️ **mainブランチへの直接コミットは禁止**
> 
> 必ず作業用ブランチを作成してからコミットしてください。

## 手順

### 1. 作業前の確認

```bash
# 現在のブランチを確認
git branch

# mainブランチにいる場合は新しいブランチを作成
git checkout -b feature/[機能名]
```

#### ブランチ命名規則

| プレフィックス | 用途 | 例 |
|---------------|------|-----|
| `feature/` | 新機能追加 | `feature/image-upload` |
| `fix/` | バグ修正 | `fix/upload-error` |
| `docs/` | ドキュメント更新 | `docs/update-readme` |
| `refactor/` | リファクタリング | `refactor/task-service` |
| `chore/` | 雑務・設定変更 | `chore/update-deps` |

### 2. walkthrough作成（コミット前に必須）

作業内容を`.gemini/steering/`にwalkthroughとして記録：

```bash
# ステアリングディレクトリ作成（既存の場合は不要）
STEERING_DIR=".gemini/steering/$(date +%s)-[開発タイトル]"
mkdir -p "${STEERING_DIR}"
```

**walkthrough.mdの必須項目:**

```markdown
# Walkthrough: [作業タイトル]

## 概要
[何を変更したかの概要]

## 変更サマリー

| ファイル | 変更内容 |
|---------|---------|
| [ファイルパス] | [変更内容] |

## 変更の詳細
[詳細な説明]

## テスト・検証
- [ ] リント: ✅
- [ ] 型チェック: ✅
- [ ] テスト: ✅

## 次のステップ
[残タスクがあれば記載]
```

### 3. コミット

```bash
# 変更をステージング
git add .

# またはファイルを個別に追加
git add [ファイルパス]

# コミット
git commit -m "[プレフィックス]: [簡潔な説明]"
```

#### コミットメッセージ規約

```
[type]: [subject]

[body（オプション）]
```

| タイプ | 説明 |
|--------|------|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `docs` | ドキュメント |
| `style` | フォーマット（コード動作に影響なし） |
| `refactor` | リファクタリング |
| `test` | テスト追加・修正 |
| `chore` | ビルド・設定変更 |

**例:**
```
feat: 画像アップロード機能を追加

- ImageUploadコンポーネントを作成
- SWRでアップロードAPIを実装
- 10MBまでのJPEG/PNGに対応
```

### 4. プッシュ

```bash
# リモートにプッシュ（初回）
git push -u origin [ブランチ名]

# 2回目以降
git push
```

### 5. PR作成

```bash
# GitHub CLIを使用
gh pr create --title "[タイトル]" --body "[説明]"

# またはGitHub Webで作成
```

## チェックリスト

コミット前に以下を確認：

- [ ] mainブランチではなく作業ブランチにいる
- [ ] walkthrough.mdを作成した
- [ ] `/pre-deploy-check`を実行してエラーがない
- [ ] コミットメッセージが規約に従っている
- [ ] 機密情報がコミットされていない

## 出力フォーマット

コミット完了時は以下の形式で報告：

```markdown
## コミット完了

- **ブランチ**: `feature/xxx`
- **コミット**: `abc1234` - [コミットメッセージ]
- **walkthrough**: `.gemini/steering/xxxxx/walkthrough.md`

### 次のアクション
- [ ] `git push` でリモートにプッシュ
- [ ] PR作成
```

## 制約

- mainブランチへの直接コミットは絶対に禁止
- コミット前にwalkthroughを必ず作成
- 機密情報（APIキー、パスワード）をコミットしない
- 大きなバイナリファイルはGit LFSを使用
