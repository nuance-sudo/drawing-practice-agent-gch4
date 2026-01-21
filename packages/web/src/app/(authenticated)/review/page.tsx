'use client';

import { Suspense } from 'react';
import { useTask } from '@/hooks/useTasks';
import { useRank } from '@/hooks/useRank';
import { FeedbackDisplay } from '@/components/features/review/FeedbackDisplay';
import { Button } from '@/components/common/Button';
import { useSearchParams, useRouter } from 'next/navigation';
import { AlertCircle, ChevronLeft, Loader2 } from 'lucide-react';

export default function ReviewPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen grid place-items-center bg-slate-50">
                <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
            </div>
        }>
            <ReviewContent />
        </Suspense>
    );
}

function ReviewContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const id = searchParams.get('id');
    const { task, isLoading, error } = useTask(id);
    const { rank } = useRank();

    if (!id) return null;

    if (isLoading) {
        return (
            <div className="min-h-screen grid place-items-center bg-slate-50">
                <div className="text-center">
                    <Loader2 className="w-10 h-10 animate-spin text-blue-600 mx-auto mb-4" />
                    <p className="text-slate-500 font-medium">分析データを読み込み中...</p>
                </div>
            </div>
        );
    }

    if (error || !task) {
        return (
            <div className="min-h-screen grid place-items-center bg-slate-50">
                <div className="text-center max-w-md mx-auto p-6">
                    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <AlertCircle className="w-8 h-8 text-red-600" />
                    </div>
                    <h2 className="text-xl font-bold text-slate-900 mb-2">読み込みエラー</h2>
                    <p className="text-slate-500 mb-6">データの取得に失敗しました。もう一度お試しください。</p>
                    <Button onClick={() => router.back()} variant="outline">
                        戻る
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 pb-20">
            {/* Navbarish */}
            <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-slate-200 px-4 py-4">
                <div className="max-w-7xl mx-auto flex items-center gap-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="-ml-2"
                        onClick={() => router.back()}
                    >
                        <ChevronLeft className="w-5 h-5 mr-1" />
                        戻る
                    </Button>
                    <h1 className="font-bold text-lg text-slate-900 truncate">
                        レビュー結果
                    </h1>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid lg:grid-cols-2 gap-8 lg:gap-12">
                    {/* Left Column: Images */}
                    <div className="space-y-8">
                        <div className="bg-white rounded-3xl p-4 shadow-sm border border-slate-100">
                            <h3 className="font-bold text-slate-500 mb-3 px-2">あなたのデッサン</h3>
                            <div className="rounded-2xl overflow-hidden bg-slate-100">
                                <img src={task.imageUrl} alt="Original" className="w-full object-contain" />
                            </div>
                        </div>

                        {task.exampleImageUrl && (
                            <div className="bg-white rounded-3xl p-4 shadow-sm border border-slate-100">
                                <h3 className="font-bold text-purple-600 mb-3 px-2">AIによる改善例</h3>
                                <div className="rounded-2xl overflow-hidden bg-purple-50">
                                    <img src={task.exampleImageUrl} alt="Example" className="w-full object-contain" />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Right Column: Feedback */}
                    <div>
                        {task.status === 'completed' && task.feedback ? (
                            <FeedbackDisplay
                                feedback={task.feedback}
                                rank={rank?.label ?? '10級'}
                            />
                        ) : (
                            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100 text-center">
                                <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
                                <h3 className="text-xl font-bold text-slate-900 mb-2">分析中...</h3>
                                <p className="text-slate-500">
                                    AIがあなたのデッサンを分析しています。<br />
                                    完了までしばらくお待ちください。
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
