import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatScore(score: number): string {
    return `${score}%`;
}

export function getScoreColor(score: number): string {
    if (score >= 80) return 'text-green-700 dark:text-green-400';
    if (score >= 60) return 'text-yellow-700 dark:text-yellow-400';
    return 'text-red-700 dark:text-red-400';
}

export function getScoreBackgroundColor(score: number): string {
    if (score >= 80) return 'bg-green-50 border-green-200';
    if (score >= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
}

export function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
}

export function capitalizeFirst(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

export function formatSimilarity(similarity: number): string {
    return `${Math.round(similarity * 100)}%`;
}

export function debounce<T extends (...args: any[]) => void>(
    func: T,
    delay: number
): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

export function validateFile(file: File): { valid: boolean; error?: string } {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/gif',
        'image/bmp',
        'image/tiff'
    ];

    if (file.size > maxSize) {
        return { valid: false, error: 'File size must be less than 10MB' };
    }

    if (!allowedTypes.includes(file.type)) {
        return { valid: false, error: 'File type not supported. Please upload PDF, DOCX, or image files.' };
    }

    return { valid: true };
}

export function getFileTypeIcon(filetype: string): string {
    switch (filetype) {
        case 'pdf':
            return '📄';
        case 'docx':
            return '📝';
        case 'image':
            return '🖼️';
        default:
            return '📄';
    }
}
