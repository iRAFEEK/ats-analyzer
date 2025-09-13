'use client';

import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Play, RotateCcw, Download, Share2 } from 'lucide-react';

import FileDrop from '@/components/FileDrop';
import ScoreCard from '@/components/ScoreCard';
import WarningsList from '@/components/WarningsList';
import EvidencePanel from '@/components/EvidencePanel';
import LoadingState from '@/components/LoadingState';

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
                    Get instant feedback on how well your résumé matches job descriptions and passes ATS systems
                </p>
            </div>

            {/* Upload Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-4">
                    <h2 className="text-2xl font-semibold text-foreground">Upload Your Résumé</h2>
                    <FileDrop onFileSelect={handleFileSelect} selectedFile={selectedFile} />
                </div>

                <div className="space-y-4">
                    <h2 className="text-2xl font-semibold text-foreground">Job Description</h2>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <div>
                            <textarea
                                {...register('jd_text')}
                                placeholder="Paste the job description here..."
                                className={cn(
                                    'w-full h-40 p-4 border rounded-lg resize-none focus:ring-2 focus:ring-primary focus:border-transparent',
                                    errors.jd_text ? 'border-destructive' : 'border-border'
                                )}
                            />
                            {errors.jd_text && (
                                <p className="text-sm text-destructive mt-1">
                                    {errors.jd_text.message}
                                </p>
                            )}
                        </div>

                        <div className="flex items-center justify-between">
                            <button
                                type="button"
                                onClick={resetAnalysis}
                                disabled={isLoading}
                                className="inline-flex items-center gap-2 px-4 py-2 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
                            >
                                <RotateCcw className="h-4 w-4" />
                                Reset
                            </button>

                            <button
                                type="submit"
                                disabled={!selectedFile || !isValid || isLoading}
                                className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <Play className="h-4 w-4" />
                                {isLoading ? 'Analyzing...' : 'Analyze'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {/* Loading State */}
            {isLoading && (
                <div className="py-12">
                    <LoadingState
                        status={analysisState.status}
                        progress={analysisState.progress}
                        message={
                            analysisState.status === 'parsing'
                                ? 'Parsing your résumé...'
                                : 'Analyzing against job requirements...'
                        }
                    />
                </div>
            )}

            {/* Error State */}
            {hasError && (
                <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6 text-center">
                    <div className="text-destructive font-medium mb-2">Analysis Failed</div>
                    <div className="text-muted-foreground mb-4">
                        {analysisState.error}
                    </div>
                    <button
                        onClick={resetAnalysis}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors"
                    >
                        <RotateCcw className="h-4 w-4" />
                        Try Again
                    </button>
                </div>
            )}

            {/* Results */}
            {hasResults && (
                <div className="space-y-6">
                    <ScoreCard score={analysisState.analysisResult!.score} />

                    <div className="flex items-center justify-end">
                        <div className="flex items-center space-x-3">
                            <button
                                onClick={() => {
                                    // TODO: Implement PDF export
                                    console.log('Export to PDF');
                                }}
                                className="inline-flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
                            >
                                <Download className="h-4 w-4" />
                                Export PDF
                            </button>

                            <button
                                onClick={() => {
                                    // TODO: Implement sharing
                                    console.log('Share results');
                                }}
                                className="inline-flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
                            >
                                <Share2 className="h-4 w-4" />
                                Share Results
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Detailed Results */}
            {hasResults && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <WarningsList ats={analysisState.analysisResult!.ats} />
                    <EvidencePanel
                        evidence={analysisState.analysisResult!.evidence}
                        missing={analysisState.analysisResult!.missing}
                        weaklySupported={analysisState.analysisResult!.weakly_supported}
                    />
                </div>
            )}

            {/* Features Section */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-12">
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
    );
}
