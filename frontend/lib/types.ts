// Core types for the ATS Analyzer frontend

export interface ParseResponse {
    text: string;
    sections: Record<string, string>;
    meta: {
        filetype: 'pdf' | 'docx' | 'image';
        has_columns: boolean;
        has_tables: boolean;
        extractability_score: number;
        ocr_used: boolean;
    };
}

export interface AnalyzeRequest {
    resume_text: string;
    jd_text: string;
}

export interface Score {
    overall: number;
    coverage: number;
    experience: number;
    education: number;
}

export interface MissingSkills {
    required: string[];
    preferred: string[];
}

export interface Suggestion {
    before: string;
    after: string;
    rationale: string;
}

export interface ATSWarnings {
    warnings: string[];
    passes: string[];
}

export interface Evidence {
    skill: string;
    section: string;
    quote: string;
    similarity: number;
}

export interface AnalyzeResponse {
    score: Score;
    missing: MissingSkills;
    weakly_supported: string[];
    suggestions: Suggestion[];
    ats: ATSWarnings;
    evidence: Evidence[];
}

export interface ErrorResponse {
    error: {
        message: string;
        code?: string;
        details?: Record<string, any>;
    };
    request_id?: string;
}

// Form types
export interface AnalysisForm {
    file?: File;
    jd_text: string;
}

// UI State types
export interface AnalysisState {
    status: 'idle' | 'parsing' | 'analyzing' | 'complete' | 'error';
    parseResult?: ParseResponse;
    analysisResult?: AnalyzeResponse;
    error?: string;
    progress: number;
}
