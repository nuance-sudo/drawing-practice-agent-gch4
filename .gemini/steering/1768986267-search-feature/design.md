# 実装設計: 検索機能

## アーキテクチャ

### Frontend (User Interface)
`packages/web` 内のコンポーネントを拡張する。

- **components/features/dashboard/CalendarFilter.tsx** (新規)
    - 月次カレンダー（Month View）を表示。
    - 該当する日付にドットなどのインジケータを表示。
    - 年月ナビゲーション（前月/次月）。

- **components/features/dashboard/TagSidebar.tsx** (変更なし)

- **components/features/dashboard/TagSidebar.tsx** (新規)
    - ユーザーが使用したタグの一覧を表示。
    - クリックイベントで特定のタグのフィルタリングを実行。

- **app/page.tsx** (変更)
    - **レイアウト統合**: `TaskList` から状態管理を移動。
    - **2カラム構成**:
        - Left (70%): `UploadSection` + `TaskGrid`
        - Right (30%): `CalendarFilter` + `TagSidebar`

- **components/features/dashboard/TaskGrid.tsx** (新規)
    - 純粋なタスク一覧表示コンポーネント。
    - `TaskList` のグリッド表示部分のみを抽出。

- **components/features/dashboard/TaskList.tsx** (削除)
    - 機能分割により廃止。

- **components/features/dashboard/CalendarFilter.tsx** (変更なし)
- **components/features/dashboard/TagSidebar.tsx** (変更なし)

### Backend (API)
`packages/agent` 内のAPIとサービスを拡張する。

- **api/reviews.py** (変更)
    - `list_reviews` エンドポイントの引数を拡張。
        - `start_date` (str, optional): YYYY-MM-DD
        - `end_date` (str, optional): YYYY-MM-DD
        - `status` (str, optional)
        - `tag` (str, optional)
    - 受け取ったパラメータを `TaskService.list_tasks` に渡す。

- **services/task_service.py** (変更)
    - `list_tasks` メソッドの引数を拡張。
    - Firestoreクエリの構築ロジックを変更。
        - デフォルト: `user_id == current_user` AND `order_by created_at DESC`
        - 条件追加:
            - `status` があれば `where("status", "==", status)`
            - `tag` があれば `where("tags", "array_contains", tag)`
            - `start_date` があれば `where("created_at", ">=", start_dt)`
            - `end_date` があれば `where("created_at", "<=", end_dt)`

### Database (Firestore)
- **Indexes**:
    - 複合クエリを実行するため、複合インデックスが必要になる可能性が高い。
    - 特に `user_id` + `created_at` + `status` や `user_id` + `tags` + `created_at` の組み合わせ。
    - 実行時にエラーが出た場合、リンクからインデックスを作成し、`firestore.indexes.json` に定義を追加する。

## データフロー
1. ユーザーが `SearchFilter` で条件入力 -> `TaskList` の State 更新。
2. `useTasks` が新しい引数で SWR を更新。
3. `api/reviews` にクエリパラメータ付き GET リクエスト。
4. `TaskService` が Firestore クエリを構築・実行。
5. 結果を返却・描画。
