---
name: work-complete
description: 作業完了後にaidlc-docsをsteeringに移動し、walkthroughを作成する。「/work-complete [作業タイトル]」で起動。
---

# 作業完了スキル

## 目的

`/aidlc`スキルで作成した`aidlc-docs/`の成果物を作業完了後に`.gemini/steering/`に移動し、walkthroughドキュメントを作成する。

## 前提条件

- `/aidlc`スキルで作業を実施し、`aidlc-docs/`にドキュメントが作成されていること
- 開発作業が完了していること

## 実行手順

### 1. 作業タイトルの確認

ユーザーが指定した作業タイトルを使用する。指定がない場合は`aidlc-docs/`の内容から適切なタイトルを提案する。

### 2. Unix タイムスタンプの取得

```bash
date +%s
```

### 3. ステアリングディレクトリの作成

```bash
mkdir -p .gemini/steering/[unixtime]-[作業タイトル]
```

**命名規則：**
- 作業タイトルはケバブケース（kebab-case）で記述
- 英語で記述（日本語は使用しない）
- 簡潔に内容を表す（例：`add-image-analysis`, `fix-login-bug`, `refactor-api-layer`）

**例：**
```bash
mkdir -p .gemini/steering/1738417134-add-image-analysis
```

### 4. aidlc-docsの移動

```bash
mv aidlc-docs/* .gemini/steering/[unixtime]-[作業タイトル]/
rmdir aidlc-docs
```

### 5. walkthrough.mdの作成

移動先ディレクトリに`walkthrough.md`を作成する。

**フォーマット：**

```markdown
# Walkthrough: [作業タイトル]

## 概要

[何を変更したかの概要を1-2文で記述]

## 変更サマリー

| ファイル | 変更内容 |
|---------|---------|
| [ファイルパス] | [変更内容] |
| [ファイルパス] | [変更内容] |

## 主要な変更点

### [変更カテゴリ1]

[詳細な説明]

### [変更カテゴリ2]

[詳細な説明]

## テスト・検証

- [x] ローカル動作確認
- [x] リント・型チェック
- [ ] その他の検証項目

## スクリーンショット（任意）

[必要に応じてスクリーンショットを追加]

## 関連Issue

- #XX

## 次のステップ

[残タスクや今後の作業があれば記載]
```

### 6. 完了報告

以下の形式でユーザーに報告する：

```markdown
## ✅ 作業完了処理が完了しました

### 移動先
`.gemini/steering/[unixtime]-[作業タイトル]/`

### 移動したファイル
- requirements.md
- design.md
- task.md
- audit.md
- [その他のファイル]

### 作成したファイル
- walkthrough.md

### 次のアクション
- `/git-commit` でコミット・PR作成を行ってください
```

---

## チェックリスト

実行前：
- [ ] aidlc-docs/が存在する
- [ ] 開発作業が完了している
- [ ] 作業タイトルが確定している

実行後：
- [ ] .gemini/steering/[unixtime]-[作業タイトル]/ に移動完了
- [ ] walkthrough.md を作成完了
- [ ] aidlc-docs/ が削除されている

---

## 注意事項

- aidlc-docs/が存在しない場合はエラーとする
- 同名のステアリングディレクトリが存在する場合は確認を求める
- walkthroughには実際に行った変更のみを記載する（計画ではなく実績）
