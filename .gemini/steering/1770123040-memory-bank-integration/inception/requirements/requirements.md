# 要件定義: メモリ機能による成長トラッキング

## Intent Analysis Summary

| 項目 | 内容 |
|------|------|
| **GitHub Issue** | [#3 🧠 メモリ機能による成長トラッキング](https://github.com/nuance-sudo/drawing-practice-agent-gch4/issues/3) |
| **Request Type** | Enhancement（機能拡張） |
| **Scope Estimate** | Multiple Components（agent, APIサーバー） |
| **Complexity Estimate** | Moderate（中程度） |

---

## 背景・目的

現在のデッサンコーチングエージェントは**単発評価のみ**を提供しています。ユーザーの過去の作品と比較した成長フィードバックを提供することで、以下の価値を創出します：

- 「昨日よりも陰影のつけ方うまくなったね」のような**成長フィードバック**
- 継続的な弱点の**改善サポート**
- モチベーション向上のための**成長可視化**
- デッサン内容の**タグ管理**（リンゴ、静物、人物など）

---

## 技術アプローチ

**Vertex AI Agent Engine Memory Bank**を使用してメモリ機能を実装します。

### 参照ドキュメント

**Google Cloud 公式:**
- [Memory Bank 概要](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview?hl=ja)
- [ADKクイックスタート](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/quickstart-adk?hl=ja)
- [メモリの生成](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories?hl=ja)
- [メモリの取得](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/fetch-memories?hl=ja)

**ADK 公式:**
- [Memory - Agent Development Kit](https://google.github.io/adk-docs/sessions/memory/)

**プロジェクト内調査レポート:**
- [Memory Bank技術調査レポート](../research/memory-bank-research.md) - ADKツール vs Vertex AI Client API詳細比較

### Memory Bankの主要機能
1. **記憶の抽出**: 会話から重要な情報を自動抽出
2. **メモリの統合**: 新情報を既存メモリと統合
3. **スコープベース分離**: ユーザーIDごとにメモリを分離
4. **類似性検索**: 関連するメモリを取得

### 技術選定結果

> [!IMPORTANT]
> 詳細は[技術調査レポート](../research/memory-bank-research.md)を参照

| 機能 | ADKツール | Vertex AI Client API |
|-----|----------|---------------------|
| セマンティック検索 | ✅ | ✅ |
| メタデータフィルタ | ❌ | ✅ |
| 時系列フィルタ | ❌ | ✅ |

**結論**: メタデータフィルタを使用するため、**Vertex AI Client APIをカスタムツールでラップ**して実装


---

## 機能要件

### FR-001: 成長フィードバック生成
- **説明**: 過去の提出作品と比較した成長フィードバックを生成
- **入力**: 現在のデッサン画像、ユーザーID
- **出力**: 成長レポート（改善点、維持すべき強み、継続的な課題）
- **例**:
  ```markdown
  ### 📈 成長レポート
  前回（1/15）と比較して：
  - ✅ **陰影表現が向上**: 明暗の階調が5段階→8段階に改善しました！
  - ✅ **立体感UP**: 反射光の表現が追加され、より立体的になりました
  - 🔄 **プロポーション**: 前回同様、右側がやや歪む傾向があります
  ```

### FR-002: 提出履歴のメモリ保存
- **説明**: 各デッサン提出時に分析結果をMemory Bankに保存
- **保存データ**:
  - 提出日時
  - 分析結果（スコア、評価コメント）
  - モチーフタグ
  - 画像参照情報

### FR-003: スキル進捗トラッキング
- **説明**: カテゴリ別のスキル進捗を追跡
- **カテゴリ**: プロポーション、陰影、質感、線の質
- **追跡内容**: 平均スコア推移、最新スコア、改善傾向

### FR-004: 過去メモリの取得・活用
- **説明**: フィードバック生成時に過去のメモリを取得してプロンプトに注入
- **取得方法**: 類似性検索または単純取得
- **スコープ**: ユーザーID（GitHub username）

### FR-005: メタデータによるモチーフ絞り込み
- **説明**: メタデータフィルタを使用してモチーフ別の提出履歴を取得
- **メタデータフィールド**:
  ```python
  metadata = {
      "motif": {"string_value": "りんご"},
      "motif_category": {"string_value": "静物"},
      "overall_score": {"double_value": 75.0},
      "proportion_score": {"double_value": 70.0},
      "tone_score": {"double_value": 80.0},
      "texture_score": {"double_value": 72.0},
      "line_quality_score": {"double_value": 78.0},
      "rank_label": {"string_value": "8級"},
      "submitted_at": {"timestamp_value": "2026-02-01T14:00:00Z"},
  }
  ```
- **ユースケース**: 「りんごの過去の作品と比較」

### FR-006: 時系列での最新投稿取得
- **説明**: システムフィールド`create_time`でフィルタして最新の提出を取得
- **フィルタ例**: `create_time>="2025-01-01T00:00:00Z"`
- **ユースケース**: 「直近5件の提出と比較」

### FR-007: 類似フィードバック検索
- **説明**: 類似性検索で過去の類似フィードバックを取得
- **検索例**: `similarity_search_params={"search_query": "陰影の表現", "top_k": 5}`
- **ユースケース**: 「陰影に関する過去のフィードバックを参照」

---

## Memory Bank データ構造設計

### メモリ構造

```json
{
  "name": "projects/.../memories/...",
  "scope": { "user_id": "github_username" },
  "fact": "デッサン分析結果のテキスト要約",
  "metadata": {
    "motif": { "string_value": "りんご" },
    "motif_category": { "string_value": "静物" },
    "overall_score": { "double_value": 75.0 },
    "proportion_score": { "double_value": 70.0 },
    "tone_score": { "double_value": 80.0 },
    "texture_score": { "double_value": 72.0 },
    "line_quality_score": { "double_value": 78.0 },
    "rank_label": { "string_value": "8級" },
    "submitted_at": { "timestamp_value": "2026-02-01T14:00:00Z" }
  },
  "topics": ["custom_memory_topic_label: dessin-analysis"]
}
```

### フィルタリング方法

| 方法 | API | ユースケース |
|-----|-----|-------------|
| メタデータフィルタ | `filter_groups` | モチーフ別絞り込み |
| システムフィールドフィルタ | `filter` | 時系列取得 |
| 類似性検索 | `similarity_search_params` | 関連フィードバック取得 |


---

## 非機能要件

### NFR-001: パフォーマンス
- メモリ取得はフィードバック生成時間に+1秒以内の追加遅延

### NFR-002: データ分離
- ユーザー間のメモリは完全に分離（スコープベース）

### NFR-003: 既存機能との互換性
- 既存のフィードバック機能は維持
- メモリがない新規ユーザーでも正常動作

---

## データモデル拡張

### 新規モデル: SkillProgression
```python
class SkillProgression(BaseModel):
    """スキル進捗トラッキング"""
    category: str           # "proportion", "tone", "texture", "line_quality"
    average_score: float    # 平均スコア
    latest_score: float     # 最新スコア
    trend: str              # "improving", "stable", "declining"
    submission_count: int   # 提出回数
```

### 既存モデル: DessinAnalysis（変更なし）
- `tags`フィールドは既に存在（モチーフタグ対応済み）

---

## 実装スコープ

### In Scope
- [ ] Memory Bank統合設定（Agent EngineのMemory Bank有効化）
- [ ] メモリ生成ロジック（提出時に分析結果を保存）
- [ ] メモリ取得ロジック（フィードバック生成時に過去メモリを取得）
- [ ] 成長フィードバックプロンプト拡張
- [ ] スキル進捗計算ロジック

### Out of Scope（将来対応）
- [ ] Webアプリでの成長グラフ表示
- [ ] 週次/月次レポート生成
- [ ] 他ユーザーとの比較機能

---

## 影響範囲

| コンポーネント | 影響 |
|---------------|------|
| `packages/agent/dessin_coaching_agent/` | Memory Bank統合設定 |
| `packages/agent/src/services/agent_engine_service.py` | メモリ取得/生成ロジック追加 |
| `packages/agent/src/models/` | SkillProgressionモデル追加 |
| Agent Engineデプロイ | Memory Bank有効化設定 |

---

## 成功基準

1. **メモリ保存**: デッサン提出時に分析結果がMemory Bankに保存される
2. **メモリ取得**: フィードバック生成時に過去のメモリが取得できる
3. **成長フィードバック**: 2回目以降の提出で成長比較フィードバックが表示される
4. **既存機能維持**: 新規ユーザー（メモリなし）でも正常に動作する
