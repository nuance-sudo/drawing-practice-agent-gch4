# 設計: 審査中ステート表示

## 現状分析

### 問題
`UploadSection.tsx`で`ImageUpload`コンポーネントを使用しているが、`isUploading`プロパティを渡していない。

```tsx
// 現在の実装 (UploadSection.tsx)
return <ImageUpload onUpload={onUpload} />;
```

`ImageUpload`コンポーネント内には既に`isUploading`に対応したUIロジックが実装済み：
- ボタンが無効化される
- スピナーと「審査中...」テキストが表示される
- クリアボタン（×）が無効化される

### 解決策
`UploadSection`コンポーネントで`isUploading`状態を管理し、`ImageUpload`に渡す。

## 変更内容

### [MODIFY] [UploadSection.tsx](file:///home/ec2-user/src/drawing-practice-agent-gch4/packages/web/src/components/features/dashboard/UploadSection.tsx)

1. `useState`を使用して`isUploading`状態を追加
2. `onUpload`関数内で状態を管理（開始時にtrue、完了/エラー時にfalse）
3. `ImageUpload`コンポーネントに`isUploading`プロパティを渡す

```tsx
'use client';

import { useState } from 'react';
import { ImageUpload } from '@/components/features/upload/ImageUpload';
import { api } from '@/lib/api';

export const UploadSection = () => {
    const [isUploading, setIsUploading] = useState(false);

    const onUpload = async (file: File) => {
        setIsUploading(true);
        try {
            await api.uploadImage(file);
        } finally {
            setIsUploading(false);
        }
    };

    return <ImageUpload onUpload={onUpload} isUploading={isUploading} />;
};
```

## 影響範囲
- `UploadSection.tsx`のみの変更
- 既存の`ImageUpload`コンポーネントのAPIは変更なし
