'use client';

import React, { useCallback, useState } from 'react';
import { Upload, File, X, AlertCircle } from 'lucide-react';
import { cn, formatFileSize, validateFile } from '@/lib/utils';

interface FileDropProps {
    onFileSelect: (file: File) => void;
    selectedFile?: File;
    onFileRemove?: () => void;
    disabled?: boolean;
    className?: string;
}

export default function FileDrop({
    onFileSelect,
    selectedFile,
    onFileRemove,
    disabled = false,
    className
}: FileDropProps) {
    const [isDragOver, setIsDragOver] = useState(false);
    const [error, setError] = useState<string>('');

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled) {
            setIsDragOver(true);
        }
    }, [disabled]);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);
        setError('');

        if (disabled) return;

        const files = Array.from(e.dataTransfer.files);
        if (files.length === 0) return;

        const file = files[0];
        const validation = validateFile(file);

        if (!validation.valid) {
            setError(validation.error || 'Invalid file');
            return;
        }

        onFileSelect(file);
    }, [disabled, onFileSelect]);

    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        setError('');
        const files = e.target.files;
        if (!files || files.length === 0) return;

        const file = files[0];
        const validation = validateFile(file);

        if (!validation.valid) {
            setError(validation.error || 'Invalid file');
            return;
        }

        onFileSelect(file);

        // Reset input value so same file can be selected again
        e.target.value = '';
    }, [onFileSelect]);

    const handleRemoveFile = useCallback(() => {
        setError('');
        onFileRemove?.();
    }, [onFileRemove]);

    if (selectedFile) {
        return (
            <div className={cn('file-drop-zone has-file', className)}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <File className="h-8 w-8 text-green-600" />
                        <div>
                            <p className="font-medium text-foreground">{selectedFile.name}</p>
                            <p className="text-sm text-muted-foreground">
                                {formatFileSize(selectedFile.size)}
                            </p>
                        </div>
                    </div>
                    {onFileRemove && (
                        <button
                            onClick={handleRemoveFile}
                            disabled={disabled}
                            className="p-1 rounded-full hover:bg-gray-100 disabled:opacity-50"
                            aria-label="Remove file"
                        >
                            <X className="h-5 w-5 text-muted-foreground" />
                        </button>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className={cn('space-y-4', className)}>
            <div
                className={cn(
                    'file-drop-zone',
                    isDragOver && 'drag-over',
                    disabled && 'opacity-50 cursor-not-allowed'
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <div className="space-y-4">
                    <div className="flex justify-center">
                        <Upload className="h-12 w-12 text-muted-foreground" />
                    </div>

                    <div className="text-center space-y-2">
                        <p className="text-lg font-medium text-foreground">
                            Drop your résumé here
                        </p>
                        <p className="text-sm text-muted-foreground">
                            or click to browse files
                        </p>
                        <p className="text-xs text-muted-foreground">
                            Supports PDF, DOCX, and image files (max 10MB)
                        </p>
                    </div>

                    <div className="flex justify-center">
                        <label className="relative">
                            <input
                                type="file"
                                className="sr-only"
                                accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.gif,.bmp,.tiff"
                                onChange={handleFileInput}
                                disabled={disabled}
                            />
                            <span className="inline-flex items-center px-4 py-2 border border-border rounded-md shadow-sm text-sm font-medium text-foreground bg-background hover:bg-muted focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 disabled:opacity-50 cursor-pointer">
                                Choose File
                            </span>
                        </label>
                    </div>
                </div>
            </div>

            {error && (
                <div className="flex items-center space-x-2 text-destructive text-sm">
                    <AlertCircle className="h-4 w-4" />
                    <span>{error}</span>
                </div>
            )}
        </div>
    );
}
