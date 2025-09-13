'use client';

import React, { useState } from 'react';
import { Search, Eye, EyeOff, Award, MapPin } from 'lucide-react';
import { Evidence, MissingSkills } from '@/lib/types';
import { cn, formatSimilarity, truncateText, capitalizeFirst } from '@/lib/utils';

interface EvidencePanelProps {
    evidence: Evidence[];
    missing: MissingSkills;
    weaklySupported: string[];
    className?: string;
}

interface EvidenceItemProps {
    evidence: Evidence;
    isExpanded: boolean;
    onToggle: () => void;
}

function EvidenceItem({ evidence, isExpanded, onToggle }: EvidenceItemProps) {
    const getSectionIcon = (section: string) => {
        switch (section.toLowerCase()) {
            case 'experience':
                return '💼';
            case 'projects':
                return '🚀';
            case 'skills':
                return '⚡';
            case 'education':
                return '🎓';
            case 'summary':
                return '📋';
            default:
                return '📄';
        }
    };

    const getSimilarityColor = (similarity: number) => {
        if (similarity >= 0.9) return 'text-green-600 bg-green-50';
        if (similarity >= 0.75) return 'text-blue-600 bg-blue-50';
        return 'text-yellow-600 bg-yellow-50';
    };

    return (
        <div className="evidence-item">
            <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                    <div className="flex-shrink-0 mt-1">
                        <span className="text-lg">{getSectionIcon(evidence.section)}</span>
                    </div>

                    <div className="flex-1 space-y-2">
                        <div className="flex items-center justify-between">
                            <h4 className="font-medium text-foreground">{evidence.skill}</h4>
                            <div className={cn(
                                'px-2 py-1 rounded-full text-xs font-medium',
                                getSimilarityColor(evidence.similarity)
                            )}>
                                {formatSimilarity(evidence.similarity)} match
                            </div>
                        </div>

                        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                            <div className="flex items-center space-x-1">
                                <MapPin className="h-3 w-3" />
                                <span>{capitalizeFirst(evidence.section)} section</span>
                            </div>
                        </div>

                        {isExpanded && (
                            <div className="mt-3 p-3 bg-muted/30 rounded-md">
                                <p className="text-sm text-foreground leading-relaxed">
                                    "{evidence.quote}"
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                <button
                    onClick={onToggle}
                    className="flex-shrink-0 p-1 rounded hover:bg-muted/50 transition-colors"
                    aria-label={isExpanded ? 'Hide context' : 'Show context'}
                >
                    {isExpanded ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                </button>
            </div>
        </div>
    );
}

function MissingSkillsSection({ missing, weaklySupported }: { missing: MissingSkills, weaklySupported: string[] }) {
    if (missing.required.length === 0 && missing.preferred.length === 0 && weaklySupported.length === 0) {
        return null;
    }

    return (
        <div className="space-y-4">
            <h4 className="font-medium text-foreground flex items-center space-x-2">
                <Search className="h-4 w-4" />
                <span>Skills Gap Analysis</span>
            </h4>

            {missing.required.length > 0 && (
                <div className="space-y-2">
                    <h5 className="text-sm font-medium text-destructive">Missing Required Skills</h5>
                    <div className="flex flex-wrap gap-2">
                        {missing.required.map((skill, index) => (
                            <span
                                key={index}
                                className="px-3 py-1 bg-destructive/10 text-destructive text-sm rounded-full border border-destructive/20"
                            >
                                {skill}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {weaklySupported.length > 0 && (
                <div className="space-y-2">
                    <h5 className="text-sm font-medium text-yellow-600">Weakly Supported Skills</h5>
                    <div className="flex flex-wrap gap-2">
                        {weaklySupported.map((skill, index) => (
                            <span
                                key={index}
                                className="px-3 py-1 bg-yellow-50 text-yellow-700 text-sm rounded-full border border-yellow-200"
                            >
                                {skill}
                            </span>
                        ))}
                    </div>
                    <p className="text-xs text-muted-foreground">
                        These skills were found but need stronger evidence or more specific examples.
                    </p>
                </div>
            )}

            {missing.preferred.length > 0 && (
                <div className="space-y-2">
                    <h5 className="text-sm font-medium text-blue-600">Missing Preferred Skills</h5>
                    <div className="flex flex-wrap gap-2">
                        {missing.preferred.map((skill, index) => (
                            <span
                                key={index}
                                className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-200"
                            >
                                {skill}
                            </span>
                        ))}
                    </div>
                    <p className="text-xs text-muted-foreground">
                        Adding these skills could improve your match score.
                    </p>
                </div>
            )}
        </div>
    );
}

export default function EvidencePanel({
    evidence,
    missing,
    weaklySupported,
    className
}: EvidencePanelProps) {
    const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
    const [searchTerm, setSearchTerm] = useState('');

    const toggleExpanded = (index: number) => {
        const newExpanded = new Set(expandedItems);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedItems(newExpanded);
    };

    const filteredEvidence = evidence.filter(item =>
        item.skill.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.section.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className={cn('score-card space-y-6', className)}>
            <div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                    Skill Evidence & Analysis
                </h3>
                <p className="text-sm text-muted-foreground">
                    Evidence found for matched skills and analysis of missing skills
                </p>
            </div>

            <MissingSkillsSection missing={missing} weaklySupported={weaklySupported} />

            {evidence.length > 0 && (
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h4 className="font-medium text-foreground flex items-center space-x-2">
                            <Award className="h-4 w-4" />
                            <span>Matched Skills ({evidence.length})</span>
                        </h4>

                        {evidence.length > 5 && (
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <input
                                    type="text"
                                    placeholder="Search skills..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pl-10 pr-4 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                                />
                            </div>
                        )}
                    </div>

                    <div className="space-y-3 max-h-96 overflow-y-auto">
                        {filteredEvidence.map((item, index) => (
                            <EvidenceItem
                                key={index}
                                evidence={item}
                                isExpanded={expandedItems.has(index)}
                                onToggle={() => toggleExpanded(index)}
                            />
                        ))}
                    </div>

                    {filteredEvidence.length === 0 && searchTerm && (
                        <div className="text-center py-8 text-muted-foreground">
                            <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p>No skills found matching "{searchTerm}"</p>
                        </div>
                    )}
                </div>
            )}

            {evidence.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                    <Award className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No skill evidence available</p>
                    <p className="text-sm">Complete the analysis to see matched skills</p>
                </div>
            )}
        </div>
    );
}
