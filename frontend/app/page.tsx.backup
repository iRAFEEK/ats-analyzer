'use client';

import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Play, RotateCcw, Download, Share2, TrendingUp } from 'lucide-react';

import FileDrop from '@/components/FileDrop';
import ScoreCard from '@/components/ScoreCard';
import WarningsList from '@/components/WarningsList';
import EvidencePanel from '@/components/EvidencePanel';
import LoadingState from '@/components/LoadingState';
import DetailedAnalysisModal from '@/components/DetailedAnalysisModal';

import { parseResume, analyzeResume, APIError } from '@/lib/api';
import { AnalysisState, AnalysisForm } from '@/lib/types';
import { cn } from '@/lib/utils';

const analysisSchema = z.object({
    jd_text: z.string().min(50, 'Job description must be at least 50 characters'),
});

export default function HomePage() {
    const [analysisState, setAnalysisState] = useState<AnalysisState>({
        status: 'idle',
        progress: 0,
    });
    const [showDetailedAnalysis, setShowDetailedAnalysis] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File>();

    const form = useForm<Pick<AnalysisForm, 'jd_text'>>({
        resolver: zodResolver(analysisSchema),
        mode: 'onChange',
    });

    const {
        register,
        handleSubmit,
        formState: { errors, isValid },
        reset: resetForm,
        getValues,
    } = form;

    const resetAnalysis = useCallback(() => {
        setAnalysisState({
            status: 'idle',
            progress: 0,
        });
        setSelectedFile(undefined);
        resetForm();
    }, [resetForm]);

    const handleFileSelect = useCallback((file: File) => {
        setSelectedFile(file);
        // Clear any previous analysis
        if (analysisState.status !== 'idle') {
            setAnalysisState(prev => ({
                ...prev,
                parseResult: undefined,
                analysisResult: undefined,
                error: undefined,
            }));
        }
    }, [analysisState.status]);

    const handleFileRemove = useCallback(() => {
        setSelectedFile(undefined);
    }, []);

    const onSubmit = async (data: Pick<AnalysisForm, 'jd_text'>) => {
        if (!selectedFile) {
            setAnalysisState(prev => ({
                ...prev,
                error: 'Please select a résumé file',
            }));
            return;
        }

        try {
            // Step 1: Parse the document
            setAnalysisState({
                status: 'parsing',
                progress: 10,
            });

            const parseResult = await parseResume(selectedFile);

            setAnalysisState(prev => ({
                ...prev,
                parseResult,
                progress: 50,
            }));

            // Step 2: Analyze against job description
            setAnalysisState(prev => ({
                ...prev,
                status: 'analyzing',
                progress: 60,
            }));

            const analysisResult = await analyzeResume({
                resume_text: parseResult.text,
                jd_text: data.jd_text,
            });

            setAnalysisState(prev => ({
                ...prev,
                analysisResult,
                status: 'complete',
                progress: 100,
            }));

        } catch (error) {
            console.error('Analysis failed:', error);

            let errorMessage = 'An unexpected error occurred';
            if (error instanceof APIError) {
                errorMessage = error.message;
            } else if (error instanceof Error) {
                errorMessage = error.message;
            }

            setAnalysisState(prev => ({
                ...prev,
                status: 'error',
                error: errorMessage,
                progress: 0,
            }));
        }
    };

    const isLoading = analysisState.status === 'parsing' || analysisState.status === 'analyzing';
    const hasResults = analysisState.status === 'complete' && analysisState.analysisResult;
    const hasError = analysisState.status === 'error';

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            {/* Hero Section */}
            <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold text-foreground">
                    ATS Résumé Analyzer
                </h1>
                <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                    Upload your résumé and job description to get instant feedback on ATS compatibility,
                    skill matching, and personalized improvement suggestions.
                </p>
                <div className="flex items-center justify-center space-x-6 text-sm text-muted-foreground">
                    <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>Privacy-focused</span>
                    </div>
                    <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span>No data stored</span>
                    </div>
                    <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                        <span>Instant results</span>
                    </div>
                </div>
            </div>

            {/* Analysis Form */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-6">
                    <div className="score-card">
                        <h2 className="text-lg font-semibold text-foreground mb-4">
                            1. Upload Your Résumé
                        </h2>
                        <FileDrop
                            onFileSelect={handleFileSelect}
                            selectedFile={selectedFile}
                            onFileRemove={handleFileRemove}
                            disabled={isLoading}
                        />
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="score-card space-y-4">
                        <h2 className="text-lg font-semibold text-foreground">
                            2. Paste Job Description
                        </h2>

                        <div className="space-y-2">
                            <textarea
                                {...register('jd_text')}
                                placeholder="Paste the job description here... Include requirements, responsibilities, and preferred skills for best results."
                                rows={12}
                                disabled={isLoading}
                                className={cn(
                                    'w-full p-4 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-colors',
                                    errors.jd_text
                                        ? 'border-destructive focus:ring-destructive'
                                        : 'border-border'
                                )}
                            />
                            {errors.jd_text && (
                                <p className="text-sm text-destructive">{errors.jd_text.message}</p>
                            )}
                        </div>

                        <div className="flex items-center justify-between pt-4">
                            <button
                                type="button"
                                onClick={resetAnalysis}
                                disabled={isLoading || analysisState.status === 'idle'}
                                className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <RotateCcw className="h-4 w-4" />
                                <span>Reset</span>
                            </button>

                            <button
                                type="submit"
                                disabled={!selectedFile || !isValid || isLoading}
                                className="inline-flex items-center space-x-2 px-6 py-3 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <Play className="h-4 w-4" />
                                <span>{isLoading ? 'Analyzing...' : 'Analyze Résumé'}</span>
                            </button>
                        </div>
                    </form>
                </div>

                <div className="space-y-6">
                    {/* Loading State */}
                    {isLoading && (
                        <LoadingState
                            status={analysisState.status as 'parsing' | 'analyzing'}
                            progress={analysisState.progress}
                        />
                    )}

                    {/* Error State */}
                    {hasError && (
                        <div className="score-card">
                            <div className="text-center space-y-4">
                                <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mx-auto">
                                    <span className="text-2xl">⚠️</span>
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-foreground mb-2">
                                        Analysis Failed
                                    </h3>
                                    <p className="text-sm text-destructive mb-4">
                                        {analysisState.error}
                                    </p>
                                    <button
                                        onClick={resetAnalysis}
                                        className="inline-flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-colors"
                                    >
                                        <RotateCcw className="h-4 w-4" />
                                        <span>Try Again</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Results */}
                    {hasResults && (
                        <div className="space-y-6">
                            <ScoreCard score={analysisState.analysisResult.score} />

                            <div className="flex items-center justify-between">
                                <button
                                    onClick={() => setShowDetailedAnalysis(true)}
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200 shadow-md hover:shadow-lg"
                                >
                                    <TrendingUp className="h-4 w-4" />
                                    View Detailed Analysis
                                </button>

                                <div className="flex items-center space-x-3">
                                    <button
                                        onClick={() => {
                                            // TODO: Implement PDF export
                                            console.log('Export to PDF');
                                        }}
                                        className="inline-flex items-center space-x-2 px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground border border-border rounded-md hover:bg-muted/50 transition-colors"
                                    >
                                        <Download className="h-4 w-4" />
                                        <span>Export PDF</span>
                                    </button>

                                    <button
                                        onClick={() => {
                                            // TODO: Implement sharing
                                            console.log('Share results');
                                        }}
                                        className="inline-flex items-center space-x-2 px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground border border-border rounded-md hover:bg-muted/50 transition-colors"
                                    >
                                        <Share2 className="h-4 w-4" />
                                        <span>Share</span>
                                    </button>
                                </div>
                            </div>
                    )}

                            {/* Placeholder for idle state */}
                            {analysisState.status === 'idle' && (
                                <div className="score-card">
                                    <div className="text-center py-12 space-y-4">
                                        <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto">
                                            <span className="text-2xl">📊</span>
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-semibold text-foreground mb-2">
                                                Ready to Analyze
                                            </h3>
                                            <p className="text-sm text-muted-foreground">
                                                Upload your résumé and paste a job description to get started
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
            </div>

                {/* Detailed Results */}
                {hasResults && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <WarningsList ats={analysisState.analysisResult.ats} />
                        <EvidencePanel
                            evidence={analysisState.analysisResult.evidence}
                            missing={analysisState.analysisResult.missing}
                            weaklySupported={analysisState.analysisResult.weakly_supported}
                        />
                    </div>
                )}

                {/* Additional Info Section */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8">
                    <div className="text-center space-y-3">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto">
                            <span className="text-2xl">🎯</span>
                        </div>
                        <h3 className="font-semibold text-foreground">Accurate Matching</h3>
                        <p className="text-sm text-muted-foreground">
                            Advanced AI algorithms analyze your skills against job requirements with high precision
                        </p>
                    </div>

                    <div className="text-center space-y-3">
                        <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto">
                            <span className="text-2xl">🔒</span>
                        </div>
                        <h3 className="font-semibold text-foreground">Privacy First</h3>
                        <p className="text-sm text-muted-foreground">
                            Your documents are processed securely and never stored or shared
                        </p>
                    </div>

                    <div className="text-center space-y-3">
                        <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto">
                            <span className="text-2xl">💡</span>
                        </div>
                        <h3 className="font-semibold text-foreground">Actionable Insights</h3>
                        <p className="text-sm text-muted-foreground">
                            Get specific recommendations to improve your résumé's ATS compatibility
                        </p>
                    </div>
                </div>
            </div>

            {/* Detailed Analysis Modal */}
            {hasResults && (
                <DetailedAnalysisModal
                    isOpen={showDetailedAnalysis}
                    onClose={() => setShowDetailedAnalysis(false)}
                    resumeText={analysisState.parseResult?.text || ''}
                    jobDescription={getValues('jd_text') || ''}
                />
            )}
        </div>
    );
}
