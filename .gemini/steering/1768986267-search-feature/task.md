# タスクリスト: 検索機能実装

- [x] **Backend: API実装**
    - [x] `packages/agent/src/services/task_service.py` の `list_tasks` を更新し、フィルタリングに対応させる。
    - [x] `packages/agent/src/api/reviews.py` の `list_reviews` を更新し、クエリパラメータを受け取るようにする。
    - [x] ローカルテストまたは単体テストでAPIの動作確認。

- [ ] **Infrastructure: Firestore Index**
    - [ ] コンソール上で必要な複合インデックスを作成（エラーログのURLから作成可能）。
    - [ ] `packages/infra/firestore.indexes.json` (またはルートの `firestore.indexes.json`) を更新し、インデックス定義をコード化する。

- [x] **Frontend: UI変更 (Pivot 3)**
    - [x] `packages/web/src/components/features/dashboard/TaskGrid.tsx` を新規作成（リスト表示のみ）。
    - [x] `packages/web/src/app/page.tsx` をリファクタリング。
        - 状態管理（`useTasks`, `filteredTasks`）を移動。
        - 2カラムレイアウト（左70%/右30%）を実装。
    - [x] `packages/web/src/components/features/dashboard/TaskList.tsx` を削除。
    - [x] `CalendarFilter` 内にフィルタ解除ボタンを配置。
    - [x] `page.tsx` からグローバルなフィルタ解除ボタンを削除。
    - [x] カレンダーとタグの相互フィルタリング（Mutual Filtering）を実装。

- [x] **Deployment**
    - [x] Backend (Cloud Run) deploy.
    - [x] Frontend (Firebase Hosting) deploy.
- [x] **Verification**
    - [x] 動作確認: 日付範囲指定で正しく絞り込めるか。
    - [x] 動作確認: タグ指定で正しく絞り込めるか。
    - [x] 動作確認: ステータス指定で正しく絞り込めるか。
    - [x] 動作確認: 複合条件で正しく動作するか。
    - [x] `npm run build` PASS.
