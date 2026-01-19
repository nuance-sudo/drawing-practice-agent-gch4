import useSWR from 'swr';
import { api } from '@/lib/api';
import type { ReviewTask } from '@/types/task';

export const useTasks = () => {
    const { data, error, isLoading, mutate } = useSWR<ReviewTask[]>(
        '/api/tasks',
        api.getTasks
    );

    return {
        tasks: data || [],
        isLoading,
        isError: error,
        mutate,
    };
};

export const useTask = (taskId: string | null) => {
    const { data, error, isLoading } = useSWR<ReviewTask | undefined>(
        taskId ? `/api/tasks/${taskId}` : null,
        () => (taskId ? api.getTask(taskId) : undefined)
    );

    return {
        task: data,
        isLoading,
        isError: error,
    };
};
