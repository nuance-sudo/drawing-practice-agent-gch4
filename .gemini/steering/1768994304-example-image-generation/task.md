# お手本画像生成機能 実装タスク

## Phase 1: ImageGenerationService基本実装

### [x] Task 1.1: ImageGenerationServiceクラス作成
- [x] `src/services/image_generation_service.py` ファイル作成
- [x] 基本クラス構造の実装
- [x] ランク計算ロジックの実装
- [x] プロンプト生成ロジックの実装

### [x] Task 1.2: プロンプトテンプレート設計
- [x] ベースプロンプトテンプレートの作成
- [x] ランク別説明文の定義
- [x] 改善点別プロンプト調整ロジック

### [x] Task 1.3: 単体テスト作成
- [x] `tests/test_image_generation_service.py` 作成
- [x] ランク計算のテストケース
- [x] プロンプト生成のテストケース

## Phase 2: GeminiService画像生成機能追加

### [x] Task 2.1: GeminiService拡張
- [x] `generate_image` メソッド追加
- [x] Gemini 2.5 Flash Image API統合
- [x] リクエスト/レスポンス処理

### [x] Task 2.2: エラーハンドリング実装
- [x] リトライ機構の実装
- [x] タイムアウト処理
- [x] 例外処理とログ出力

### [x] Task 2.3: 設定管理
- [x] 環境変数の追加
- [x] 設定クラスの更新
- [x] デフォルト値の設定

## Phase 3: StorageService拡張

### [x] Task 3.1: StorageServiceクラス作成/拡張
- [x] ImageGenerationService内に画像保存機能を実装
- [x] 生成画像保存機能の実装
- [x] CDN URL生成機能

### [x] Task 3.2: Cloud Storage設定
- [x] バケット構成の確認
- [x] ディレクトリ構造の実装
- [x] 権限設定の確認

### [x] Task 3.3: 画像処理ユーティリティ
- [x] 画像形式変換（base64 → bytes）
- [x] ファイル名生成ロジック
- [x] メタデータ付与

## Phase 4: ADK Agent統合

### [x] Task 4.1: Agentツール追加
- [x] 既存の `process_review_task` に画像生成機能を統合
- [x] エラーハンドリング

### [x] Task 4.2: Agent処理フロー更新
- [x] `api/reviews.py` の処理フロー修正
- [x] 画像生成ステップの追加
- [x] 非同期処理の実装

### [x] Task 4.3: タスクモデル拡張
- [x] `ReviewTask` モデルの更新
- [x] 画像生成ステータスフィールド追加（example_image_url）

## Phase 5: フロントエンド表示機能

### [x] Task 5.1: 画像表示コンポーネント作成
- [x] `ExampleImageDisplay.tsx` コンポーネント作成
- [x] 元画像とお手本画像の並列表示
- [x] 生成中の状態表示

### [x] Task 5.2: 既存コンポーネント更新
- [x] `FeedbackDisplay.tsx` の更新
- [x] お手本画像セクションの追加
- [x] レスポンシブデザインの調整

### [x] Task 5.3: 状態管理更新
- [x] レビューページでの画像表示統合
- [x] 画像生成状態の管理

## Phase 6: テスト・デバッグ

### [x] Task 6.1: 統合テスト作成
- [x] 包括的な単体テストの実装
- [x] 画像生成フローのテスト
- [x] エラーケースのテスト

### [x] Task 6.2: テスト設定修正
- [x] Google Cloud認証問題の解決
- [x] モック設定の最適化
- [x] 全テストケースの成功確認

### [ ] Task 6.3: パフォーマンステスト
- [ ] 生成時間の計測
- [ ] 同時リクエスト処理の確認
- [ ] メモリ使用量の監視

## Phase 7: 本番デプロイ

### [ ] Task 7.1: 環境設定
- [ ] 本番環境の環境変数設定
- [ ] Cloud Storage設定
- [ ] IAM権限の確認

### [ ] Task 7.2: デプロイメント
- [ ] Cloud Runサービスの更新
- [ ] 設定ファイルの更新
- [ ] デプロイメントスクリプトの実行

### [ ] Task 7.3: 監視・ログ設定
- [ ] メトリクス収集の設定
- [ ] アラート設定
- [ ] ログ監視の設定

## 詳細実装チェックリスト

### ImageGenerationService実装詳細

#### [ ] ランク計算ロジック
```python
def get_target_rank(self, current_rank: Rank) -> Rank:
    """現在のランクからワンランク上のターゲットランクを取得"""
    # 実装内容:
    # - ランク順序の定義
    # - 最上位ランクの処理
    # - エラーハンドリング
```

#### [ ] プロンプト生成ロジック
```python
def create_generation_prompt(
    self,
    analysis: DessinAnalysis,
    target_rank: Rank,
    motif_tags: List[str]
) -> str:
    """ランクと改善点に基づいてプロンプトを生成"""
    # 実装内容:
    # - ベーステンプレートの適用
    # - 改善点の具体的な記述
    # - ランク別調整の適用
```

### GeminiService拡張詳細

#### [ ] 画像生成API呼び出し
```python
async def generate_image(
    self, 
    prompt: str,
    original_image_data: bytes = None
) -> bytes:
    """Gemini 2.5 Flash Imageで画像を生成"""
    # 実装内容:
    # - API リクエストの構築
    # - レスポンス処理
    # - base64デコード
```

#### [ ] リトライ機構
```python
async def generate_with_retry(
    self,
    prompt: str,
    original_image_data: bytes,
    max_retries: int = 3
) -> bytes:
    # 実装内容:
    # - 指数バックオフ
    # - エラー分類
    # - ログ出力
```

### StorageService実装詳細

#### [ ] 画像保存機能
```python
def save_generated_image(
    self,
    image_data: bytes,
    task_id: str,
    user_id: str
) -> str:
    """生成画像をCloud Storageに保存し、CDN URLを返す"""
    # 実装内容:
    # - ファイルパス生成
    # - メタデータ設定
    # - CDN URL構築
```

### Agent統合詳細

#### [ ] ツール実装
```python
@Tool
def generate_example_image(
    self,
    task_id: str,
    original_image_url: str,
    analysis_json: str,
    user_rank_json: str
) -> str:
    # 実装内容:
    # - JSON パース
    # - サービス呼び出し
    # - エラーハンドリング
```

#### [ ] 処理フロー更新
```python
async def process_review_task(self, task_data: dict) -> dict:
    # 実装内容:
    # - 既存フローとの統合
    # - 非同期処理
    # - 状態管理
```

## 完了条件

### 機能完了条件
- [ ] ユーザーがデッサンをアップロードすると、自動的にお手本画像が生成される
- [ ] お手本画像は現在のランクより1つ上のレベルで生成される
- [ ] 分析結果の改善点が視覚的に反映されている
- [ ] 生成失敗時もシステムが正常に動作する
- [ ] フロントエンドで元画像とお手本画像が並列表示される

### 品質完了条件
- [ ] 単体テストカバレッジ80%以上
- [ ] 統合テストが全て通過
- [ ] 画像生成成功率95%以上
- [ ] 平均生成時間60秒以内
- [ ] エラーハンドリングが適切に動作

### デプロイ完了条件
- [ ] 本番環境で正常動作
- [ ] 監視・ログが正常に出力
- [ ] パフォーマンスが要件を満たす
- [ ] セキュリティ要件を満たす

## 注意事項

### 実装時の注意点
- Gemini 2.5 Flash Image APIの制限事項を考慮する
- 画像生成は時間がかかるため、適切な非同期処理を実装する
- 生成失敗時でもユーザー体験を損なわないようにする
- コスト管理のため、不要な生成を避ける仕組みを検討する

### テスト時の注意点
- 実際のAPI呼び出しはコストがかかるため、モックを活用する
- 異なるランク・モチーフでの生成品質を確認する
- エラーケースの網羅的なテストを実施する

### デプロイ時の注意点
- 本番環境でのAPI制限・コストを確認する
- 段階的なロールアウトを検討する
- 監視体制を整えてからデプロイする