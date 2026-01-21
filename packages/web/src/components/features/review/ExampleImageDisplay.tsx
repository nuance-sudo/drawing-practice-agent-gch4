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
  /** お手本画像のURL（生成完了時のみ） */
  exampleImageUrl?: string;
  /** 画像生成中かどうか */
  isGenerating: boolean;
  /** 画像生成に失敗したかどうか */
  generationFailed?: boolean;
  /** ユーザーの現在のランク */
  currentRank?: string;
  /** ターゲットランク（ワンランク上） */
  targetRank?: string;
}

export const ExampleImageDisplay: React.FC<ExampleImageDisplayProps> = ({
  originalImageUrl,
  exampleImageUrl,
  isGenerating,
  generationFailed = false,
  currentRank,
  targetRank
}) => {
  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          デッサン比較
        </h2>
        {currentRank && targetRank && (
          <p className="text-sm text-gray-600">
            現在のランク: <span className="font-semibold text-blue-600">{currentRank}</span>
            {' → '}
            目標レベル: <span className="font-semibold text-green-600">{targetRank}</span>
          </p>
        )}
      </div>

      {/* 画像比較エリア */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 元画像 */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">
              あなたのデッサン
            </h3>
            {currentRank && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                {currentRank}レベル
              </span>
            )}
          </div>
          
          <div className="relative">
            <img 
              src={originalImageUrl} 
              alt="あなたのデッサン" 
              className="w-full rounded-lg shadow-md border border-gray-200"
            />
          </div>
        </div>

        {/* お手本画像 */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">
              お手本画像
            </h3>
            {targetRank && (
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                {targetRank}レベル
              </span>
            )}
          </div>

          <div className="relative">
            {isGenerating ? (
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
                      AI（Gemini 2.5 Flash Image）が{targetRank || '上位'}レベルの<br />
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
                
                {/* AI生成の注記 */}
                <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
                  <div className="flex items-start space-x-2">
                    <div className="flex-shrink-0">
                      <svg className="w-4 h-4 text-amber-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-xs text-amber-800">
                        <strong>AI生成画像</strong><br />
                        この画像はGemini 2.5 Flash Imageによって生成されました。
                        実際の手描きではありません。
                      </p>
                    </div>
                  </div>
                </div>
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
                    <p className="text-sm text-red-600 mt-1">
                      テキストフィードバックをご参考ください
                    </p>
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

      {/* 改善ポイントのヒント（お手本画像がある場合） */}
      {exampleImageUrl && !isGenerating && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-blue-900 mb-1">
                お手本画像の活用方法
              </h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 左右の画像を比較して、違いを観察してください</li>
                <li>• 特に改善が必要な部分（プロポーション、陰影、線の質など）に注目</li>
                <li>• 次回の練習時に、お手本の技法を参考にしてください</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};