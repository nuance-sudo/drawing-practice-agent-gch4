# Walkthrough: 評価基準の適正化とデプロイ自動化

## 概要
ユーザーのデッサン評価基準（プロポーション、陰影、質感、線の質）をランク（10級〜師範）に応じて詳細化しました。
また、デプロイ手順を改善し、`/deploy-app` スキルを実装しました。

## 変更サマリー

| ファイル | 変更内容 |
|---------|---------|
| `packages/agent/src/prompts/coaching.py` | `DESSIN_ANALYSIS_SYSTEM_PROMPT` にランク別の詳細な評価基準（ルーブリック）を追加 |
| `packages/agent/src/models/rank.py` | `Rank.description` プロパティを削除（プロンプトへのロジック移行のため重複排除） |
| `packages/web/src/hooks/useRank.ts` | 認証フックのインポートエラー修正 (`useAuth` -> `useAuthStore`) |
| `packages/infra/DEPLOY_GUIDE.md` | デプロイ手順を更新（Firebase Hosting / Cloud Run） |
| `.agent/skills/deploy-app/SKILL.md` | デプロイ自動化スキルの作成 |
| `packages/agent/src/api/reviews.py` | ランク情報を分析ツールに渡すように修正 |
| `packages/agent/src/services/rank_service.py` | ランク昇格ロジックの調整 |
| `packages/agent/src/tools/analysis.py` | ランク情報をプロンプトに注入するよう修正 |

## テスト・検証
- [x] ローカルでのTypeScript型チェック（`packages/web`）
- [x] バックエンドのビルドとCloud Runへのデプロイ成功
- [x] WebアプリケーションのビルドとFirebase Hostingへのデプロイ成功
- [x] ランク定義の整合性確認

## 関連Issue
- #39 (Feedback Service Implementation)

## 次のステップ
- ユーザーによる実際のアップロードと評価フィードバックの品質確認
