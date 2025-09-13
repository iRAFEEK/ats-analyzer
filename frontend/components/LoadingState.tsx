'use client';

import React from 'react';
import { Loader2, FileText, Search, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingStateProps {
    status: 'parsing' | 'analyzing';
    progress?: number;
    className?: string;
}

interface LoadingStepProps {
    icon: React.ReactNode;
    title: string;
    description: string;
    isActive: boolean;
    isComplete: boolean;
}

function LoadingStep({ icon, title, description, isActive, isComplete }: LoadingStepProps) {
    return (
        <div className={cn(
            'flex items-start space-x-4 p-4 rounded-lg transition-all duration-300',
            isActive && 'bg-primary/5 border border-primary/20',
            isComplete && 'opacity-75'
        )}>
            <div className={cn(
                'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-colors',
                isActive && 'bg-primary text-primary-foreground',
                isComplete && 'bg-green-500 text-white',
                !isActive && !isComplete && 'bg-muted text-muted-foreground'
            )}>
                {isActive ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                    icon
                )}
            </div>

            <div className="flex-1 space-y-1">
                <h4 className={cn(
                    'font-medium transition-colors',
                    isActive && 'text-foreground',
                    isComplete && 'text-muted-foreground',
                    !isActive && !isComplete && 'text-muted-foreground'
                )}>
                    {title}
                </h4>
                <p className="text-sm text-muted-foreground">
                    {description}
                </p>
            </div>
        </div>
    );
}

export default function LoadingState({ status, progress = 0, className }: LoadingStateProps) {
    const isParsing = status === 'parsing';
    const isAnalyzing = status === 'analyzing';

    const steps = [
        {
            icon: <FileText className="h-5 w-5" />,
            title: 'Parsing Document',
            description: 'Extracting text and analyzing document structure',
            isActive: isParsing,
            isComplete: isAnalyzing,
        },
        {
            icon: <Search className="h-5 w-5" />,
            title: 'Analyzing Content',
            description: 'Matching skills and calculating compatibility scores',
            isActive: isAnalyzing,
            isComplete: false,
        },
        {
            icon: <BarChart3 className="h-5 w-5" />,
            title: 'Generating Report',
            description: 'Preparing detailed analysis and recommendations',
            isActive: false,
            isComplete: false,
        },
    ];

    return (
        <div className={cn('score-card space-y-6', className)}>
            <div className="text-center space-y-2">
                <div className="flex justify-center">
                    <div className="relative">
                        <div className="w-16 h-16 border-4 border-muted rounded-full"></div>
                        <div
                            className="absolute top-0 left-0 w-16 h-16 border-4 border-primary rounded-full transition-all duration-500 ease-out"
                            style={{
                                clipPath: `inset(0 ${100 - progress}% 0 0)`,
                            }}
                        ></div>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <Loader2 className="h-6 w-6 text-primary animate-spin" />
                        </div>
                    </div>
                </div>

                <h3 className="text-lg font-semibold text-foreground">
                    {isParsing ? 'Processing Document...' : 'Analyzing Content...'}
                </h3>

                <p className="text-sm text-muted-foreground">
                    {isParsing
                        ? 'This may take a few seconds for image files or complex documents'
                        : 'Matching your skills against job requirements'
                    }
                </p>

                {progress > 0 && (
                    <div className="w-full max-w-xs mx-auto">
                        <div className="w-full bg-muted rounded-full h-2">
                            <div
                                className="bg-primary h-2 rounded-full transition-all duration-500 ease-out"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{progress}% complete</p>
                    </div>
                )}
            </div>

            <div className="space-y-2">
                {steps.map((step, index) => (
                    <LoadingStep key={index} {...step} />
                ))}
            </div>

            <div className="pt-4 border-t border-border">
                <div className="bg-muted/50 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 mt-0.5">
                            <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                        </div>
                        <div className="text-xs text-muted-foreground space-y-1">
                            <p><strong>Privacy Notice:</strong> Your document is processed locally and securely.</p>
                            <p>No personal information is stored or shared with third parties.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
