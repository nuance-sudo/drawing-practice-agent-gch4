# 要件分析: Vertex AI Agent Engine マイグレーション

## 1. 意図分析

### 1.1 ユーザー目標
Cloud Run上で稼働している鉛筆デッサンコーチングエージェントを、Vertex AI Agent Engineへマイグレーションする。

### 1.2 動機・背景
- **Memory Bank統合**: Memory BankはADK Runner/Sessionと統合して使用する設計のため、エージェントをAgent Engineにデプロイする必要がある
- **アーキテクチャの分離**: APIレイヤーはCloud Runのまま維持し、エージェント処理のみAgent Engineに移行
- **スケーラビリティ**: エージェント処理のスケーリングをAgent Engineに委任

### 1.3 スコープ
- **対象**: `packages/agent/` のエージェント部分
- **対象外**: Web フロントエンド、Cloud Functions（画像生成・アノテーション）

## 2. 現状アーキテクチャ

```
┌─────────────────┐     ┌─────────────────────────────────┐     ┌────────────┐
│                 │     │          Cloud Run              │     │            │
│    Web App      │────▶│  ┌───────────┐  ┌───────────┐  │────▶│ Gemini API │
│  (Next.js)      │     │  │  FastAPI  │  │ ADK Agent │  │     │            │
│                 │     │  └───────────┘  └───────────┘  │     └────────────┘
└─────────────────┘     └─────────────────────────────────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │  Firestore   │
                              └──────────────┘
```

## 3. 目標アーキテクチャ

```
┌─────────────────┐     ┌───────────────────────┐     ┌──────────────────────────┐
│                 │     │      Cloud Run        │     │   Vertex AI Agent Engine │
│    Web App      │────▶│  ┌───────────────┐   │────▶│  ┌────────────────────┐  │
│  (Next.js)      │     │  │    FastAPI    │   │     │  │    ADK Agent       │  │
│                 │     │  └───────────────┘   │     │  │  (コーチングAgent) │  │
└─────────────────┘     └───────────────────────┘     │  └────────────────────┘  │
                                     │                 │            │             │
                                     │                 │            ▼             │
                                     │                 │  ┌────────────────────┐  │
                                     │                 │  │    Memory Bank     │  │
                                     │                 │  └────────────────────┘  │
                                     │                 └──────────────────────────┘
                                     ▼                              │
                              ┌──────────────┐                      │
                              │  Firestore   │◀─────────────────────┘
                              └──────────────┘
```

## 4. 機能要件

### 4.1 必須要件（Must Have）

| ID | 要件 | 説明 |
|----|------|------|
| FR-001 | ADKエージェントをAgent Engineにデプロイ | 既存の`root_agent`をAgent Engine形式に変換・デプロイ |
| FR-002 | Cloud RunからAgent Engineへの呼び出し | FastAPIからAgent Engine APIを呼び出す統合 |
| FR-003 | 既存機能の維持 | デッサン分析、フィードバック生成が正常動作 |
| FR-004 | フィーチャーフラグ | Agent Engine使用/不使用を切り替え可能 |

### 4.2 推奨要件（Should Have）

| ID | 要件 | 説明 |
|----|------|------|
| FR-005 | Memory Bank統合 | ユーザーごとの長期記憶保持 |
| FR-006 | デプロイスクリプト | Agent Engineへの自動デプロイ |

### 4.3 将来要件（Could Have）

| ID | 要件 | 説明 |
|----|------|------|
| FR-007 | セッション管理 | Agent Engineのセッション機能活用 |

## 5. 技術要件

### 5.1 Vertex AI Agent Engine

| 項目 | 値 |
|------|-----|
| Python バージョン | 3.12（現在使用中、Agent Engineは3.8-3.12対応） |
| ADK バージョン | 1.18+ |
| google-cloud-aiplatform | 1.133+ |
| デプロイ方式 | `AdkApp`によるラップ |

### 5.2 API連携

| 項目 | 説明 |
|------|------|
| 呼び出し方式 | `vertexai.agent_engines` または gRPC API |
| 認証 | サービスアカウント（ADC） |

## 6. 設計上の考慮事項

### 6.1 段階的移行
1. **Phase 1**: Agent Engineへのデプロイ（基本動作確認）
2. **Phase 2**: Cloud RunからAgent Engineへの統合
3. **Phase 3**: Memory Bank統合（オプション）

### 6.2 リスク・制約

| リスク | 対策 |
|--------|------|
| Agent Engine API互換性 | フィーチャーフラグで旧実装にフォールバック可能 |
| レイテンシ増加 | モニタリング設置、必要に応じて最適化 |
| コスト増 | PoCフェーズで使用量監視 |

## 7. 成功基準

- [ ] Agent Engineにエージェントがデプロイされている
- [ ] Cloud RunからAgent Engineを呼び出してデッサン分析が動作する
- [ ] 既存のWeb UIからの機能が正常に動作する
- [ ] フィーチャーフラグでCloud Run直接実行とAgent Engine実行を切り替え可能

## 8. 補足情報

### 8.1 既存の準備状況（Issue #46より）
- **Agent Engineインスタンス**: 作成済み（ID: `4011449426684936192`）
- **Memory Bank準備**: `memory_bank_service.py` 作成済み（`git stash`に保存）

### 8.2 参考リソース
- [ADK Documentation](https://google.github.io/adk/)
- [Vertex AI Agent Engine Documentation](https://cloud.google.com/vertex-ai/docs/agents)
