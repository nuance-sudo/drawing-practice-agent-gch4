'use client';

import { useState } from 'react';
import { ImageUpload } from '@/components/features/upload/ImageUpload';
import { api } from '@/lib/api';

export const UploadSection = () => {
    const [isUploading, setIsUploading] = useState(false);

    const onUpload = async (file: File) => {
        setIsUploading(true);
        try {
            await api.uploadImage(file);
        } finally {
            setIsUploading(false);
        }
    };

    return <ImageUpload onUpload={onUpload} isUploading={isUploading} />;
};
