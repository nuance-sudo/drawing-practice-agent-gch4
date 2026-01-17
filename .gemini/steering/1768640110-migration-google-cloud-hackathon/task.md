# マイグレーションタスク: Google Cloud Hackathon 対応

## 概要
お絵描きコーチングエージェント（/home/ec2-user/src/drawing-practice-agent-gch4/tmp/source-reference）をAWS版からGoogle Cloud版へマイグレーションし、第4回 Agentic AI Hackathon with Google Cloud（https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=rule）の要件に対応する。

## ハッカソン要件

### 必須条件
- [ ] Google Cloud アプリケーション実行プロダクト（Cloud Run等）の使用
- [ ] Google Cloud AI 技術（Vertex AI、Gemini API、ADK等）の使用

### 提出物
- [ ] GitHubリポジトリ（公開）
- [ ] デプロイ済みプロジェクトURL
- [ ] Zenn記事（トピック: gch4）

## ドキュメント作成

### 永続的ドキュメント（docs/）
- [x] product-requirements.md - プロダクト要求定義書
- [x] functional-design.md - 機能設計書
- [x] architecture.md - 技術仕様書
- [x] repository-structure.md - リポジトリ構造定義書
- [x] development-guidelines.md - 開発ガイドライン
- [x] glossary.md - ユビキタス言語定義

### 作業ドキュメント
- [x] task.md - タスクリスト（本ファイル）
- [ ] requirements.md - マイグレーション要求
- [ ] design.md - マイグレーション設計

## 環境設定

- [ ] GCP初期セットアップ
    - [x] gcloud CLIインストール
    - [x] gcloud認証
    - [x] プロジェクト作成・設定

## インフラ変更（AWS → GCP）

### 置き換え対象
| AWS | GCP | ステータス |
|-----|-----|-----------|
| Bedrock AgentCore | Cloud Run + ADK | [ ] |
| S3 | Cloud Storage | [ ] |
| CloudFront | Cloud CDN | [ ] |
| DynamoDB | Firestore | [ ] |
| SQS | Cloud Tasks / Pub/Sub | [ ] |
| Secrets Manager | Secret Manager | [ ] |
| CloudWatch | Cloud Logging / Monitoring | [ ] |
| ECR | Artifact Registry | [ ] |
| IAM (AWS) | IAM (GCP) | [ ] |

## エージェント実装変更

- [ ] Strands Agents → Google ADK への移行検討
- [ ] boto3 → google-cloud-* への置き換え
- [ ] Gemini API呼び出し（Vertex AI経由推奨）

## 検証項目

- [ ] ローカル動作確認
- [ ] Cloud Runデプロイ
- [ ] GitHub Actions連携確認
- [ ] E2Eテスト

## 提出準備

- [ ] Zenn記事作成（カテゴリ: Idea、トピック: gch4）
- [ ] システムアーキテクチャ図
- [ ] デモ動画（3分程度）
