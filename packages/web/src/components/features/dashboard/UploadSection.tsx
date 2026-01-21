'use client';

import { ImageUpload } from '@/components/features/upload/ImageUpload';
import { api } from '@/lib/api';

export const UploadSection = () => {
    const onUpload = async (file: File) => {
        // Upload the image - Firestore realtime will automatically update the task list
        await api.uploadImage(file);
    };

    return <ImageUpload onUpload={onUpload} />;
};
