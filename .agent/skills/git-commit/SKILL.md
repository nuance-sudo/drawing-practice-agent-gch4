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

### 2. 機密情報チェック（コミット前に必須）

> ⚠️ **コミット前に必ず機密情報が含まれていないか確認**
>
> プロジェクトID、リソースID、APIキー等がハードコードされていないか確認してください。

#### チェック対象パターン

| カテゴリ | パターン例 | 説明 |
|---------|-----------|------|
| GCPプロジェクトID | `projects/xxx`, `project_id = "xxx"` | GCPプロジェクト名・ID |
| リソースID | `reasoningEngines/xxx`, `agents/xxx` | Vertex AI Agent Engine等のリソースID |
| APIキー | `GOOGLE_API_KEY`, `sk-xxx`, `AIza...` | 各種APIキー・シークレット |
| 認証情報 | `password`, `secret`, `token` | パスワード・トークン |
| 接続文字列 | `mongodb://`, `postgresql://` | データベース接続文字列 |

#### チェックコマンド

```bash
# ステージング済みの変更で機密情報をチェック
git diff --cached --unified=0 | grep -iE \
  '(project[_-]?id|GOOGLE_API_KEY|API_KEY|SECRET|PASSWORD|TOKEN|sk-[a-zA-Z0-9]+|AIza[a-zA-Z0-9]+|projects/[a-zA-Z0-9-]+|reasoningEngines/[0-9]+|agents/[a-zA-Z0-9-]+)'

# 結果が空なら OK、出力があれば要確認
```

#### 発見時の対応

1. **環境変数に移動**: 機密値を`.env`や環境変数に移動
2. **設定ファイル確認**: `config.py`等で`os.environ.get()`を使用しているか確認
3. **`.gitignore`確認**: `.env`ファイルが除外されているか確認

```python
# ❌ NG: ハードコード
PROJECT_ID = "my-gcp-project-123"

# ✅ OK: 環境変数から取得
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
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


### 6. PRレビュー対応（レビュー指摘があった場合）

#### 6.1 レビューコメントの確認

```python
# レビューサマリーを取得
mcp_github-mcp-server_pull_request_read(
    method="get_reviews",
    owner="nuance-sudo",
    repo="drawing-practice-agent-gch4",
    pullNumber=XX
)

# 詳細なレビューコメントを取得
mcp_github-mcp-server_pull_request_read(
    method="get_review_comments",
    owner="nuance-sudo",
    repo="drawing-practice-agent-gch4",
    pullNumber=XX
)
```

#### 6.2 指摘のトリアージ（難易度・重要度の整理）

> ⚠️ **すべてのレビュー指摘に対応する必要はない**
> 
> PoCの範囲を超える指摘は無視してマージしてOK。
> **マージの判断はユーザーが行う**ため、難易度と重要度を説明する。

レビュー指摘を以下のフォーマットで整理して報告する：

```markdown
## レビュー指摘事項

| 問題 | 難易度 | 対応 |
|------|--------|------|
| **[問題1]** | 🟢 簡単 | ✅ 対応（〜分）|
| **[問題2]** | 🟡 中程度 | ✅ 対応（〜分）|
| **[問題3]** | 🔴 複雑 | ⏭️ PoCでは見送り |

### 対応判断の基準

| 難易度 | 目安 | 対応方針 |
|--------|------|----------|
| 🟢 簡単 | 5分以内 | 即時対応推奨 |
| 🟡 中程度 | 10-30分 | ユーザー判断 |
| 🔴 複雑 | 1時間以上 / 設計変更必要 | PoC見送り推奨 |

簡単な修正だけ対応しますか？それともPoCとして現状のままマージしますか？
```

#### 6.3 修正とプッシュ

```bash
# 修正を実施
# ...

# コミット（修正内容を明記）
git add .
git commit -m "fix: レビュー指摘対応

- [指摘1への対応]
- [指摘2への対応]"

# 同じブランチにプッシュ → PRが自動更新される
git push origin [ブランチ名]
```

#### 6.4 レビュワーに通知

```python
# PRにコメントを追加
mcp_github-mcp-server_add_issue_comment(
    owner="nuance-sudo",
    repo="drawing-practice-agent-gch4",
    issue_number=XX,  # PRの番号
    body="レビュー指摘に対応しました。再レビューをお願いします。\n\n## 対応内容\n- [対応1]\n- [対応2]"
)
```

### 7. PRマージ

レビュー承認後、PRをマージ：

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
- [ ] **機密情報チェックコマンドを実行した**（手順2参照）
- [ ] チェック結果に機密情報が含まれていない
- [ ] コミットメッセージが規約に従っている

PR作成後：
- [ ] 関連Issueのタスクを更新した
- [ ] PRの説明に変更内容を記載した

レビュー対応後：
- [ ] レビューコメントをすべて確認した
- [ ] 修正が必要な箇所を対応した
- [ ] 同じブランチにプッシュしてPRを更新した
- [ ] レビュワーに再レビューを依頼した（必要な場合）

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
