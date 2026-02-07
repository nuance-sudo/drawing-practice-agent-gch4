# エージェントフロー設計書

## 概要

本ドキュメントは、鉛筆デッサンコーチングエージェントの処理フローを詳細に説明します。

---

## 全体アーキテクチャ

```mermaid
flowchart TB
    subgraph Client["クライアント"]
        A[Web App<br/>Next.js]
    end

    subgraph CloudRun["Cloud Run API Server"]
        B[FastAPI]
        C[reviews.py]
    end

    subgraph CloudTasks["Cloud Tasks"]
        D[review-queue]
    end

    subgraph Functions["Cloud Run Functions"]
        E[process-review]
        F[annotate-image]
        G[generate-image]
        H[complete-task]
    end

    subgraph AgentEngine["Vertex AI Agent Engine"]
        I[dessin_coaching_agent]
        J[Memory Bank]
    end

    subgraph Storage["Cloud Storage"]
        K[画像バケット]
    end

    subgraph DB["Firestore"]
        L[review_tasks]
    end

    A -->|1. POST /reviews| B
    B --> C
    C -->|2. タスク作成| L
    C -->|3. タスク投入| D
    D -->|4. 実行| E
    E -->|5. 分析リクエスト| I
    I -->|6. メモリ検索/保存| J
    E -->|7. アノテーション生成| F
    F --> K
    E -->|8. お手本画像生成| G
    G --> K
    G -->|9. 完了通知| H
    H -->|10. ステータス更新| L
```

---

## 処理フロー詳細

### 1. レビューリクエスト受付

```mermaid
sequenceDiagram
    participant Client as Web App
    participant API as API Server
    participant DB as Firestore
    participant Queue as Cloud Tasks

    Client->>API: GET /reviews/upload-url
    API-->>Client: upload_url / public_url
    Client->>API: POST /reviews {image_url}
    API->>API: Firebase ID Token認証
    API->>DB: タスク作成 (status: pending)
    API->>Queue: タスク投入
    API-->>Client: 201 Created {task_id}
```

| ステップ | 処理 | コンポーネント |
|------|------|----------------|
| 1 | Firebase ID Token認証 | `src/auth/dependencies.py` |
| 2 | タスク作成 | `TaskService.create_task()` |
| 3 | Cloud Tasks投入 | `CloudTasksService.create_review_task()` |

### 2. バックグラウンド処理

```mermaid
sequenceDiagram
    participant Queue as Cloud Tasks
    participant Func as process-review
    participant Agent as Agent Engine
    participant Memory as Memory Bank
    participant DB as Firestore

    Queue->>Func: タスク実行
    Func->>DB: status: processing
    Func->>Agent: 分析リクエスト<br/>(image_url, rank, user_id)
    Agent->>Memory: 過去メモリ検索
    Agent->>Agent: デッサン分析
    Agent->>Agent: 成長スコア計算
    Agent->>Memory: 分析結果保存
    Agent-->>Func: DessinAnalysis
    Func->>DB: 分析結果保存
```

### 3. エージェント内部フロー

```mermaid
flowchart LR
    subgraph Entry["入力"]
        A[image_url]
        B[rank_label]
        C[user_id]
    end

    subgraph Agent["dessin_coaching_agent"]
        D[preload_memory_tool]
        E[search_memory_by_motif]
        F[search_recent_memories]
        G[analyze_dessin_image]
    end

    subgraph Output["出力"]
        H[DessinAnalysis]
    end

    A --> G
    B --> G
    C --> D
    D --> G
    E --> G
    F --> G
    G --> H
```

| ツール | 役割 |
|--------|------|
| `preload_memory_tool` | セッション開始時に過去メモリをプリロード |
| `search_memory_by_motif` | 同じモチーフの過去提出を検索 |
| `search_recent_memories` | ユーザーの直近提出を取得 |
| `analyze_dessin_image` | Gemini APIでデッサンを分析 |

### 4. 成長トラッキングフロー

```mermaid
flowchart TB
    A[現在の分析結果] --> B{過去メモリあり?}
    B -->|No| C[初回提出<br/>growth_score = null]
    B -->|Yes| D[過去平均スコア計算]
    D --> E[成長スコア = 50 + 差分]
    E --> F{score > 50?}
    F -->|Yes| G[成長]
    F -->|No| H{維持/後退}
```

**計算式:**
```
growth_score = 50 + (current_score - past_average_score)
```

- **50以上**: 成長
- **50**: 維持
- **50未満**: 後退

### 5. 画像生成フロー

```mermaid
sequenceDiagram
    participant Func as process-review
    participant Annotate as annotate-image
    participant Generate as generate-image
    participant Complete as complete-task
    participant Storage as Cloud Storage
    participant DB as Firestore

    Func->>Annotate: アノテーション生成
    Annotate->>Storage: 画像保存
    Annotate-->>Func: annotated_image_url

    Func->>Generate: お手本画像生成
    Generate->>Storage: 画像保存
    Generate->>Complete: 完了通知
    Complete->>DB: status: completed
```

---

## データフロー

### Memory Bankへの保存データ

| フィールド | 内容 |
|------------|------|
| `motif` | モチーフ名 (タグから抽出) |
| `overall_score` | 総合スコア |
| `proportion_score` | プロポーションスコア |
| `tone_score` | トーンスコア |
| `texture_score` | 質感スコア |
| `line_quality_score` | 線の質スコア |
| `growth_score` | 成長スコア |
| `submitted_at` | 提出日時 |

### Firestoreタスクステータス遷移

```mermaid
stateDiagram-v2
    [*] --> pending: タスク作成
    pending --> processing: Cloud Tasks実行開始
    processing --> completed: 画像生成完了
    processing --> failed: エラー発生
    completed --> [*]
    failed --> [*]
```

---

## エラーハンドリング

| フェーズ | 失敗時の動作 |
|----------|--------------|
| Cloud Tasks投入 | 同期処理にフォールバック |
| Agent Engine分析 | status: failed、エラーメッセージ保存 |
| アノテーション生成 | スキップしてお手本生成に進む |
| お手本画像生成 | 画像なしで完了 |
| ランク更新 | スキップ（分析結果は保存） |

---

## 関連ファイル

| コンポーネント | ファイル |
|----------------|--------|
| APIエンドポイント | `packages/agent/src/api/reviews.py` |
| Agent定義 | `packages/agent/dessin_coaching_agent/agent.py` |
| 分析ツール | `packages/agent/dessin_coaching_agent/tools.py` |
| メモリツール | `packages/agent/dessin_coaching_agent/memory_tools.py` |
| メモリ保存 | `packages/agent/dessin_coaching_agent/callbacks.py` |
| プロンプト | `packages/agent/dessin_coaching_agent/prompts.py` |
| モデル | `packages/agent/dessin_coaching_agent/models.py` |
