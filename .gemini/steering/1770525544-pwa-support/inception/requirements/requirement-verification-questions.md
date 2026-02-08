# Requirements Clarification Questions

PWA対応の要件を明確化するため、以下の質問に回答してください。

## Question 1
PWA対応の対象範囲はどれですか？

A) フロントエンドのみ（`packages/web`）
B) フロントエンド + APIヘッダー設定（`packages/web` と `packages/agent`）
C) フロントエンド + Firebase Hosting設定（`packages/web` と `firebase.json`）
D) フロントエンド + API + Functions/Infra まで含める
X) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 2
オフライン対応の方針はどれですか？

A) オフライン対応は不要（最小PWA）
B) 主要ページの基本オフライン表示のみ
C) 画像キャッシュ含む積極的なオフライン対応
X) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 3
インストール導線の要件はどれですか？

A) 自動（ブラウザの標準インストール誘導のみ）
B) 画面内に手動インストール案内を追加
C) iOS向けの手動案内を追加
X) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 4
プッシュ通知の要件はどれですか？

A) 今回は実装しない
B) フロントエンド側の購読UIのみ
C) フロントエンド + サーバー側送信まで
X) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 5
PWAのアイコン/スプラッシュの扱いはどれですか？

A) 既存のアイコン（`public/icon.png` など）を流用
B) 新規アイコンを追加（こちらで設定のみ）
C) アイコン生成まで含める
X) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 6
セキュリティヘッダーの追加方針はどれですか？

A) `next.config.ts` で推奨ヘッダーを追加
B) 追加しない
C) 既存のヘッダー方針に合わせる（詳細はOtherで指定）
X) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 7
完了条件（Definition of Done）はどれですか？

A) LighthouseでPWA判定がPASS
B) インストール可能でホーム画面から起動できる
C) A+B+オフライン動作確認
X) Other (please describe after [Answer]: tag below)

[Answer]:X こっちでやります。スマホで確認出来ればok

