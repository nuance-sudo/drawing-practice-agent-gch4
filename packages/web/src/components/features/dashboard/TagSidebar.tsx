'use client';

import { Tag } from 'lucide-react';
import type { ReviewTask } from '@/types/task';

type Props = {
    tasks: ReviewTask[];
    selectedTag?: string;
    onSelectTag: (tag: string) => void;
};

export const TagSidebar = ({ tasks, selectedTag, onSelectTag }: Props) => {
    // タグの集計
    const tagCounts = tasks.reduce((acc, task) => {
        task.tags?.forEach((tag) => {
            acc[tag] = (acc[tag] || 0) + 1;
        });
        return acc;
    }, {} as Record<string, number>);

    // 出現回数順にソート
    const sortedTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]);

    if (sortedTags.length === 0) {
        return null;
    }

    return (
        <div className="rounded-2xl bg-white border border-slate-100 shadow-sm p-4 h-fit sticky top-4">
            <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2 mb-4">
                <Tag className="w-4 h-4 text-blue-500" />
                Tags
            </h3>
            <div className="flex flex-wrap gap-2">
                <button
                    onClick={() => onSelectTag('')}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${!selectedTag
                            ? 'bg-slate-800 text-white shadow-sm'
                            : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                        }`}
                >
                    All
                </button>
                {sortedTags.map(([tag, count]) => (
                    <button
                        key={tag}
                        onClick={() => onSelectTag(selectedTag === tag ? '' : tag)}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${selectedTag === tag
                                ? 'bg-blue-600 text-white shadow-sm'
                                : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                            }`}
                    >
                        <span>{tag}</span>
                        <span className={`px-1 rounded-full text-[10px] ${selectedTag === tag ? 'bg-blue-500/50 text-white' : 'bg-blue-100 text-blue-600'
                            }`}>
                            {count}
                        </span>
                    </button>
                ))}
            </div>
        </div>
    );
};
