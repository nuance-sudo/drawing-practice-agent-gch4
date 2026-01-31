# 実装設計：お手本画像生成へのバウンディング画像統合

## 概要

お手本画像生成時に、元画像に加えてバウンディング画像（アノテーション画像）をGemini APIに渡すことで、改善ポイントにフォーカスした修正を可能にする。

## 実装アプローチ

### 1. 処理フローの変更

#### 現在のフロー
```
annotate_image (非同期) → generate_image (非同期)
       ↓                        ↓
  Firestore更新            Firestore更新
```

#### 新しいフロー
```
annotate_image (同期待ち) → annotated_image_url取得 → generate_image (非同期)
       ↓                                                       ↓
  Firestore更新                                          Firestore更新
```

### 2. 変更コンポーネント

---

### packages/functions/annotate_image/main.py

#### 現状
- 処理完了時にZONE用IDトークン認証後HTTP 200を返す
- Firestoreにannotated_image_urlを保存

#### 変更点
- レスポンスにannotated_image_urlを含める（呼び出し元が取得できるように）

```python
# 現在
return {"status": "success", "path": blob_path}, 200

# 変更後
return {
    "status": "success", 
    "path": blob_path,
    "annotated_image_url": annotated_image_url
}, 200
```

---

### packages/functions/generate_image/main.py

#### 現状
- 元画像URLのみ受け取り
- Gemini APIに元画像のみ渡す

#### 変更点

1. **入力パラメータ追加**
   ```python
   annotated_image_url = request_json.get("annotated_image_url")  # オプショナル
   ```

2. **プロンプト拡張**
   ```python
   # バウンディング画像が提供された場合、プロンプトに追加
   ANNOTATED_IMAGE_REFERENCE = """
   **Reference Annotated Image:**
   The second image shows the original drawing with bounding boxes highlighting areas for improvement.
   Each numbered bounding box corresponds to a specific improvement point listed above.
   
   Pay special attention to these highlighted areas when creating the improved drawing:
   - Focus on correcting the issues within each bounding box
   - Maintain the parts outside the bounding boxes that are already well-executed
   - The numbers in the bounding boxes match the improvement points above
   """
   ```

3. **Gemini API呼び出し変更**
   ```python
   # 元画像のみの場合
   contents = [prompt, original_image]
   
   # アノテーション画像も渡す場合
   contents = [prompt, original_image, annotated_image]
   ```

---

### packages/agent/src/services/annotation_service.py

#### 現状
- Cloud Functionを非同期呼び出し（結果を待たない）

#### 変更点
- 同期呼び出しに変更し、annotated_image_urlを取得して返す

```python
async def generate_annotated_image(...) -> str | None:
    """アノテーション画像生成リクエストを送信し、結果を待つ
    
    Returns:
        生成されたアノテーション画像のURL、または失敗時はNone
    """
    # ... 既存の認証処理 ...
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            self.function_url,
            json=payload,
            headers=headers,
            timeout=120,  # タイムアウトを延長
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("annotated_image_url")
            return None
```

---

### packages/agent/src/services/image_generation_service.py

#### 現状
- original_image_urlのみ受け取り

#### 変更点
- annotated_image_urlを追加パラメータとして受け取る

```python
async def generate_example_image(
    self,
    task_id: str,
    original_image_url: str,
    annotated_image_url: str | None,  # 追加
    analysis: DessinAnalysis,
    user_rank: UserRank,
    motif_tags: List[str]
) -> None:
    # Cloud Function呼び出し時にannotated_image_urlも渡す
    payload = {
        "task_id": task_id,
        "user_id": user_rank.user_id,
        "original_image_url": original_image_url,
        "annotated_image_url": annotated_image_url,  # 追加
        # ...
    }
```

---

### packages/agent/src/api/reviews.py

#### 現状
```python
# アノテーション生成（非同期、結果待たず）
await annotation_service.generate_annotated_image(...)

# お手本画像生成
await image_generation_service.generate_example_image(
    task_id=task_id,
    original_image_url=image_url,
    ...
)
```

#### 変更点
```python
# アノテーション生成（同期待ち）
annotated_image_url = await annotation_service.generate_annotated_image(...)

# お手本画像生成（アノテーション画像URLも渡す）
await image_generation_service.generate_example_image(
    task_id=task_id,
    original_image_url=image_url,
    annotated_image_url=annotated_image_url,  # 追加
    ...
)
```

---

## プロンプト変更詳細

### generate_image/main.py の BASE_PROMPT_TEMPLATE 拡張

```python
ANNOTATED_IMAGE_INSTRUCTION = """
**Annotated Reference Image (Second Image):**
An annotated version of the original drawing is provided as the second image.
This image contains:
- Colored bounding boxes highlighting specific areas that need improvement
- Numbered circles (1, 2, 3...) next to each bounding box
- Each number corresponds to an improvement point listed in "Key Areas for Improvement" above

**Important Instructions for the Annotated Image:**
1. Focus your improvements on the areas within the bounding boxes
2. The numbered improvements above directly correspond to the numbered bounding boxes
3. Preserve the good qualities of areas outside the bounding boxes
4. Use the visual reference to understand exactly WHERE improvements are needed
"""
```

### 使用フロー

```python
def create_generation_prompt(..., has_annotated_image: bool = False):
    # ... 既存の処理 ...
    
    if has_annotated_image:
        prompt += ANNOTATED_IMAGE_INSTRUCTION
    
    return prompt
```

---

## テスト計画

### 単体テスト
- `AnnotationService.generate_annotated_image`がURLを正しく返すこと
- `ImageGenerationService`が新しいパラメータを正しく渡すこと
- `create_generation_prompt`がアノテーション画像用の指示を正しく追加すること

### 統合テスト
- エンドツーエンドで、アノテーション画像URLがお手本画像生成に渡されること
- アノテーション画像がない場合も従来通り動作すること（後方互換性）

### 手動テスト
- 実際にデッサン画像をアップロードし、生成されたお手本画像が改善ポイントを反映していることを確認

---

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| アノテーション生成のタイムアウト | お手本画像生成が始まらない | タイムアウト後はannotated_image_url=Noneで続行 |
| アノテーション失敗 | 改善ポイントが可視化されない | 元画像のみでお手本画像を生成（従来通り） |
| 処理時間の増加 | ユーザー体験の低下 | ステータス表示で進捗を伝える（既存UIで対応済み） |
