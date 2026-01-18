---
name: git-commit
description: コミット、プッシュ、ブランチ作成、PR作成、マージを依頼されたときに使用。mainへの直接コミットは禁止。必ずブランチを作成してコミットする。
---

# Git コミット・PR・マージ手順

## 目標
mainブランチを保護しながら、適切なブランチ運用でコミット・PR作成・マージを行う。

## 重要なルール

> ⚠️ **mainブランチへの直接コミットは禁止**
> 
> 必ず作業用ブランチを作成してからコミットしてください。

---

## 手順

### 1. 作業用ブランチの作成

```bash
# 現在のブランチを確認
git branch

# mainブランチから新しいブランチを作成
git checkout main
git pull origin main
git checkout -b feature/[機能名]
```

#### ブランチ命名規則

| プレフィックス | 用途 | 例 |
|---------------|------|-----|
| `feature/` | 新機能追加 | `feature/step1-agent-foundation` |
| `fix/` | バグ修正 | `fix/upload-error` |
| `docs/` | ドキュメント更新 | `docs/update-readme` |
| `refactor/` | リファクタリング | `refactor/task-service` |
| `chore/` | 雑務・設定変更 | `chore/update-deps` |

### 2. walkthrough作成（コミット前に必須）

ステアリングディレクトリにwalkthroughを作成：

```markdown
# Walkthrough: [作業タイトル]

## 概要
[何を変更したかの概要]

## 変更サマリー

| ファイル | 変更内容 |
|---------|---------| 
| [ファイルパス] | [変更内容] |

## テスト・検証
- [x] ローカル動作確認
- [x] リント・型チェック

## 関連Issue
- #XX

## 次のステップ
[残タスクがあれば記載]
```

### 3. コミット

```bash
# 変更をステージング
git add .

# コミット（関連Issueを参照）
git commit -m "[type]: [subject]

[body]

Closes #XX"
```

#### コミットメッセージ規約

| タイプ | 説明 |
|--------|------|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `docs` | ドキュメント |
| `style` | フォーマット |
| `refactor` | リファクタリング |
| `test` | テスト追加・修正 |
| `chore` | ビルド・設定変更 |

### 4. プッシュ

```bash
# リモートにプッシュ
git push -u origin [ブランチ名]
```

### 5. PR作成

GitHub MCP Serverを使用してPRを作成：

```python
# MCP Tool使用
mcp_github-mcp-server_create_pull_request(
    owner="nuance-sudo",
    repo="drawing-practice-agent-gch4",
    title="[type]: [subject]",
    body="## 概要\n...\n\nCloses #XX",
    head="feature/xxx",
    base="main"
)
```

### 6. 関連Issueの更新

PRを作成したら、関連Issueのタスクを完了状態に更新：

```python
# Issue本文のタスクを完了に更新
mcp_github-mcp-server_issue_write(
    method="update",
    owner="nuance-sudo",
    repo="drawing-practice-agent-gch4",
    issue_number=XX,
    body="## タスク\n- [x] 完了したタスク\n..."
)
```

### 7. PRマージ

レビュー後、PRをマージ：

```python
mcp_github-mcp-server_merge_pull_request(
    owner="nuance-sudo",
    repo="drawing-practice-agent-gch4",
    pullNumber=XX,
    merge_method="squash",
    commit_title="[type]: [subject] (#XX)",
    commit_message="変更内容のサマリー"
)
```

### 8. Issueクローズ

マージ後、関連Issueをクローズ：

```python
mcp_github-mcp-server_issue_write(
    method="update",
    owner="nuance-sudo",
    repo="drawing-practice-agent-gch4",
    issue_number=XX,
    state="closed",
    state_reason="completed"
)
```

### 9. 次のブランチ作成

マージ後、mainを更新して次のブランチを作成：

```bash
git checkout main
git pull origin main
git checkout -b feature/[次の機能名]
```

---

## 完全なワークフロー例

```bash
# 1. ブランチ作成
git checkout main && git pull origin main
git checkout -b feature/step1-agent-foundation

# 2. 開発作業...

# 3. コミット
git add .
git commit -m "feat: Step 1 エージェント基盤構築

- packages/agent/ にPython/FastAPI/ADK基盤を作成
- pyproject.toml で最新依存関係を定義

Closes #13"

# 4. プッシュ
git push -u origin feature/step1-agent-foundation

# 5. PR作成 → マージ → Issue更新（MCPツール使用）

# 6. 次のブランチへ
git checkout main && git pull origin main
git checkout -b feature/step2-gemini-analysis
```

---

## チェックリスト

コミット前：
- [ ] mainブランチではなく作業ブランチにいる
- [ ] walkthrough.mdを作成した
- [ ] コミットメッセージが規約に従っている
- [ ] 機密情報がコミットされていない

PR作成後：
- [ ] 関連Issueのタスクを更新した
- [ ] PRの説明に変更内容を記載した

マージ後：
- [ ] 関連Issueをクローズした
- [ ] mainを最新化して次のブランチを作成した

---

## 出力フォーマット

```markdown
## ✅ コミット・PR作成完了

### ブランチ
`feature/xxx`

### コミット
`abc1234` - [コミットメッセージ]

### PR
[#XX タイトル](URL)

### Issue更新
[#XX](URL) のタスクを完了状態に更新
```

---

## 制約

- mainブランチへの直接コミットは絶対に禁止
- コミット前にwalkthroughを必ず作成
- 機密情報（APIキー、パスワード）をコミットしない
- 大きなバイナリファイルはGit LFSを使用
- PR作成時は必ず関連Issueを参照（`Closes #XX`）
