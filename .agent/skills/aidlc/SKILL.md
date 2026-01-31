---
name: aidlc
description: AI-DLC（AI-Driven Development Life Cycle）ワークフローを起動。大規模な新機能開発・リファクタリング・新規プロジェクト立ち上げ時に使用。「/aidlc [開発内容]」で起動。
---

# AI-DLC コアワークフロー

ソフトウェア開発をリクエストされた場合、**必ずこのワークフローに従う**。

## 適応型ワークフロー原則

**ワークフローは作業に適応する、その逆ではない。**

AIモデルは以下に基づいて必要なステージをインテリジェントに評価:
1. ユーザーの意図の明確さ
2. 既存コードベースの状態（あれば）
3. 変更の複雑性とスコープ
4. リスクと影響度の評価

## MANDATORY: 日本語での出力

**CRITICAL**: 全ての成果物およびドキュメントは**日本語**で作成すること。

- aidlc-docs/配下の全てのMarkdownファイル
- ユーザーへの説明・質問・完了メッセージ
- コード内のコメント（技術用語は英語可）
- audit.mdへの記録

**例外**: コード自体（変数名、関数名等）は英語で記述。

## MANDATORY: ルール詳細の読み込み

**CRITICAL**: どのフェーズを実行する際も、必ず `resources/` ディレクトリ内の関連ルール詳細ファイルを読み込んで使用すること。

**共通ルール**: ワークフロー開始時に必ず読み込む:
- `common/process-overview.md` - ワークフロー概要
- `common/session-continuity.md` - セッション再開ガイダンス
- `common/content-validation.md` - コンテンツ検証要件
- `common/question-format-guide.md` - 質問形式ルール

## MANDATORY: コンテンツ検証

**CRITICAL**: ファイルを作成する前に、`common/content-validation.md` に従ってコンテンツを検証:
- Mermaidダイアグラム構文を検証
- ASCIIアートダイアグラムを検証（`common/ascii-diagram-standards.md` 参照）
- 特殊文字を適切にエスケープ
- 複雑なビジュアルコンテンツにテキスト代替を提供

## MANDATORY: 質問ファイル形式

**CRITICAL**: どのフェーズでも質問する際は、質問形式ガイドラインに従う。

**詳細は `common/question-format-guide.md` を参照**:
- 多肢選択形式（A, B, C, D, E オプション）
- [Answer]: タグの使用
- 回答検証とあいまいさの解決

## MANDATORY: ウェルカムメッセージ

**CRITICAL**: ソフトウェア開発リクエストを開始する際、必ずウェルカムメッセージを表示。

**ウェルカムメッセージの表示方法**:
1. `common/welcome-message.md` からウェルカムメッセージを読み込む
2. 完全なメッセージをユーザーに表示
3. 新しいワークフローの開始時に**1回だけ**実行
4. 以降のやり取りではこのファイルを読み込まない（コンテキスト節約のため）

---

# 適応型ソフトウェア開発ワークフロー

---

# 🔵 INCEPTION PHASE

**目的**: 計画、要件収集、アーキテクチャ決定

**フォーカス**: **WHAT**（何を）と**WHY**（なぜ）を決定

**INCEPTION PHASEのステージ**:
- ワークスペース検出（ALWAYS）
- リバースエンジニアリング（CONDITIONAL - Brownfieldのみ）
- 要件分析（ALWAYS - 適応的深度）
- ユーザーストーリー（CONDITIONAL）
- ワークフロー計画（ALWAYS）
- アプリケーション設計（CONDITIONAL）
- ユニット生成（CONDITIONAL）

---

## ワークスペース検出（ALWAYS EXECUTE）

1. **MANDATORY**: 初期ユーザーリクエストをaudit.mdに完全な生の入力として記録
2. `inception/workspace-detection.md` から全ステップを読み込む
3. ワークスペース検出を実行:
   - 既存の aidlc-state.md を確認（見つかれば再開）
   - ワークスペースをスキャンして既存コードを確認
   - BrownfieldかGreenfieldかを判定
   - 既存のリバースエンジニアリング成果物を確認
4. 次のフェーズを決定: リバースエンジニアリング（Brownfieldで成果物なし）または 要件分析
5. **MANDATORY**: 発見事項をaudit.mdに記録
6. 完了メッセージをユーザーに提示（workspace-detection.md参照）
7. 次のフェーズに自動的に進む

## リバースエンジニアリング（CONDITIONAL - Brownfieldのみ）

**実行条件**:
- 既存のコードベースが検出された
- 以前のリバースエンジニアリング成果物が見つからない

**スキップ条件**:
- Greenfieldプロジェクト
- 以前のリバースエンジニアリング成果物が存在

**実行**:
1. **MANDATORY**: リバースエンジニアリング開始をaudit.mdに記録
2. `inception/reverse-engineering.md` から全ステップを読み込む
3. リバースエンジニアリングを実行:
   - 全パッケージとコンポーネントを分析
   - ビジネス概要ドキュメントを生成
   - アーキテクチャドキュメントを生成
   - コード構造ドキュメントを生成
   - APIドキュメントを生成
   - コンポーネントインベントリを生成
   - 相互作用図を生成
   - 技術スタックドキュメントを生成
   - 依存関係ドキュメントを生成
4. **明示的な承認を待つ**: 詳細な完了メッセージを提示 - ユーザーが確認するまで**進まない**
5. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

## 要件分析（ALWAYS EXECUTE - Adaptive Depth）

**常に実行**だが、深度はリクエストの明確さと複雑性に基づいて変化:
- **Minimal**: シンプルで明確なリクエスト - 意図分析のみ文書化
- **Standard**: 通常の複雑性 - 機能・非機能要件を収集
- **Comprehensive**: 複雑、高リスク - トレーサビリティ付き詳細要件

**実行**:
1. **MANDATORY**: このフェーズ中のユーザー入力をaudit.mdに記録
2. `inception/requirements-analysis.md` から全ステップを読み込む
3. 要件分析を実行:
   - リバースエンジニアリング成果物を読み込む（Brownfieldの場合）
   - ユーザーリクエストを分析（意図分析）
   - 必要な要件深度を決定
   - 現在の要件を評価
   - 明確化質問を生成（必要に応じて）
   - 要件ドキュメントを生成
4. 適切な深度（minimal/standard/comprehensive）で実行
5. **明示的な承認を待つ**: requirements-analysis.md の承認形式に従う - ユーザーが確認するまで**進まない**
6. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

## ユーザーストーリー（CONDITIONAL）

**インテリジェント評価**: 多要素分析を用いてユーザーストーリーが価値を追加するか判定。

**ALWAYS 実行する場合**（高優先度指標）:
- 新しいユーザー向け機能または機能性
- ユーザーワークフローやインタラクションに影響する変更
- 複数のユーザータイプまたはペルソナが関与
- 受入基準が必要な複雑なビジネス要件

**SKIP する場合**（低優先度 - シンプルなケース）:
- ユーザー影響ゼロの純粋な内部リファクタリング
- 明確で限定的なスコープのシンプルなバグ修正
- ドキュメントのみの更新

**実行**:
1. **MANDATORY**: このフェーズ中のユーザー入力をaudit.mdに記録
2. `inception/user-stories.md` から全ステップを読み込む
3. **MANDATORY**: インテリジェント評価を実行してユーザーストーリーが必要か検証
4. **PART 1 - 計画**: 質問付きストーリープランを作成、回答を収集、あいまいさを分析、承認を得る
5. **PART 2 - 生成**: 承認されたプランを実行してストーリーとペルソナを生成
6. **明示的な承認を待つ**: user-stories.md の承認形式に従う - ユーザーが確認するまで**進まない**
7. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

## ワークフロー計画（ALWAYS EXECUTE）

1. **MANDATORY**: このフェーズ中のユーザー入力をaudit.mdに記録
2. `inception/workflow-planning.md` から全ステップを読み込む
3. **MANDATORY**: コンテンツ検証ルールを `common/content-validation.md` から読み込む
4. 全ての先行コンテキストを読み込む:
   - リバースエンジニアリング成果物（Brownfieldの場合）
   - 意図分析
   - 要件（実行された場合）
   - ユーザーストーリー（実行された場合）
5. ワークフロー計画を実行:
   - 実行するフェーズを決定
   - 各フェーズの深度レベルを決定
   - マルチパッケージ変更シーケンスを作成（Brownfieldの場合）
   - ワークフロー可視化を生成（ファイル書き込み前にMermaid構文を検証）
6. **MANDATORY**: ファイル作成前にcontent-validation.mdに従って全コンテンツを検証
7. **明示的な承認を待つ**: workflow-planning.md の推奨事項を提示、ユーザーが推奨をオーバーライドできることを強調 - ユーザーが確認するまで**進まない**
8. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

## アプリケーション設計（CONDITIONAL）

**実行条件**:
- 新しいコンポーネントまたはサービスが必要
- コンポーネントメソッドとビジネスルールの定義が必要
- サービスレイヤー設計が必要

**スキップ条件**:
- 既存コンポーネント境界内の変更
- 新しいコンポーネントやメソッドなし
- 純粋な実装変更

**実行**:
1. **MANDATORY**: このフェーズ中のユーザー入力をaudit.mdに記録
2. `inception/application-design.md` から全ステップを読み込む
3. リバースエンジニアリング成果物を読み込む（Brownfieldの場合）
4. 適切な深度（minimal/standard/comprehensive）で実行
5. **明示的な承認を待つ**: 詳細な完了メッセージを提示 - ユーザーが確認するまで**進まない**
6. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

## ユニット生成（CONDITIONAL）

**実行条件**:
- システムを複数の作業単位に分解する必要がある
- 複数のサービスまたはモジュールが必要
- 構造化された分解が必要な複雑なシステム

**スキップ条件**:
- 単一のシンプルなユニット
- 分解不要
- 単一コンポーネントの直接的な実装

**実行**:
1. **MANDATORY**: このフェーズ中のユーザー入力をaudit.mdに記録
2. `inception/units-generation.md` から全ステップを読み込む
3. リバースエンジニアリング成果物を読み込む（Brownfieldの場合）
4. 適切な深度（minimal/standard/comprehensive）で実行
5. **明示的な承認を待つ**: 詳細な完了メッセージを提示 - ユーザーが確認するまで**進まない**
6. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

---

# 🟢 CONSTRUCTION PHASE

**目的**: 詳細設計、NFR実装、コード生成

**フォーカス**: **HOW**（どのように）を決定

**CONSTRUCTION PHASEのステージ**:
- Per-Unit Loop（各ユニットに対して実行）:
  - 機能設計（CONDITIONAL, per-unit）
  - NFR要件（CONDITIONAL, per-unit）
  - NFR設計（CONDITIONAL, per-unit）
  - インフラ設計（CONDITIONAL, per-unit）
  - コード生成（ALWAYS, per-unit）
- ビルド & テスト（ALWAYS - 全ユニット完了後）

**注意**: 各ユニットは次のユニットに移る前に完全に完了（設計 + コード）される。

---

## Per-Unit Loop（各ユニットに対して実行）

**各作業単位に対して以下のステージを順次実行:**

### 機能設計（CONDITIONAL, per-unit）

**実行条件**:
- 新しいデータモデルまたはスキーマ
- 複雑なビジネスロジック
- 詳細設計が必要なビジネスルール

**スキップ条件**:
- シンプルなロジック変更
- 新しいビジネスロジックなし

**実行**:
1. **MANDATORY**: このステージ中のユーザー入力をaudit.mdに記録
2. `construction/functional-design.md` から全ステップを読み込む
3. このユニットの機能設計を実行
4. **MANDATORY**: functional-design.mdで定義された標準化2オプション完了メッセージを提示
5. **明示的な承認を待つ**: ユーザーは「変更をリクエスト」または「次のステージに進む」を選択 - ユーザーが確認するまで**進まない**
6. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

### NFR要件（CONDITIONAL, per-unit）

**実行条件**:
- パフォーマンス要件が存在
- セキュリティ考慮事項が必要
- スケーラビリティの懸念あり
- 技術スタック選択が必要

**スキップ条件**:
- NFR要件なし
- 技術スタックは既に決定済み

**実行**:
1. **MANDATORY**: このステージ中のユーザー入力をaudit.mdに記録
2. `construction/nfr-requirements.md` から全ステップを読み込む
3. このユニットのNFR評価を実行
4. **MANDATORY**: nfr-requirements.mdで定義された標準化2オプション完了メッセージを提示
5. **明示的な承認を待つ**: ユーザーが確認するまで**進まない**
6. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

### NFR設計（CONDITIONAL, per-unit）

**実行条件**:
- NFR要件が実行された
- NFRパターンを組み込む必要がある

**スキップ条件**:
- NFR要件なし
- NFR要件評価がスキップされた

**実行**:
1. **MANDATORY**: このステージ中のユーザー入力をaudit.mdに記録
2. `construction/nfr-design.md` から全ステップを読み込む
3. このユニットのNFR設計を実行
4. **MANDATORY**: nfr-design.mdで定義された標準化2オプション完了メッセージを提示
5. **明示的な承認を待つ**: ユーザーが確認するまで**進まない**
6. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

### インフラ設計（CONDITIONAL, per-unit）

**実行条件**:
- インフラサービスのマッピングが必要
- デプロイメントアーキテクチャが必要
- クラウドリソースの仕様が必要

**スキップ条件**:
- インフラ変更なし
- インフラは既に定義済み

**実行**:
1. **MANDATORY**: このステージ中のユーザー入力をaudit.mdに記録
2. `construction/infrastructure-design.md` から全ステップを読み込む
3. このユニットのインフラ設計を実行
4. **MANDATORY**: infrastructure-design.mdで定義された標準化2オプション完了メッセージを提示
5. **明示的な承認を待つ**: ユーザーが確認するまで**進まない**
6. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

### コード生成（ALWAYS EXECUTE, per-unit）

**各ユニットに対して常に実行**

**コード生成は1ステージ内に2パートある**:
1. **Part 1 - 計画**: 明示的なステップを含む詳細なコード生成計画を作成
2. **Part 2 - 生成**: 承認された計画を実行してコード、テスト、成果物を生成

**実行**:
1. **MANDATORY**: このステージ中のユーザー入力をaudit.mdに記録
2. `construction/code-generation.md` から全ステップを読み込む
3. **PART 1 - 計画**: チェックボックス付きコード生成計画を作成、ユーザー承認を得る
4. **PART 2 - 生成**: 承認された計画を実行してこのユニットのコードを生成
5. **MANDATORY**: code-generation.mdで定義された標準化2オプション完了メッセージを提示
6. **明示的な承認を待つ**: ユーザーが確認するまで**進まない**
7. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

---

## ビルド & テスト（ALWAYS EXECUTE）

1. **MANDATORY**: このフェーズ中のユーザー入力をaudit.mdに記録
2. `construction/build-and-test.md` から全ステップを読み込む
3. 包括的なビルド・テスト手順を生成:
   - 全ユニットのビルド手順
   - 単体テスト実行手順
   - 統合テスト手順（ユニット間の相互作用をテスト）
   - パフォーマンステスト手順（該当する場合）
   - 追加テスト手順（コントラクトテスト、セキュリティテスト、e2eテスト等）
4. build-and-test/サブディレクトリに手順ファイルを作成
5. **明示的な承認を待つ**: 「**ビルド・テスト手順が完了しました。Operationsステージに進む準備はできましたか？**」- ユーザーが確認するまで**進まない**
6. **MANDATORY**: ユーザーの応答をaudit.mdに完全な生の入力として記録

---

# 🟡 OPERATIONS PHASE

## Operations（PLACEHOLDER）

**ステータス**: このステージは現在、将来の拡張のためのプレースホルダー。

Operationsステージは最終的に以下を含む予定:
- デプロイメント計画と実行
- モニタリングと可観測性セットアップ
- インシデント対応手順
- メンテナンスとサポートワークフロー
- 本番準備チェックリスト

**現状**: 全てのビルド・テスト活動はCONSTRUCTIONフェーズで処理。

---

## 主要原則

- **適応型実行**: 価値を追加するステージのみ実行
- **透明な計画**: 開始前に常に実行計画を表示
- **ユーザーコントロール**: ユーザーはステージの追加/除外をリクエスト可能
- **進捗追跡**: aidlc-state.mdに実行・スキップしたステージを更新
- **完全な監査証跡**: 全てのユーザー入力とAI応答をタイムスタンプ付きでaudit.mdに記録
  - **CRITICAL**: ユーザーの**完全な生の入力**をそのままキャプチャ
  - **CRITICAL**: 監査ログでユーザー入力を要約・言い換えしない
  - **CRITICAL**: 承認だけでなく全てのやり取りを記録
- **品質フォーカス**: 複雑な変更には完全な処理、シンプルな変更は効率的に
- **コンテンツ検証**: ファイル作成前に常にcontent-validation.mdルールに従って検証
- **緊急動作禁止**: CONSTRUCTIONフェーズは各ルールファイルで定義された標準化2オプション完了メッセージを使用する必要がある。3オプションメニューやその他の緊急ナビゲーションパターンを作成しない

---

## ディレクトリ構造

```text
<WORKSPACE-ROOT>/                   # ⚠️ アプリケーションコードはここ
├── [project-specific structure]    # プロジェクトによって異なる（code-generation.md参照）
│
├── aidlc-docs/                     # 📄 ドキュメントのみ
│   ├── inception/                  # 🔵 INCEPTION PHASE
│   │   ├── plans/
│   │   ├── reverse-engineering/    # Brownfieldのみ
│   │   ├── requirements/
│   │   ├── user-stories/
│   │   └── application-design/
│   ├── construction/               # 🟢 CONSTRUCTION PHASE
│   │   ├── plans/
│   │   ├── {unit-name}/
│   │   │   ├── functional-design/
│   │   │   ├── nfr-requirements/
│   │   │   ├── nfr-design/
│   │   │   ├── infrastructure-design/
│   │   │   └── code/               # Markdownサマリーのみ
│   │   └── build-and-test/
│   ├── operations/                 # 🟡 OPERATIONS PHASE（placeholder）
│   ├── aidlc-state.md
│   └── audit.md
```

**CRITICAL RULE**:
- アプリケーションコード: ワークスペースルート（aidlc-docs/には**絶対に**置かない）
- ドキュメント: aidlc-docs/のみ
- プロジェクト構造: プロジェクトタイプごとのパターンはcode-generation.md参照

---

## ルール詳細ファイル一覧（resources/配下）

### 共通ルール（resources/common/）

| ファイル | 説明 |
|---------|------|
| `process-overview.md` | ワークフロー概要（技術リファレンス） |
| `welcome-message.md` | ユーザー向けウェルカムメッセージ |
| `session-continuity.md` | セッション再開ガイダンス |
| `content-validation.md` | コンテンツ検証要件 |
| `question-format-guide.md` | 質問形式ルール |
| `depth-levels.md` | 深度レベル定義 |
| `terminology.md` | 用語定義 |
| `ascii-diagram-standards.md` | ASCIIダイアグラム標準 |
| `error-handling.md` | エラーハンドリング |
| `overconfidence-prevention.md` | 過信防止 |
| `workflow-changes.md` | ワークフロー変更履歴 |

### INCEPTIONフェーズ（resources/inception/）

| ファイル | 説明 |
|---------|------|
| `workspace-detection.md` | ワークスペース検出詳細手順 |
| `reverse-engineering.md` | リバースエンジニアリング詳細手順 |
| `requirements-analysis.md` | 要件分析詳細手順 |
| `user-stories.md` | ユーザーストーリー詳細手順 |
| `workflow-planning.md` | ワークフロー計画詳細手順 |
| `application-design.md` | アプリケーション設計詳細手順 |
| `units-generation.md` | ユニット生成詳細手順 |

### CONSTRUCTIONフェーズ（resources/construction/）

| ファイル | 説明 |
|---------|------|
| `functional-design.md` | 機能設計詳細手順 |
| `nfr-requirements.md` | NFR要件詳細手順 |
| `nfr-design.md` | NFR設計詳細手順 |
| `infrastructure-design.md` | インフラ設計詳細手順 |
| `code-generation.md` | コード生成詳細手順 |
| `build-and-test.md` | ビルド&テスト詳細手順 |

### OPERATIONSフェーズ（resources/operations/）

| ファイル | 説明 |
|---------|------|
| `operations.md` | オペレーション（プレースホルダー） |

---

## 参考資料

- [AI-DLC GitHub リポジトリ](https://github.com/awslabs/aidlc-workflows)
- [AI-DLC ブログ記事](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)
- [AI-DLC 方法論ペーパー](https://prod.d13rzhkk8cj2z0.amplifyapp.com/)
