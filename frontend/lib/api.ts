// API client for ATS Analyzer backend

import { ParseResponse, AnalyzeRequest, AnalyzeResponse, ErrorResponse } from './types';

const API_BASE_URL = process.env.NODE_ENV === 'development'
    ? '/api'  // Proxied to backend during development
    : '/api/v1';  // Direct API routes in production (handled by Vercel)

class APIError extends Error {
    constructor(
        message: string,
        public status: number,
        public code?: string,
        public details?: Record<string, any>
    ) {
        super(message);
        this.name = 'APIError';
    }
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let errorData: ErrorResponse;
        try {
            errorData = await response.json();
        } catch {
            throw new APIError(
                `HTTP ${response.status}: ${response.statusText}`,
                response.status
            );
        }

        throw new APIError(
            errorData.error.message,
            response.status,
            errorData.error.code,
            errorData.error.details
        );
    }

    return response.json();
}

export async function parseResume(file: File): Promise<ParseResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/parse`, {
        method: 'POST',
        body: formData,
    });

    return handleResponse<ParseResponse>(response);
}

export async function analyzeResume(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    return handleResponse<AnalyzeResponse>(response);
}

export async function healthCheck(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${API_BASE_URL}/../health`);
    return handleResponse(response);
}

export { APIError };
