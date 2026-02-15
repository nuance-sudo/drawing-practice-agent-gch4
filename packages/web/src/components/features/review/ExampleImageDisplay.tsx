/**
 * お手本画像表示コンポーネント
 * 
 * 元のデッサンとAI生成されたお手本画像を並列表示し、
 * 生成中の状態も適切に表示する。
 */

import React from 'react';

interface ExampleImageDisplayProps {
  /** 元画像のURL */
  originalImageUrl: string;
  /** アノテーション画像のURL（生成完了時のみ） */
  annotatedImageUrl?: string;
  /** お手本画像のURL（生成完了時のみ） */
  exampleImageUrl?: string;
  /** 画像生成中かどうか */
  isGenerating: boolean;
  /** 画像生成に失敗したかどうか */
  generationFailed?: boolean;
  /** アノテーション生成中かどうか */
  isAnnotating?: boolean;
  /** アノテーション生成に失敗したかどうか */
  annotationFailed?: boolean;
  /** 画像生成リトライコールバック */
  onRetryImages?: () => void;
  /** リトライ中かどうか */
  isRetrying?: boolean;
}

export const ExampleImageDisplay: React.FC<ExampleImageDisplayProps> = ({
  originalImageUrl,
  annotatedImageUrl,
  exampleImageUrl,
  isGenerating,
  generationFailed = false,
  isAnnotating = false,
  annotationFailed = false,
  onRetryImages,
  isRetrying = false,
}) => {
  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          デッサン比較
        </h2>
        <p className="text-sm text-gray-600">
          改善点を修正したお手本と比較できます
        </p>
      </div>

      {/* 画像比較エリア */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 元画像 */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">
              あなたのデッサン
            </h3>
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
              オリジナル
            </span>
          </div>

          <div className="relative">
            <img
              src={originalImageUrl}
              alt="あなたのデッサン"
              className="w-full rounded-lg shadow-md border border-gray-200"
            />
          </div>
        </div>

        {/* アノテーション画像 */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">
              改善ポイント
            </h3>
            <span className="px-2 py-1 bg-amber-100 text-amber-800 text-xs font-medium rounded-full">
              注目箇所
            </span>
          </div>

          <div className="relative">
            {isRetrying && !annotatedImageUrl ? (
              <div className="flex items-center justify-center h-64 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border-2 border-dashed border-amber-300">
                <div className="text-center space-y-4">
                  <div className="w-12 h-12 border-4 border-amber-200 border-t-amber-600 rounded-full animate-spin mx-auto"></div>
                  <div className="space-y-2">
                    <p className="text-gray-700 font-medium">
                      再生成中...
                    </p>
                    <p className="text-sm text-gray-500">
                      アノテーション画像を再生成しています
                    </p>
                  </div>
                </div>
              </div>
            ) : isAnnotating ? (
              <div className="flex items-center justify-center h-64 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-center space-y-4">
                  <div className="relative">
                    <div className="w-12 h-12 border-4 border-amber-200 border-t-amber-600 rounded-full animate-spin mx-auto"></div>
                    <div className="absolute inset-0 w-12 h-12 border-4 border-transparent border-r-amber-400 rounded-full animate-pulse mx-auto"></div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-gray-700 font-medium">
                      アノテーションを生成中...
                    </p>
                    <p className="text-sm text-gray-500">
                      改善点の注目箇所を抽出しています
                    </p>
                  </div>
                </div>
              </div>
            ) : annotatedImageUrl ? (
              <img
                src={annotatedImageUrl}
                alt="アノテーション画像"
                className="w-full rounded-lg shadow-md border border-gray-200"
              />
            ) : annotationFailed ? (
              <div className="flex items-center justify-center h-64 bg-red-50 rounded-lg border-2 border-dashed border-red-200">
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto">
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-red-700 font-medium">
                      アノテーション生成に失敗しました
                    </p>
                    {onRetryImages && (
                      <button
                        onClick={onRetryImages}
                        disabled={isRetrying}
                        className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        再試行する
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center mx-auto">
                    <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <p className="text-gray-600">
                    アノテーションはまだ生成されていません
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* お手本画像 */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">
              お手本画像
            </h3>
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
              改善例
            </span>
          </div>

          <div className="relative">
            {isRetrying && !exampleImageUrl ? (
              <div className="flex items-center justify-center h-64 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border-2 border-dashed border-blue-300">
                <div className="text-center space-y-4">
                  <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
                  <div className="space-y-2">
                    <p className="text-gray-700 font-medium">
                      再生成中...
                    </p>
                    <p className="text-sm text-gray-500">
                      お手本画像を再生成しています
                    </p>
                  </div>
                </div>
              </div>
            ) : isGenerating ? (
              // 生成中の表示
              <div className="flex items-center justify-center h-64 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-center space-y-4">
                  {/* アニメーションスピナー */}
                  <div className="relative">
                    <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
                    <div className="absolute inset-0 w-12 h-12 border-4 border-transparent border-r-green-400 rounded-full animate-pulse mx-auto"></div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-gray-700 font-medium">
                      お手本画像を生成中...
                    </p>
                    <p className="text-sm text-gray-500">
                      AI（Gemini 2.5 Flash Image）が<br />
                      改善例を作成しています
                    </p>
                  </div>

                  {/* プログレスバー風のアニメーション */}
                  <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden mx-auto">
                    <div className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full animate-pulse"></div>
                  </div>
                </div>
              </div>
            ) : exampleImageUrl ? (
              // 生成完了時の表示
              <div className="space-y-3">
                <img
                  src={exampleImageUrl}
                  alt="お手本デッサン"
                  className="w-full rounded-lg shadow-md border border-gray-200"
                />
              </div>
            ) : generationFailed ? (
              // 生成失敗時の表示
              <div className="flex items-center justify-center h-64 bg-red-50 rounded-lg border-2 border-dashed border-red-200">
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto">
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-red-700 font-medium">
                      お手本画像の生成に失敗しました
                    </p>
                    {onRetryImages && (
                      <button
                        onClick={onRetryImages}
                        disabled={isRetrying}
                        className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        再試行する
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              // 初期状態（まだ生成されていない）
              <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center mx-auto">
                    <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <p className="text-gray-600">
                    お手本画像はまだ生成されていません
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};