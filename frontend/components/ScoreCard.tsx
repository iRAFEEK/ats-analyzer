'use client';

import React from 'react';
import { Info } from 'lucide-react';
import { Score } from '@/lib/types';
import { formatScore, getScoreColor, getScoreBackgroundColor, cn } from '@/lib/utils';

interface ScoreCardProps {
    score: Score;
    className?: string;
}

interface ScoreItemProps {
    label: string;
    value: number;
    description: string;
    className?: string;
}

function ScoreItem({ label, value, description, className }: ScoreItemProps) {
    return (
        <div className={cn('space-y-2', className)}>
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-foreground">{label}</span>
                    <div className="group relative">
                        <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-popover text-popover-foreground text-xs rounded-md shadow-lg border border-border opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10 w-48">
                            {description}
                        </div>
                    </div>
                </div>
                <span className={cn('text-lg font-bold', getScoreColor(value))}>
                    {formatScore(value)}
                </span>
            </div>

            <div className="w-full bg-muted rounded-full h-2">
                <div
                    className={cn(
                        'h-2 rounded-full transition-all duration-500 ease-out',
                        value >= 80 ? 'bg-green-500' :
                            value >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    )}
                    style={{ width: `${value}%` }}
                />
            </div>
        </div>
    );
}

export default function ScoreCard({ score, className }: ScoreCardProps) {
    return (
        <div className={cn('score-card space-y-6', className)}>
            <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold text-foreground">Analysis Results</h3>
                <div className={cn(
                    'inline-flex items-center justify-center w-20 h-20 rounded-full text-2xl font-bold',
                    getScoreBackgroundColor(score.overall),
                    getScoreColor(score.overall)
                )}>
                    {score.overall}
                </div>
                <p className="text-sm text-muted-foreground">Overall Score</p>
            </div>

            <div className="space-y-4">
                <ScoreItem
                    label="Skill Coverage"
                    value={score.coverage}
                    description="How well your skills match the job requirements. Based on required and preferred skills found in your résumé."
                />

                <ScoreItem
                    label="Experience Relevance"
                    value={score.experience}
                    description="How relevant your work experience is to the position. Considers years of experience, recency, and skill alignment."
                />

                <ScoreItem
                    label="Education Fit"
                    value={score.education}
                    description="How well your educational background matches the job requirements."
                />
            </div>

            <div className="pt-4 border-t border-border">
                <div className="text-xs text-muted-foreground space-y-1">
                    <p>• Scores are calculated using industry-standard ATS algorithms</p>
                    <p>• 80+ is excellent, 60-79 is good, below 60 needs improvement</p>
                    <p>• Focus on missing required skills for the biggest impact</p>
                </div>
            </div>
        </div>
    );
}
