# コーディング規約

## React / TypeScript / Vite

### 1. ファイル・ディレクトリ構成

**概要**: 機能別にディレクトリを分けて、コードの可読性と保守性を向上させる

#### 基本構成

```
packages/web/src/
├── main.tsx          # エントリーポイント
├── App.tsx           # ルートコンポーネント
├── index.css         # グローバルスタイル
├── components/       # UIコンポーネント
│   └── common/       # 共通コンポーネント
├── pages/            # ページコンポーネント
├── stores/           # Zustandストア
├── hooks/            # カスタムフック
├── api/              # API呼び出し
├── types/            # 型定義
└── utils/            # ユーティリティ
```

#### ルール

- コンポーネントは機能ごとにディレクトリを分ける
- 1ファイル1コンポーネントの原則を守る
- index.tsでの再エクスポートは最小限に

### 2. 命名規則

**概要**: 一貫性のある命名でコードの可読性を向上させる

| 種別 | 規則 | 例 |
|------|------|-----|
| コンポーネント | PascalCase.tsx | `ImageUpload.tsx`, `TaskList.tsx` |
| フック | use + PascalCase.ts | `useReview.ts`, `useTasks.ts` |
| ストア | camelCase + Store.ts | `taskStore.ts`, `authStore.ts` |
| 型定義 | PascalCase | `ReviewTask`, `Feedback` |
| 定数 | UPPER_SNAKE_CASE | `MAX_FILE_SIZE`, `API_BASE_URL` |
| CSS クラス | kebab-case | `task-card`, `upload-button` |

```typescript
// ✅ 良い例
// ImageUpload.tsx
export const ImageUpload: React.FC<ImageUploadProps> = ({ onUpload }) => {
  const MAX_FILE_SIZE = 10 * 1024 * 1024;
  ...
};

// useReview.ts
export const useReview = (taskId: string) => {
  ...
};

// taskStore.ts
export const useTaskStore = create<TaskState>((set) => ({
  ...
}));

// ❌ 悪い例
// imageupload.tsx  // PascalCaseでない
export const imageUpload = () => { ... };  // 関数名がPascalCaseでない
```

### 3. 型定義

**概要**: 型を必須とし、`any`型は使用禁止

#### 基本ルール

- すべての変数・関数に型を指定
- `any`型は使用禁止
- `interface`より`type`を推奨
- ジェネリクスを適切に活用

```typescript
// ✅ 良い例 - 型定義
type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

type ReviewTask = {
  taskId: string;
  userId: string;
  status: TaskStatus;
  score?: number;
  feedback?: Feedback;
};

type Feedback = {
  overallScore: number;
  strengths: string[];
  improvements: string[];
};

// ✅ 良い例 - コンポーネントProps
type ImageUploadProps = {
  onUpload: (file: File) => void;
  maxSize?: number;
  accept?: string[];
};

export const ImageUpload: React.FC<ImageUploadProps> = ({
  onUpload,
  maxSize = 10 * 1024 * 1024,
  accept = ['image/jpeg', 'image/png'],
}) => {
  ...
};

// ❌ 悪い例
const handleData = (data: any) => { ... };  // any型使用
const result: object = { ... };  // 具体的な型を使用すべき
```

### 4. コンポーネント構成

**概要**: 一貫した構成でコンポーネントを記述

```typescript
// 1. インポート（順序を守る）
import { useState, useCallback } from 'react';
import { useTaskStore } from '@/stores/taskStore';
import { Button } from '@/components/common/Button';
import type { ReviewTask } from '@/types/task';

// 2. 型定義
type TaskCardProps = {
  task: ReviewTask;
  onSelect: (taskId: string) => void;
};

// 3. コンポーネント定義
export const TaskCard: React.FC<TaskCardProps> = ({ task, onSelect }) => {
  // 3.1 hooks（状態、副作用）
  const [isExpanded, setIsExpanded] = useState(false);
  const { updateTask } = useTaskStore();
  
  // 3.2 計算・メモ化
  const statusColor = useMemo(() => {
    switch (task.status) {
      case 'completed': return 'text-green-500';
      case 'failed': return 'text-red-500';
      default: return 'text-gray-500';
    }
  }, [task.status]);
  
  // 3.3 イベントハンドラ
  const handleClick = useCallback(() => {
    onSelect(task.taskId);
  }, [task.taskId, onSelect]);
  
  // 3.4 JSX
  return (
    <div className="task-card" onClick={handleClick}>
      <span className={statusColor}>{task.status}</span>
    </div>
  );
};
```

### 5. 状態管理（Zustand）

**概要**: Zustandを使用したグローバルステート管理

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ✅ 良い例 - ストア定義
type TaskState = {
  tasks: ReviewTask[];
  currentTask: ReviewTask | null;
  isLoading: boolean;
  error: string | null;
};

type TaskActions = {
  setTasks: (tasks: ReviewTask[]) => void;
  setCurrentTask: (task: ReviewTask | null) => void;
  addTask: (task: ReviewTask) => void;
  updateTaskStatus: (taskId: string, status: TaskStatus) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
};

export const useTaskStore = create<TaskState & TaskActions>()(
  persist(
    (set) => ({
      // State
      tasks: [],
      currentTask: null,
      isLoading: false,
      error: null,
      
      // Actions
      setTasks: (tasks) => set({ tasks }),
      setCurrentTask: (task) => set({ currentTask: task }),
      addTask: (task) => set((state) => ({ 
        tasks: [...state.tasks, task] 
      })),
      updateTaskStatus: (taskId, status) => set((state) => ({
        tasks: state.tasks.map((t) => 
          t.taskId === taskId ? { ...t, status } : t
        ),
      })),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
    }),
    { name: 'task-storage' }
  )
);
```

### 6. データフェッチ（SWR）

**概要**: SWRを使用したデータ取得とキャッシュ管理

```typescript
import useSWR from 'swr';
import useSWRMutation from 'swr/mutation';

// ✅ 良い例 - フェッチャー定義
const fetcher = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// ✅ 良い例 - データ取得フック
export const useReview = (taskId: string) => {
  const { data, error, isLoading, mutate } = useSWR<ReviewTask>(
    taskId ? `/api/reviews/${taskId}` : null,
    fetcher,
    {
      refreshInterval: 5000, // ポーリング
      revalidateOnFocus: true,
    }
  );

  return {
    task: data,
    isLoading,
    isError: !!error,
    error,
    refresh: mutate,
  };
};

// ✅ 良い例 - ミューテーションフック
export const useCreateReview = () => {
  const { trigger, isMutating, error } = useSWRMutation(
    '/api/reviews',
    async (url: string, { arg }: { arg: { file: File } }) => {
      const formData = new FormData();
      formData.append('image', arg.file);
      
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      
      return response.json();
    }
  );

  return {
    createReview: trigger,
    isCreating: isMutating,
    error,
  };
};
```

### 7. スタイリング（Tailwind CSS）

**概要**: Tailwind CSSを使用したスタイリング

```typescript
// ✅ 良い例 - Tailwindクラスの使用
export const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary',
  size = 'md',
  children,
  ...props 
}) => {
  const baseClasses = 'rounded font-medium transition-colors focus:outline-none focus:ring-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-400',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]}`}
      {...props}
    >
      {children}
    </button>
  );
};

// ✅ 良い例 - tailwind-mergeの使用
import { twMerge } from 'tailwind-merge';

const className = twMerge(
  'px-4 py-2 bg-blue-500',
  isActive && 'bg-blue-700',
  customClassName
);
```

### 8. エラーハンドリング

**概要**: 適切なエラーハンドリングとユーザーフィードバック

```typescript
// ✅ 良い例 - API呼び出しのエラーハンドリング
export const useUploadImage = () => {
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(async (file: File) => {
    try {
      setError(null);
      
      if (file.size > MAX_FILE_SIZE) {
        throw new Error('ファイルサイズが大きすぎます');
      }
      
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: createFormData(file),
      });

      if (!response.ok) {
        throw new Error(`アップロードに失敗しました: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : '不明なエラー';
      setError(message);
      throw err;
    }
  }, []);

  return { upload, error };
};

// ✅ 良い例 - ErrorBoundary
import { ErrorBoundary } from 'react-error-boundary';

const ErrorFallback = ({ error, resetErrorBoundary }) => (
  <div className="error-container">
    <p>エラーが発生しました: {error.message}</p>
    <button onClick={resetErrorBoundary}>再試行</button>
  </div>
);

<ErrorBoundary FallbackComponent={ErrorFallback}>
  <App />
</ErrorBoundary>
```

### 9. パフォーマンス最適化

**概要**: React.memo、useCallback、useMemoを適切に使用

```typescript
// ✅ 良い例 - React.memoでコンポーネント最適化
const TaskCard = React.memo<TaskCardProps>(({ task, onSelect }) => {
  return <div onClick={() => onSelect(task.taskId)}>{task.status}</div>;
});

// ✅ 良い例 - useCallbackでコールバック最適化
const handleSubmit = useCallback((file: File) => {
  uploadImage(file);
}, [uploadImage]);

// ✅ 良い例 - useMemoで計算結果キャッシュ
const completedTasks = useMemo(() => {
  return tasks.filter(task => task.status === 'completed');
}, [tasks]);

// ✅ 良い例 - 遅延ローディング
const ReviewPage = React.lazy(() => import('./pages/Review'));

<Suspense fallback={<Loading />}>
  <ReviewPage />
</Suspense>
```

### 10. アクセシビリティ

**概要**: a11y対応を考慮したコンポーネント実装

```typescript
// ✅ 良い例 - アクセシビリティ対応
<button
  type="button"
  aria-label="画像をアップロード"
  aria-busy={isUploading}
  disabled={isUploading}
>
  {isUploading ? 'アップロード中...' : 'アップロード'}
</button>

<img
  src={imageUrl}
  alt="アップロードされたデッサン画像"
  loading="lazy"
/>

// ✅ 良い例 - フォーカス管理
<input
  id="file-input"
  type="file"
  aria-describedby="file-help"
/>
<p id="file-help">JPEG、PNG形式、最大10MB</p>
```
