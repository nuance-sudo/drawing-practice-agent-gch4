'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';
import type { ReviewTask } from '@/types/task';

type Props = {
    tasks: ReviewTask[];
    selectedDate?: string;
    onSelectDate: (date: string) => void;
};

export const CalendarFilter = ({ tasks, selectedDate, onSelectDate }: Props) => {
    const [currentMonth, setCurrentMonth] = useState(new Date());

    const getDaysInMonth = (year: number, month: number) => {
        return new Date(year, month + 1, 0).getDate();
    };

    const getFirstDayOfMonth = (year: number, month: number) => {
        return new Date(year, month, 1).getDay();
    };

    const handlePrevMonth = () => {
        setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
    };

    const handleNextMonth = () => {
        setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
    };

    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);

    // 日付ごとのタスク数を集計
    const taskCounts = tasks.reduce((acc, task) => {
        const date = task.createdAt.split('T')[0];
        acc[date] = (acc[date] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const days = [];
    // Before month filler
    for (let i = 0; i < firstDay; i++) {
        days.push(<div key={`empty-${i}`} className="h-9 w-9" />);
    }

    // Days in month
    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const count = taskCounts[dateStr] || 0;
        const isSelected = selectedDate === dateStr;
        const isToday = new Date().toISOString().split('T')[0] === dateStr;

        days.push(
            <button
                key={day}
                onClick={() => onSelectDate(isSelected ? '' : dateStr)}
                className={`
                    relative h-9 w-9 rounded-lg text-sm font-medium flex items-center justify-center transition-all
                    ${isSelected
                        ? 'bg-blue-600 text-white shadow-md shadow-blue-200'
                        : isToday
                            ? 'bg-blue-50 text-blue-600 font-bold border border-blue-100'
                            : 'text-slate-700 hover:bg-slate-100'
                    }
                `}
            >
                {day}
                {count > 0 && !isSelected && (
                    <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-blue-500" />
                )}
                {count > 0 && isSelected && (
                    <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-white/70" />
                )}
            </button>
        );
    }

    return (
        <div className="rounded-2xl bg-white border border-slate-100 shadow-sm p-4 w-full">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                        <CalendarIcon className="w-4 h-4 text-blue-500" />
                        {year}年 {month + 1}月
                    </h3>
                    {selectedDate && (
                        <button
                            onClick={() => onSelectDate('')}
                            className="text-xs text-slate-400 hover:text-slate-600 font-medium px-2 py-0.5 rounded-full hover:bg-slate-50 transition-colors"
                        >
                            解除
                        </button>
                    )}
                </div>
                <div className="flex gap-1">
                    <button
                        onClick={handlePrevMonth}
                        className="p-1.5 rounded-lg hover:bg-slate-50 text-slate-500 hover:text-slate-700 transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4" />
                    </button>
                    <button
                        onClick={handleNextMonth}
                        className="p-1.5 rounded-lg hover:bg-slate-50 text-slate-500 hover:text-slate-700 transition-colors"
                    >
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-7 gap-1 text-center mb-1">
                {['日', '月', '火', '水', '木', '金', '土'].map(d => (
                    <div key={d} className="text-xs font-medium text-slate-400 h-6 flex items-center justify-center">
                        {d}
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-7 gap-1 place-items-center">
                {days}
            </div>
        </div>
    );
};
