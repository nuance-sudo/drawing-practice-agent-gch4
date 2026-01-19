'use client';

import { ImageUpload } from '@/components/features/upload/ImageUpload';
import { useTasks } from '@/hooks/useTasks';
import { api } from '@/lib/api';

export const UploadSection = () => {
    const { mutate } = useTasks();

    const onUpload = async (file: File) => {
        // In a real app, handle error/loading state here or in ImageUpload
        // ImageUpload has isUploading prop, so we should probably manage local state here
        // But for now, just await api
        await api.uploadImage(file);
        mutate();
    };

    return <ImageUpload onUpload={onUpload} />;
};
