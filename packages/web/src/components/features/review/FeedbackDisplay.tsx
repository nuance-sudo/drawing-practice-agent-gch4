import { useState, useCallback } from 'react';
import { Star, TrendingUp, Equal, AlertTriangle, Sprout } from 'lucide-react';
import type { ReviewTask, Feedback, CategoryFeedback, GrowthFeedback } from '@/types/task';
import { clsx } from 'clsx';
import { ExampleImageDisplay } from './ExampleImageDisplay';
import { api } from '@/lib/api';

type FeedbackDisplayProps = {
    task: ReviewTask;
    feedback: Feedback;
    rankAtReview: string;
};

export const FeedbackDisplay = ({ task, feedback, rankAtReview }: FeedbackDisplayProps) => {
    const isGenerating = task.status === 'processing' && !task.exampleImageUrl;
    const generationFailed = (task.status === 'completed' || task.status === 'failed') && !task.exampleImageUrl;
    const isAnnotating = task.status === 'processing' && !task.annotatedImageUrl;
    const annotationFailed = (task.status === 'completed' || task.status === 'failed') && !task.annotatedImageUrl;

    const [isRetrying, setIsRetrying] = useState(false);

    const handleRetryImages = useCallback(async () => {
        setIsRetrying(true);
        try {
            await api.retryImages(task.taskId);
            // Firestore onSnapshotリスナーがリアルタイムでUIを自動更新
        } catch (error) {
            console.error('画像生成リトライに失敗しました:', error);
        } finally {
            setIsRetrying(false);
        }
    }, [task.taskId]);

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl text-white shadow-lg">
                <div>
                    <h2 className="text-3xl font-bold mb-2">総合評価</h2>
                    <div className="flex items-baseline gap-2">
                        <span className="text-5xl font-black">{feedback.overallScore}</span>
                        <span className="text-xl opacity-80">/100</span>
                    </div>
                </div>
                <div className="flex items-center gap-4 bg-white/10 p-4 rounded-2xl backdrop-blur-sm">
                    <div className="text-right">
                        <p className="text-sm opacity-80">審査時のランク</p>
                        <p className="text-2xl font-bold">{rankAtReview}</p>
                    </div>
                    {task.rankChanged ? (
                        <TrendingUp className="w-8 h-8 text-green-300" />
                    ) : (
                        <Equal className="w-8 h-8 opacity-60" />
                    )}
                </div>
            </div>

            {/* お手本画像表示セクション */}
            <div className="bg-white rounded-3xl p-6 shadow-lg border border-gray-100">
                <ExampleImageDisplay
                    originalImageUrl={task.imageUrl}
                    annotatedImageUrl={task.annotatedImageUrl}
                    exampleImageUrl={task.exampleImageUrl}
                    isGenerating={isGenerating}
                    generationFailed={generationFailed}
                    isAnnotating={isAnnotating}
                    annotationFailed={annotationFailed}
                    onRetryImages={handleRetryImages}
                    isRetrying={isRetrying}
                />
            </div>

            {/* Categories Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                <CategoryCard
                    title="プロポーション"
                    data={feedback.details.proportion}
                    icon="📐"
                    color="blue"
                />
                <CategoryCard
                    title="陰影（トーン）"
                    data={feedback.details.shading}
                    icon="🌗"
                    color="indigo"
                />
                <CategoryCard
                    title="質感"
                    data={feedback.details.texture}
                    icon="🎨"
                    color="emerald"
                />
                <CategoryCard
                    title="線の質"
                    data={feedback.details.lineQuality}
                    icon="✏️"
                    color="purple"
                />
            </div>

            {/* Growth Section */}
            {feedback.details.growth && (
                <GrowthCard data={feedback.details.growth} />
            )}

            {/* Strengths & Improvements */}
            <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-green-50 rounded-3xl p-6 border border-green-100">
                    <h3 className="flex items-center gap-2 text-xl font-bold text-green-800 mb-4">
                        <Star className="w-6 h-6 fill-green-600 text-green-600" />
                        良い点
                    </h3>
                    <ul className="space-y-3">
                        {feedback.strengths.map((point, i) => (
                            <li key={i} className="flex gap-3 text-green-900">
                                <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-green-200 rounded-full text-green-700 font-bold text-sm">
                                    {i + 1}
                                </span>
                                {point}
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="bg-amber-50 rounded-3xl p-6 border border-amber-100">
                    <h3 className="flex items-center gap-2 text-xl font-bold text-amber-800 mb-4">
                        <AlertTriangle className="w-6 h-6 text-amber-600" />
                        改善ポイント
                    </h3>
                    <ul className="space-y-3">
                        {feedback.improvements.map((point, i) => (
                            <li key={i} className="flex gap-3 text-amber-900">
                                <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-amber-200 rounded-full text-amber-700 font-bold text-sm">
                                    {i + 1}
                                </span>
                                {point}
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
};

const CategoryCard = ({
    title,
    data,
    icon,
    color,
}: {
    title: string;
    data: CategoryFeedback;
    icon: string;
    color: 'blue' | 'indigo' | 'purple' | 'emerald';
}) => {
    const colors = {
        blue: 'bg-blue-50 text-blue-900 border-blue-100 ring-blue-500',
        indigo: 'bg-indigo-50 text-indigo-900 border-indigo-100 ring-indigo-500',
        purple: 'bg-purple-50 text-purple-900 border-purple-100 ring-purple-500',
        emerald: 'bg-emerald-50 text-emerald-900 border-emerald-100 ring-emerald-500',
    };

    return (
        <div className={clsx('rounded-3xl p-6 border transition-all hover:shadow-md', colors[color])}>
            <div className="flex justify-between items-start mb-4">
                <div className="text-4xl mb-2">{icon}</div>
                <div className="text-3xl font-bold opacity-80">{data.score}</div>
            </div>
            <h3 className="text-lg font-bold mb-3">{title}</h3>
            <ul className="space-y-2 text-sm opacity-90">
                {data.comments.map((comment, i) => (
                    <li key={i} className="flex gap-2">
                        <span className="opacity-60">•</span>
                        {comment}
                    </li>
                ))}
            </ul>
        </div>
    );
};

const GrowthCard = ({ data }: { data: GrowthFeedback }) => {
    const isFirstSubmission = data.score === null;

    return (
        <div className="bg-gradient-to-br from-teal-50 to-cyan-50 rounded-3xl p-6 border border-teal-100 shadow-lg">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <Sprout className="w-8 h-8 text-teal-600" />
                    <h3 className="text-2xl font-bold text-teal-900">成長トラッキング</h3>
                </div>
                {!isFirstSubmission && (
                    <div className="bg-teal-100 px-4 py-2 rounded-full">
                        <span className="text-2xl font-bold text-teal-800">{data.score}</span>
                        <span className="text-sm text-teal-600">/100</span>
                    </div>
                )}
                {isFirstSubmission && (
                    <div className="bg-gray-100 px-4 py-2 rounded-full">
                        <span className="text-sm text-gray-600">初回提出</span>
                    </div>
                )}
            </div>

            <p className="text-teal-800 mb-6 bg-white/50 p-4 rounded-2xl">
                {data.comparisonSummary}
            </p>

            {!isFirstSubmission && (
                <div className="grid md:grid-cols-3 gap-4">
                    {data.improvedAreas.length > 0 && (
                        <div className="bg-white/60 rounded-2xl p-4">
                            <h4 className="font-bold text-teal-800 mb-2 flex items-center gap-2">
                                <TrendingUp className="w-4 h-4" />
                                改善した点
                            </h4>
                            <ul className="space-y-1 text-sm text-teal-700">
                                {data.improvedAreas.map((area, i) => (
                                    <li key={i}>• {area}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {data.consistentStrengths.length > 0 && (
                        <div className="bg-white/60 rounded-2xl p-4">
                            <h4 className="font-bold text-teal-800 mb-2 flex items-center gap-2">
                                <Star className="w-4 h-4" />
                                維持している強み
                            </h4>
                            <ul className="space-y-1 text-sm text-teal-700">
                                {data.consistentStrengths.map((strength, i) => (
                                    <li key={i}>• {strength}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {data.ongoingChallenges.length > 0 && (
                        <div className="bg-white/60 rounded-2xl p-4">
                            <h4 className="font-bold text-teal-800 mb-2 flex items-center gap-2">
                                <AlertTriangle className="w-4 h-4" />
                                継続課題
                            </h4>
                            <ul className="space-y-1 text-sm text-teal-700">
                                {data.ongoingChallenges.map((challenge, i) => (
                                    <li key={i}>• {challenge}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
