# 鉛筆デッサンコーチングエージェント ユビキタス言語定義（Glossary）

## 概要

本ドキュメントは、プロジェクトで使用するドメイン用語の定義と、コード上での命名規則を定義します。チーム内での認識統一とコードの可読性向上を目的とします。

---

## ドメイン用語

### デッサン関連

| 日本語 | 英語 | コード上の命名 | 説明 |
|--------|------|----------------|------|
| デッサン | Dessin | `dessin` | 鉛筆などで描かれた素描画 |
| プロポーション | Proportion | `proportion` | 形の正確さ、比率・バランス |
| 陰影 / トーン | Tone | `tone` | 明暗の階調、光と影の表現 |
| 質感 | Texture | `texture` | 素材感の表現 |
| 線の質 | Line Quality | `line_quality` | 運筆、筆圧、ハッチング |
| ハッチング | Hatching | `hatching` | 平行線による陰影表現技法 |
| 輪郭線 | Contour | `contour` | モチーフの外形を示す線 |
| 補助線 | Guide Line | `guide_line` | 形を正確に取るための補助的な線 |
| モチーフ | Motif | `motif` | デッサンの対象物 |

### コーチング関連

| 日本語 | 英語 | コード上の命名 | 説明 |
|--------|------|----------------|------|
| コーチング | Coaching | `coaching` | フィードバックによる指導 |
| フィードバック | Feedback | `feedback` | 分析結果に基づく改善提案 |
| 分析 | Analysis | `analysis` | デッサンの評価・解析 |
| 改善点 | Improvement | `improvement` | 改善すべきポイント |
| 強み | Strength | `strength` | 良くできている点 |
| お手本画像 | Example Image | `example_image` | 改善例を示す生成画像 |
| スコア | Score | `score` | 評価点（0-100） |

### ランク関連

| 日本語 | 英語 | コード上の命名 | 説明 |
|--------|------|----------------|------|
| ランク | Rank | `rank` | ユーザーの習熟度レベル |
| 級 | Kyu | `kyu` | 初心者〜中級者のランク（10級〜1級） |
| 段 | Dan | `dan` | 上級者のランク（初段〜3段） |
| 師範代 | Sub-master | `sub_master` | 準最高ランク |
| 師範 | Master | `master` | 最高ランク |
| 昇格 | Promotion | `promotion` | ランクの上昇 |
| 昇格条件 | Promotion Criteria | `promotion_criteria` | ランクアップに必要な条件 |

### システム関連

| 日本語 | 英語 | コード上の命名 | 説明 |
|--------|------|----------------|------|
| エージェント | Agent | `agent` | ADKで構築されたAIエージェント |
| ツール | Tool | `tool` | エージェントが使用する機能 |
| セッション | Session | `session` | 1回の会話・処理単位 |
| メモリ | Memory | `memory` | 長期記憶（過去のフィードバック等） |
| メモリバンク | Memory Bank | `memory_bank` | Vertex AI Memory Bank |
| 提出 | Submission | `submission` | ユーザーのデッサン投稿 |

---

## GitHub関連用語

| 日本語 | 英語 | コード上の命名 | 説明 |
|--------|------|----------------|------|
| プルリクエスト | Pull Request | `pr` / `pull_request` | コード変更の提案 |
| リポジトリ | Repository | `repo` / `repository` | コード保管場所 |
| コミット | Commit | `commit` | 変更の記録単位 |
| コメント | Comment | `comment` | PRへのフィードバックコメント |
| ワークフロー | Workflow | `workflow` | GitHub Actionsの処理定義 |

---

## GCP関連用語

| 日本語 | 英語 | コード上の命名 | 説明 |
|--------|------|----------------|------|
| プロジェクトID | Project ID | `project_id` | GCPプロジェクト識別子 |
| リージョン | Region / Location | `location` | GCPリソースの配置場所 |
| サービスアカウント | Service Account | `service_account` | GCP認証用アカウント |
| シークレット | Secret | `secret` | Secret Managerで管理される秘密情報 |

---

## ADK（Agents Development Kit）用語

| 日本語 | 英語 | コード上の命名 | 説明 |
|--------|------|----------------|------|
| ルートエージェント | Root Agent | `root_agent` | メインエージェント（ADK規約） |
| ランナー | Runner | `runner` | エージェント実行エンジン |
| セッションサービス | Session Service | `session_service` | セッション管理サービス |
| メモリサービス | Memory Service | `memory_service` | 長期記憶サービス |

---

## モデル名対応表

### Pydanticモデル

| クラス名 | 用途 | ファイル |
|----------|------|----------|
| `CoachingRequest` | コーチングリクエスト | `models/request.py` |
| `DessinAnalysis` | デッサン分析結果 | `models/analysis.py` |
| `ProportionAnalysis` | プロポーション分析 | `models/analysis.py` |
| `ToneAnalysis` | 陰影分析 | `models/analysis.py` |
| `TextureAnalysis` | 質感分析 | `models/analysis.py` |
| `LineQualityAnalysis` | 線の質分析 | `models/analysis.py` |
| `DessinFeedback` | フィードバック | `models/feedback.py` |
| `UserRank` | ユーザーランク | `models/rank.py` |

---

## サービス名対応表

| クラス名 | 用途 | ファイル |
|----------|------|----------|
| `GeminiService` | Vertex AI Gemini連携 | `services/gemini_service.py` |
| `RankService` | ランク管理（Firestore） | `services/rank_service.py` |
| `MemoryService` | メモリ管理（Memory Bank） | `services/memory_service.py` |
| `SecretsService` | Secret Manager連携 | `services/secrets.py` |

---

## ツール名対応表

| 関数名 | 用途 | ファイル |
|--------|------|----------|
| `analyze_dessin` | デッサン分析 | `tools/image_tool.py` |
| `generate_feedback` | フィードバック生成 | `agent.py` |
| `generate_example_image` | お手本画像生成 | `tools/image_tool.py` |
| `post_github_comment` | GitHubコメント投稿 | `tools/github_tool.py` |
| `get_pr_images` | PR画像取得 | `tools/github_tool.py` |
| `search_memory` | メモリ検索 | `agent.py` |

---

## 略語一覧

| 略語 | 正式名称 | 説明 |
|------|----------|------|
| ADK | Agents Development Kit | Googleのエージェント開発キット |
| GCP | Google Cloud Platform | Googleのクラウドプラットフォーム |
| PR | Pull Request | GitHubのプルリクエスト |
| API | Application Programming Interface | アプリケーション間のインターフェース |
| LLM | Large Language Model | 大規模言語モデル |
| JWT | JSON Web Token | 認証トークン形式 |

---

## 参考文書

### ハッカソン関連

| ドキュメント | URL |
|-------------|-----|
| 第4回 Agentic AI Hackathon ルール | https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=rule |

### ADK（Agents Development Kit）

| ドキュメント | URL |
|-------------|-----|
| ADK公式ドキュメント | https://google.github.io/adk-docs/ |
| API Reference（Python） | https://google.github.io/adk-docs/api-reference/python/ |
| Multi-Agents（マルチエージェント） | https://google.github.io/adk-docs/agents/multi-agents/ |
| Sessions（セッション管理） | https://google.github.io/adk-docs/sessions/ |
| Memory（メモリ機能） | https://google.github.io/adk-docs/sessions/memory/ |
| Cloud Run Deploy | https://google.github.io/adk-docs/deploy/cloud_run/ |

### Gemini API

| ドキュメント | URL |
|-------------|-----|
| Gemini 3（gemini-3-flash-preview） | https://ai.google.dev/gemini-api/docs/gemini-3?hl=ja |
| 画像生成（gemini-2.5-flash-image） | https://ai.google.dev/gemini-api/docs/image-generation?hl=ja |
| Thinking機能 | https://ai.google.dev/gemini-api/docs/thinking?hl=ja |
| マルチモーダル | https://ai.google.dev/gemini-api/docs/vision?hl=ja |

### Google Cloud

| ドキュメント | URL |
|-------------|-----|
| Vertex AI | https://cloud.google.com/vertex-ai/docs |
| Cloud Run | https://cloud.google.com/run/docs |
| Firestore | https://cloud.google.com/firestore/docs |
| Secret Manager | https://cloud.google.com/secret-manager/docs |
| Workload Identity Federation | https://cloud.google.com/iam/docs/workload-identity-federation |

### GitHub

| ドキュメント | URL |
|-------------|-----|
| GitHub REST API | https://docs.github.com/en/rest |
| GitHub Apps | https://docs.github.com/en/apps |
| GitHub Actions | https://docs.github.com/en/actions |

### ローカル参考資料

| ドキュメント | パス |
|-------------|------|
| AWS版ソースリファレンス | `tmp/source-reference/` |
