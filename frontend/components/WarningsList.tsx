'use client';

import React from 'react';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { ATSWarnings } from '@/lib/types';
import { cn } from '@/lib/utils';

interface WarningsListProps {
    ats: ATSWarnings;
    className?: string;
}

interface WarningItemProps {
    type: 'warning' | 'success';
    message: string;
    fix?: string;
}

function WarningItem({ type, message, fix }: WarningItemProps) {
    const isWarning = type === 'warning';

    return (
        <div className={cn(
            'flex items-start space-x-3 p-4 rounded-lg border-l-4',
            isWarning
                ? 'bg-destructive/10 border-destructive text-destructive-foreground'
                : 'bg-green-50 border-green-500 text-green-800'
        )}>
            <div className="flex-shrink-0 mt-0.5">
                {isWarning ? (
                    <AlertTriangle className="h-5 w-5" />
                ) : (
                    <CheckCircle className="h-5 w-5" />
                )}
            </div>

            <div className="flex-1 space-y-1">
                <p className="text-sm font-medium">{message}</p>
                {fix && (
                    <p className="text-xs opacity-90">
                        <strong>Fix:</strong> {fix}
                    </p>
                )}
            </div>
        </div>
    );
}

const warningFixes: Record<string, string> = {
    'Multi-column layout detected': 'Use a single-column format to ensure ATS can read your content sequentially.',
    'Table-like formatting may break parsers': 'Replace tables with simple bullet points or plain text formatting.',
    'Low text density': 'Ensure your résumé has sufficient text content. Avoid image-heavy designs.',
    'Unusual characters detected': 'Use standard fonts and avoid special symbols that may not render properly.',
    'No email address found': 'Include a professional email address in your contact information.',
    'No phone number found': 'Add your phone number to your contact details.',
    'Missing or unclear section headers': 'Use clear, standard section headers like "Experience", "Education", "Skills".',
    'Resume appears too short': 'Add more detail about your experience, projects, and achievements.',
    'Resume may be too long': 'Condense your content to 1-2 pages, focusing on most relevant information.',
    'Non-standard characters found': 'Use standard ASCII characters and avoid special symbols or emojis.',
    'Excessive bullet points': 'Limit bullet points to 3-5 per role, focusing on key achievements.',
};

export default function WarningsList({ ats, className }: WarningsListProps) {
    const hasWarnings = ats.warnings.length > 0;
    const hasPasses = ats.passes.length > 0;

    if (!hasWarnings && !hasPasses) {
        return (
            <div className={cn('score-card', className)}>
                <div className="text-center py-8">
                    <Info className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No ATS compatibility data available</p>
                </div>
            </div>
        );
    }

    return (
        <div className={cn('score-card space-y-6', className)}>
            <div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                    ATS Compatibility Check
                </h3>
                <p className="text-sm text-muted-foreground">
                    Automated checks for common formatting issues that can break ATS parsing
                </p>
            </div>

            {hasWarnings && (
                <div className="space-y-3">
                    <h4 className="text-md font-medium text-destructive flex items-center space-x-2">
                        <AlertTriangle className="h-4 w-4" />
                        <span>Issues Found ({ats.warnings.length})</span>
                    </h4>

                    <div className="space-y-3">
                        {ats.warnings.map((warning, index) => (
                            <WarningItem
                                key={index}
                                type="warning"
                                message={warning}
                                fix={warningFixes[warning]}
                            />
                        ))}
                    </div>
                </div>
            )}

            {hasPasses && (
                <div className="space-y-3">
                    <h4 className="text-md font-medium text-green-700 flex items-center space-x-2">
                        <CheckCircle className="h-4 w-4" />
                        <span>Good Practices ({ats.passes.length})</span>
                    </h4>

                    <div className="space-y-3">
                        {ats.passes.map((pass, index) => (
                            <WarningItem
                                key={index}
                                type="success"
                                message={pass}
                            />
                        ))}
                    </div>
                </div>
            )}

            <div className="pt-4 border-t border-border">
                <div className="bg-muted/50 rounded-lg p-4">
                    <h5 className="text-sm font-medium text-foreground mb-2">ATS Best Practices</h5>
                    <ul className="text-xs text-muted-foreground space-y-1">
                        <li>• Use standard section headers (Experience, Education, Skills)</li>
                        <li>• Stick to common fonts (Arial, Calibri, Times New Roman)</li>
                        <li>• Avoid images, graphics, and complex formatting</li>
                        <li>• Use bullet points instead of tables or columns</li>
                        <li>• Include keywords from the job description</li>
                        <li>• Save as PDF to preserve formatting</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
