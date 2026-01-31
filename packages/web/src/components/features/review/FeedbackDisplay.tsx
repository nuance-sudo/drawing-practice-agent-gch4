import { Star, TrendingUp, Equal, AlertTriangle } from 'lucide-react';
import type { ReviewTask, Feedback, CategoryFeedback } from '@/types/task';
import { clsx } from 'clsx';
import { ExampleImageDisplay } from './ExampleImageDisplay';

type FeedbackDisplayProps = {
    task: ReviewTask;
    feedback: Feedback;
    rankAtReview: string;
};

export const FeedbackDisplay = ({ task, feedback, rankAtReview }: FeedbackDisplayProps) => {
    const isGenerating = task.status === 'processing' && !task.exampleImageUrl;
    const generationFailed = task.status === 'completed' && !task.exampleImageUrl;
    const isAnnotating = task.status === 'processing' && !task.annotatedImageUrl;
    const annotationFailed = task.status === 'completed' && !task.annotatedImageUrl;

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
                />
            </div>

            {/* Categories Grid */}
            <div className="grid md:grid-cols-3 gap-6">
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
                    title="線の質"
                    data={feedback.details.lineQuality}
                    icon="✏️"
                    color="purple"
                />
            </div>

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
    color: 'blue' | 'indigo' | 'purple';
}) => {
    const colors = {
        blue: 'bg-blue-50 text-blue-900 border-blue-100 ring-blue-500',
        indigo: 'bg-indigo-50 text-indigo-900 border-indigo-100 ring-indigo-500',
        purple: 'bg-purple-50 text-purple-900 border-purple-100 ring-purple-500',
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
