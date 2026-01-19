'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, X, Image as ImageIcon, CheckCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { Button } from '@/components/common/Button';

type ImageUploadProps = {
    onUpload: (file: File) => Promise<void>;
    isUploading?: boolean;
};

export const ImageUpload = ({ onUpload, isUploading = false }: ImageUploadProps) => {
    const [dragActive, setDragActive] = useState(false);
    const [preview, setPreview] = useState<string | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const validateFile = (file: File) => {
        // 10MB limit
        if (file.size > 10 * 1024 * 1024) {
            alert('10MB以下の画像ファイルを選択してください');
            return false;
        }
        // Type check
        if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
            alert('JPEG, PNG, WebP形式のみ対応しています');
            return false;
        }
        return true;
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const droppedFile = e.dataTransfer.files[0];
            if (validateFile(droppedFile)) {
                setFile(droppedFile);
                setPreview(URL.createObjectURL(droppedFile));
            }
        }
    }, []);

    const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            if (validateFile(selectedFile)) {
                setFile(selectedFile);
                setPreview(URL.createObjectURL(selectedFile));
            }
        }
    }, []);

    const clearFile = useCallback(() => {
        if (preview) URL.revokeObjectURL(preview);
        setFile(null);
        setPreview(null);
        if (inputRef.current) inputRef.current.value = '';
    }, [preview]);

    const handleSubmit = useCallback(async () => {
        if (file) {
            await onUpload(file);
            clearFile();
        }
    }, [file, onUpload, clearFile]);

    return (
        <div className="w-full max-w-xl mx-auto">
            <div
                className={clsx(
                    'relative overflow-hidden rounded-3xl border-2 border-dashed transition-all duration-300 ease-out',
                    dragActive
                        ? 'border-blue-500 bg-blue-50 scale-[1.02]'
                        : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100/50 hover:border-slate-300',
                    preview ? 'h-[400px]' : 'h-[300px]'
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <input
                    ref={inputRef}
                    type="file"
                    className="hidden"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleChange}
                    disabled={isUploading}
                />

                {preview ? (
                    <div className="relative h-full w-full p-4">
                        <img
                            src={preview}
                            alt="Preview"
                            className="h-full w-full object-contain rounded-2xl shadow-sm"
                        />
                        <button
                            onClick={clearFile}
                            disabled={isUploading}
                            className="absolute top-6 right-6 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                        <div className="absolute bottom-6 left-1/2 -translate-x-1/2">
                            <Button
                                onClick={handleSubmit}
                                disabled={isUploading}
                                className="shadow-xl"
                                size="lg"
                            >
                                {isUploading ? (
                                    <span className="flex items-center gap-2">
                                        <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                                        審査中...
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-2">
                                        <CheckCircle className="w-5 h-5" />
                                        この画像で審査する
                                    </span>
                                )}
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
                        <div className={clsx(
                            "group mb-6 rounded-full p-6 transition-colors duration-300",
                            dragActive ? "bg-blue-100 text-blue-600" : "bg-white shadow-sm text-slate-400"
                        )}>
                            <Upload className={clsx(
                                "w-10 h-10 transition-transform duration-300",
                                dragActive ? "scale-110" : "group-hover:scale-110"
                            )} />
                        </div>
                        <h3 className="mb-2 text-xl font-bold text-slate-900">
                            デッサン画像をアップロード
                        </h3>
                        <p className="mb-8 text-slate-500 max-w-xs mx-auto leading-relaxed">
                            ここにドラッグ＆ドロップ、または
                            <button
                                onClick={() => inputRef.current?.click()}
                                className="mx-1 font-semibold text-blue-600 hover:text-blue-700 hover:underline decoration-2 underline-offset-2"
                                disabled={isUploading}
                            >
                                ファイルを選択
                            </button>
                            してください
                        </p>
                        <div className="flex items-center gap-4 text-xs font-medium text-slate-400 bg-white px-4 py-2 rounded-full shadow-sm border border-slate-100">
                            <span className="flex items-center gap-1.5">
                                <ImageIcon className="w-3.5 h-3.5" />
                                JPEG, PNG, WebP
                            </span>
                            <span className="h-3 w-px bg-slate-200" />
                            <span>Max 10MB</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
