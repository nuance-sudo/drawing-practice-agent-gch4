# Agent Engine APIマイグレーション要件

## 概要
Cloud RunのAPIサーバーから、Vertex AI Agent Engineにデプロイされたエージェントを呼び出す実装を更新する。

## 背景
- エージェントがVertex AI Agent Engineにデプロイ完了
- Cloud RunのAPIサーバーからAgent Engineを呼び出す必要がある
- 現在の`agent_engine_service.py`は古いSDKパターンを使用している
- 公式ドキュメントに基づいて新しいSDKパターンに移行する

## 参考ドキュメント
- https://docs.cloud.google.com/agent-builder/agent-engine/use/overview?hl=ja
- https://docs.cloud.google.com/agent-builder/agent-engine/use/adk?hl=ja

## 要件

### 1. Agent Engine呼び出しの更新
- 新しいVertex AI SDK(`vertexai.Client`)を使用する
- `async_stream_query`メソッドでエージェントにクエリを送信
- セッション管理は必要に応じて実装（現状は不要）

### 2. 互換性維持
- 既存の`reviews.py`からの呼び出しインターフェースは維持
- レスポンス形式は維持

### 3. エラーハンドリング
- Agent Engine呼び出しエラーのハンドリング
- タイムアウト設定の検討

## 制約
- Python 3.12
- 既存のテストが通ること
