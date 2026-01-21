'use client';

import { Loader2, Clock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import type { ReviewTask } from '@/types/task';

type Props = {
    tasks: ReviewTask[];
    loading?: boolean;
    error?: Error | null;
};

export const TaskGrid = ({ tasks, loading, error }: Props) => {
    if (loading) {
        return (
            <div className="flex justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-xl bg-red-50 p-4 text-red-600 flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                <p>タスクの読み込みに失敗しました</p>
            </div>
        );
    }

    if (tasks.length === 0) {
        return (
            <div className="text-center py-12 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                <p className="text-slate-500">条件に一致する履歴が見つかりませんでした</p>
            </div>
        );
    }

    return (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tasks.map((task: ReviewTask) => (
                <Link
                    key={task.taskId}
                    href={`/review?id=${task.taskId}`}
                    className="group relative overflow-hidden rounded-2xl bg-white border border-slate-100 shadow-sm transition-all hover:shadow-md hover:border-blue-100 block"
                >
                    <div className="aspect-square w-full overflow-hidden bg-slate-100 relative">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                            src={task.imageUrl}
                            alt="Drawing"
                            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                        <div className="absolute top-3 right-3">
                            <StatusBadge status={task.status} />
                        </div>
                    </div>

                    <div className="p-4">
                        <div className="flex items-center justify-between text-sm text-slate-500 mb-1">
                            <span>{new Date(task.createdAt).toLocaleDateString()}</span>
                            <span>{new Date(task.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                    </div>
                </Link>
            ))}
        </div>
    );
};

const StatusBadge = ({ status }: { status: string }) => {
    const styles = {
        pending: 'bg-yellow-100/90 text-yellow-700 backdrop-blur-sm',
        processing: 'bg-blue-100/90 text-blue-700 backdrop-blur-sm',
        completed: 'bg-green-100/90 text-green-700 backdrop-blur-sm',
        failed: 'bg-red-100/90 text-red-700 backdrop-blur-sm',
    };

    const icons = {
        pending: Clock,
        processing: Loader2,
        completed: CheckCircle2,
        failed: XCircle,
    };

    const labels = {
        pending: '待機中',
        processing: '分析中',
        completed: '完了',
        failed: 'エラー',
    };

    const Icon = icons[status as keyof typeof icons] || AlertCircle;
    const style = styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-700';

    return (
        <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium shadow-sm ${style}`}>
            <Icon className={`w-3.5 h-3.5 ${status === 'processing' ? 'animate-spin' : ''}`} />
            {labels[status as keyof typeof labels] || status}
        </span>
    );
};
