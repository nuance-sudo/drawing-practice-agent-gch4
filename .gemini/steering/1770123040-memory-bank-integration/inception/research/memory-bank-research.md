# Memory Bank技術調査レポート

## 調査日時
2026-02-01T14:35:00Z - 14:37:00Z

## 調査目的
Memory Bank統合において、ADK標準ツールとVertex AI Client APIのどちらを使用するか判断するため、機能差異を調査。

---

## 参照ドキュメント

### Google Cloud 公式ドキュメント
- [Memory Bank 概要](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview?hl=ja)
- [ADKクイックスタート](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/quickstart-adk?hl=ja)
- [メモリの生成](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories?hl=ja)
- [メモリの取得](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/fetch-memories?hl=ja)

### ADK 公式ドキュメント
- [Memory - Agent Development Kit](https://google.github.io/adk-docs/sessions/memory/)

### Python パッケージドキュメント
- `google.adk.memory` モジュール
- `google.adk.tools.preload_memory_tool` モジュール
- `google.adk.tools.load_memory_tool` モジュール

---

## ADKメモリサービス

### BaseMemoryService（抽象クラス）

```python
class google.adk.memory.BaseMemoryService:
    """Base class for memory services."""
    
    async def add_session_to_memory(session) -> None:
        """セッションをメモリに追加"""
        
    async def search_memory(*, app_name, user_id, query) -> SearchMemoryResponse:
        """メモリを検索（クエリベース）"""
```

> [!IMPORTANT]
> `search_memory`は`query`パラメータのみ。**メタデータフィルタやタイムスタンプフィルタは含まれない**。

### 実装クラス

| クラス | 用途 | 特徴 |
|-------|------|------|
| `InMemoryMemoryService` | 開発・テスト | キーワードマッチング、本番非推奨 |
| `VertexAiMemoryBankService` | 本番 | Vertex AI Memory Bank連携 |
| `VertexAiRagMemoryService` | RAG | Vertex AI RAG Corpus連携 |

---

## ADKメモリツール

### PreloadMemoryTool

```python
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

class PreloadMemoryTool(BaseTool):
    """各LLMリクエストごとに自動実行されるツール"""
```

**特徴:**
- **自動実行**: モデルが呼び出すのではなく、`process_llm_request`で自動的にメモリをプリロード
- **制御不可**: フィルタ条件などの指定不可
- **用途**: ターンごとに過去のメモリを自動的にコンテキストに追加

### LoadMemoryTool

```python
from google.adk.tools.load_memory_tool import LoadMemoryTool

async def load_memory(query: str, tool_context) -> LoadMemoryResponse:
    """クエリでメモリを検索"""
```

**特徴:**
- **モデル呼び出し**: エージェントが必要と判断したときに呼び出し
- **クエリベース**: セマンティック検索のみ
- **メタデータフィルタ**: **未サポート**

### カスタムツールでのメモリ検索

```python
# tool_context経由でメモリ検索
async def custom_memory_tool(query: str, tool_context: ToolContext) -> list[str]:
    results = await tool_context.search_memory(query)
    return [m.content for m in results.memories]
```

**制約**: `search_memory`はクエリのみ対応。メタデータフィルタには対応していない。

---

## Vertex AI Client API

### メモリ作成（メタデータ付き）

```python
from vertexai import Client

client = Client()
client.agent_engines.memories.create(
    parent="projects/{project}/locations/{location}/reasoningEngines/{id}",
    memory={
        "scope": {"user_id": "github_username"},
        "fact": "分析結果のテキスト"
    },
    config={
        "metadata": {
            "motif": {"string_value": "りんご"},
            "overall_score": {"double_value": 75.0},
            "submitted_at": {"timestamp_value": "2026-02-01T14:00:00Z"}
        }
    }
)
```

### メモリ取得（フィルタ付き）

#### メタデータフィルタ（filter_groups）

```python
results = client.agent_engines.memories.retrieve(
    name="projects/.../reasoningEngines/...",
    scope={"user_id": "github_username"},
    config={
        "filter_groups": [
            {
                "filters": [
                    {"key": "motif", "value": {"string_value": "りんご"}}
                ]
            }
        ]
    }
)
```

#### システムフィールドフィルタ（filter）

```python
# 時系列フィルタ
results = client.agent_engines.memories.retrieve(
    name="...",
    scope={"user_id": "..."},
    config={"filter": 'create_time>="2026-01-01T00:00:00Z"'}
)
```

#### 類似性検索

```python
results = client.agent_engines.memories.retrieve(
    name="...",
    scope={"user_id": "..."},
    similarity_search_params={
        "search_query": "陰影の表現",
        "top_k": 5
    }
)
```

---

## 機能比較サマリー

| 機能 | ADKツール | Vertex AI Client API |
|-----|----------|---------------------|
| セマンティック検索 | ✅ `LoadMemoryTool(query=...)` | ✅ `similarity_search_params` |
| 全メモリ自動取得 | ✅ `PreloadMemoryTool` | - |
| メタデータフィルタ | ❌ 未サポート | ✅ `filter_groups` |
| 時系列フィルタ | ❌ 未サポート | ✅ `filter` |
| メタデータ付き保存 | ❌ 未サポート | ✅ `config.metadata` |

---

## 結論

### 推奨アプローチ

**メタデータフィルタを使用するには、Vertex AI Client APIを直接呼び出すカスタムツールの作成が必要**

```
┌──────────────────────────────────────────────┐
│              ADKエージェント                  │
├──────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────────────┐  │
│  │PreloadMemory │  │search_memory_by_motif│  │
│  │    Tool      │  │  (カスタムツール)     │  │
│  └──────┬───────┘  └──────────┬───────────┘  │
│         │                     │              │
│         v                     v              │
│  VertexAiMemoryBank    Vertex AI Client API  │
│      Service           (filter_groups使用)   │
└──────────────────────────────────────────────┘
```

### 関連ドキュメント

- [要件定義](file:///home/ec2-user/src/drawing-practice-agent-gch4/aidlc-docs/inception/requirements/requirements.md) - FR-005〜FR-007参照
- [実行計画](file:///home/ec2-user/src/drawing-practice-agent-gch4/aidlc-docs/inception/plans/execution-plan.md)
