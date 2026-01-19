import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ReviewTask, TaskStatus } from '@/types/task';

type TaskState = {
    tasks: ReviewTask[];
    currentTaskId: string | null;
    isLoading: boolean;
    error: string | null;
};

type TaskActions = {
    setTasks: (tasks: ReviewTask[]) => void;
    addTask: (task: ReviewTask) => void;
    updateTask: (taskId: string, updates: Partial<ReviewTask>) => void;
    setCurrentTaskId: (taskId: string | null) => void;
    setLoading: (isLoading: boolean) => void;
    setError: (error: string | null) => void;
};

export const useTaskStore = create<TaskState & TaskActions>()(
    persist(
        (set) => ({
            // State
            tasks: [],
            currentTaskId: null,
            isLoading: false,
            error: null,

            // Actions
            setTasks: (tasks) => set({ tasks }),
            addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
            updateTask: (taskId, updates) =>
                set((state) => ({
                    tasks: state.tasks.map((t) =>
                        t.taskId === taskId ? { ...t, ...updates } : t
                    ),
                })),
            setCurrentTaskId: (currentTaskId) => set({ currentTaskId }),
            setLoading: (isLoading) => set({ isLoading }),
            setError: (error) => set({ error }),
        }),
        {
            name: 'headers-task-storage', // Changed from task-storage to avoid conflicts if any
        }
    )
);
