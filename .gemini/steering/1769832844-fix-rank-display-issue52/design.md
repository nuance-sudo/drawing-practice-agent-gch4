# Issue #52: 設計書

## アーキテクチャ概要

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Firestore
    
    User->>Frontend: 画像アップロード
    Frontend->>Backend: POST /reviews
    Backend->>Firestore: ユーザーランク取得
    Firestore-->>Backend: 現在のランク
    Backend->>Firestore: タスク作成（rank_at_review含む）
    Backend-->>Frontend: タスクID
    
    Note over Backend: バックグラウンド処理
    Backend->>Backend: 分析実行
    Backend->>Firestore: 結果保存
    
    User->>Frontend: 結果確認
    Frontend->>Backend: GET /reviews/{id}
    Backend->>Firestore: タスク取得
    Firestore-->>Backend: タスク（rank_at_review含む）
    Backend-->>Frontend: レスポンス
    Frontend->>User: 審査時ランクを表示
```

## データモデル変更

### ReviewTask（バックエンド）

```python
class ReviewTask(BaseModel):
    # 既存フィールド...
    rank_at_review: str | None  # 追加: "10級", "1段" など
```

### ReviewTask（フロントエンド）

```typescript
type ReviewTask = {
    // 既存フィールド...
    rankAtReview?: string;  // 追加
};
```

## コンポーネント設計

### UserProfileMenu（新規）

```
┌──────────────────┐
│ [👤 アバター]    │ ← クリックでドロップダウン
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ ユーザー名       │
│ ───────────────  │
│ 現在のランク     │
│ [10級] ↗        │
│ ───────────────  │
│ [ログアウト]     │
└──────────────────┘
```

### FeedbackDisplay変更

**Before:**
- `rank` props: 現在のランク（useRankから取得）

**After:**
- タスクに保存された `rankAtReview` を使用
- 存在しない場合は現在のランクをフォールバック

## 影響範囲

### バックエンド

| ファイル | 変更内容 |
|---------|---------|
| `src/models/task.py` | rank_at_reviewフィールド追加 |
| `src/services/task_service.py` | 変換処理の追加 |
| `src/api/reviews.py` | タスク作成時にランク保存 |

### フロントエンド

| ファイル | 変更内容 |
|---------|---------|
| `src/types/task.ts` | rankAtReviewフィールド追加 |
| `src/components/features/review/FeedbackDisplay.tsx` | 表示ロジック変更 |
| `src/components/common/UserProfileMenu.tsx` | 新規作成 |
| `src/app/page.tsx` | ヘッダーにプロフィール追加 |
