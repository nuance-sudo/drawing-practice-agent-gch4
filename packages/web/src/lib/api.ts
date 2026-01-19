import { getAuthToken } from './auth';
import type { ReviewTask } from '@/types/task';

// 環境変数またはデフォルトのlocalhost
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchWithAuth(path: string, options: RequestInit = {}) {
    const token = await getAuthToken();
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);

    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
    }

    if (response.status === 204) return null;
    return response.json();
}

export const api = {
    getTasks: async (): Promise<ReviewTask[]> => {
        const data = await fetchWithAuth('/reviews');
        return data.tasks; // Response wrapper { tasks: [], total_count }
    },

    getTask: async (taskId: string): Promise<ReviewTask | undefined> => {
        try {
            return await fetchWithAuth(`/reviews/${taskId}`);
        } catch (e) {
            if (e instanceof Error && e.message.includes('404')) return undefined;
            throw e;
        }
    },

    uploadImage: async (file: File): Promise<ReviewTask> => {
        // 1. Get Signed URL
        const contentType = file.type;
        const { upload_url, public_url } = await fetchWithAuth(
            `/reviews/upload-url?content_type=${encodeURIComponent(contentType)}`
        );

        // 2. Upload to GCS
        const uploadRes = await fetch(upload_url, {
            method: 'PUT',
            headers: { 'Content-Type': contentType },
            body: file,
        });

        if (!uploadRes.ok) {
            throw new Error('Upload failed');
        }

        // 3. Create Review Task
        return await fetchWithAuth('/reviews', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_url: public_url,
            }),
        });
    },
};
