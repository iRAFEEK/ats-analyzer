"""Skill matching service using embeddings and similarity."""

from typing import List, Optional, Tuple
from dataclasses import dataclass

import structlog
from sentence_transformers import SentenceTransformer
import numpy as np
from rapidfuzz import fuzz

from ats_analyzer.api.dto import Evidence, MissingSkills, Suggestion
from ats_analyzer.services.extract import ExtractedEntities, ExtractedSkill
from ats_analyzer.services.jd import JDRequirements, JDRequirement
from ats_analyzer.core.config import get_scoring_config

logger = structlog.get_logger(__name__)


@dataclass
class SkillMatch:
    """Skill match with similarity score."""
    jd_skill: str
    resume_skill: Optional[ExtractedSkill]
    similarity: float
    is_required: bool
    evidence: Optional[Evidence]


@dataclass
class MatchResults:
    """Complete matching results."""
    required_matches: List[SkillMatch]
    preferred_matches: List[SkillMatch]
    missing: MissingSkills
    weakly_supported: List[str]
    suggestions: List[Suggestion]
    evidence: List[Evidence]


class SkillMatcher:
    """Skill matching using embeddings and fuzzy matching."""
    
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.config = get_scoring_config()
        
    def _get_model(self) -> SentenceTransformer:
        """Lazy load sentence transformer model."""
        if self.model is None:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer model")
            except Exception as e:
                logger.warning("Failed to load sentence transformer", error=str(e))
                raise
        return self.model
    
    def calculate_similarity(self, skill1: str, skill2: str) -> float:
        """Calculate similarity between two skills (much more strict and accurate)."""
        skill1_clean = skill1.lower().strip()
        skill2_clean = skill2.lower().strip()
        
        # Exact match gets highest score
        if skill1_clean == skill2_clean:
            return 1.0
        
        # Check for common abbreviations and synonyms (expanded and more accurate)
        synonyms = {
            'js': 'javascript',
            'ts': 'typescript', 
            'py': 'python',
            'ai': 'artificial intelligence',
            'ml': 'machine learning',
            'dl': 'deep learning',
            'nlp': 'natural language processing',
            'cv': 'computer vision',
            'db': 'database',
            'sql': 'structured query language',
            'nosql': 'no sql',
            'api': 'application programming interface',
            'rest': 'representational state transfer',
            'ui': 'user interface',
            'ux': 'user experience',
            'aws': 'amazon web services',
            'gcp': 'google cloud platform',
            'k8s': 'kubernetes',
            'docker': 'containerization',
            'css3': 'css',
            'html5': 'html',
            'node': 'node.js',
            'nodejs': 'node.js',
            'reactjs': 'react',
            'react.js': 'react',
            'vue.js': 'vue',
            'vuejs': 'vue'
        }
        
        # Normalize using synonyms
        skill1_norm = synonyms.get(skill1_clean, skill1_clean)
        skill2_norm = synonyms.get(skill2_clean, skill2_clean)
        
        if skill1_norm == skill2_norm:
            return 0.98
        
        # STRICT: Only allow very high fuzzy matches to proceed
        fuzzy_ratio = fuzz.ratio(skill1_norm, skill2_norm) / 100.0
        
        # If fuzzy match is too low, don't even bother with semantic similarity
        if fuzzy_ratio < 0.7:
            return 0.0
        
        # Very high fuzzy match threshold for acceptance
        if fuzzy_ratio >= 0.95:
            return fuzzy_ratio
        
        # For medium fuzzy scores, be extremely conservative with semantic similarity
        try:
            model = self._get_model()
            embeddings = model.encode([skill1_norm, skill2_norm])
            
            # Calculate cosine similarity
            semantic_sim = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            # MUCH more conservative - require BOTH high fuzzy AND high semantic
            if semantic_sim >= 0.85 and fuzzy_ratio >= 0.85:
                return min(0.9, max(fuzzy_ratio, float(semantic_sim)))
            elif semantic_sim >= 0.8 and fuzzy_ratio >= 0.9:
                return min(0.85, float(semantic_sim))
            else:
                # Reject if either score is too low
                return 0.0
            
        except Exception as e:
            logger.warning("Semantic similarity failed, using fuzzy only", error=str(e))
            # Only return fuzzy if it's very high
            return fuzzy_ratio if fuzzy_ratio >= 0.9 else 0.0
    
    def find_best_match(
        self, 
        jd_skill: str, 
        resume_skills: List[ExtractedSkill]
    ) -> Tuple[Optional[ExtractedSkill], float]:
        """Find best matching resume skill for a JD skill (more accurate matching)."""
        best_skill = None
        best_score = 0.0
        
        # Also check for partial matches within skill names
        jd_skill_words = set(jd_skill.lower().split())
        
        for resume_skill in resume_skills:
            # Try matching against both the extracted name and canonical name
            score1 = self.calculate_similarity(jd_skill, resume_skill.name)
            score2 = self.calculate_similarity(jd_skill, resume_skill.canonical_name)
            
            # Also check for word-level matches for compound skills
            resume_words = set(resume_skill.name.lower().split())
            word_overlap = len(jd_skill_words.intersection(resume_words)) / len(jd_skill_words.union(resume_words))
            
            # Combine different matching approaches
            direct_score = max(score1, score2)
            
            # If there's significant word overlap, boost the score slightly
            if word_overlap >= 0.5 and direct_score >= 0.6:
                direct_score = min(0.9, direct_score + (word_overlap * 0.1))
            
            # Penalize matches that are too generic
            if len(resume_skill.name.split()) == 1 and len(jd_skill.split()) > 1:
                direct_score *= 0.9  # Slight penalty for generic matches
            
            if direct_score > best_score:
                best_score = direct_score
                best_skill = resume_skill
        
        return best_skill, best_score
    
    def match_skills(
        self, 
        jd_requirements: JDRequirements,
        resume_entities: ExtractedEntities
    ) -> MatchResults:
        """Match JD requirements against resume skills."""
        logger.info("Starting skill matching")
        
        required_matches = []
        preferred_matches = []
        evidence = []
        
        # Match required skills
        for jd_req in jd_requirements.required_skills:
            best_skill, similarity = self.find_best_match(
                jd_req.skill, 
                resume_entities.skills
            )
            
            # Create evidence if match is good enough (much stricter validation)
            skill_evidence = None
            if best_skill and similarity >= self.config["similarity_thresholds"]["required_hit"]:
                # STRICT validation: check if the context actually mentions the skill
                context_text = best_skill.context.lower()
                skill_name = jd_req.skill.lower()
                
                # Check if skill name or close variants appear in context
                skill_mentioned = (
                    skill_name in context_text or
                    any(word in context_text for word in skill_name.split() if len(word) > 2)
                )
                
                # Additional word overlap check
                context_words = set(context_text.split())
                skill_words = set(skill_name.split())
                word_overlap = len(skill_words.intersection(context_words)) / len(skill_words) if skill_words else 0
                
                # EXTREMELY strict evidence requirements - require actual mention
                if skill_mentioned and word_overlap >= 0.5:
                    skill_evidence = Evidence(
                        skill=jd_req.skill,
                        section=best_skill.section,
                        quote=best_skill.context,
                        similarity=similarity,
                    )
                    evidence.append(skill_evidence)
                else:
                    # Log rejected matches for debugging
                    logger.warning(
                        "Rejected skill match due to poor context support",
                        jd_skill=jd_req.skill,
                        resume_skill=best_skill.name,
                        similarity=similarity,
                        context=best_skill.context[:100],
                        skill_mentioned=skill_mentioned,
                        word_overlap=word_overlap
                    )
            
            required_matches.append(SkillMatch(
                jd_skill=jd_req.skill,
                resume_skill=best_skill,
                similarity=similarity,
                is_required=True,
                evidence=skill_evidence,
            ))
        
        # Match preferred skills
        for jd_req in jd_requirements.preferred_skills:
            best_skill, similarity = self.find_best_match(
                jd_req.skill,
                resume_entities.skills
            )
            
            # Create evidence if match is good enough (much stricter validation)
            skill_evidence = None
            if best_skill and similarity >= self.config["similarity_thresholds"]["preferred_hit"]:
                # STRICT validation for preferred skills too
                context_text = best_skill.context.lower()
                skill_name = jd_req.skill.lower()
                
                # Check if skill name or close variants appear in context
                skill_mentioned = (
                    skill_name in context_text or
                    any(word in context_text for word in skill_name.split() if len(word) > 2)
                )
                
                # Additional word overlap check
                context_words = set(context_text.split())
                skill_words = set(skill_name.split())
                word_overlap = len(skill_words.intersection(context_words)) / len(skill_words) if skill_words else 0
                
                # EXTREMELY strict evidence requirements for preferred skills too
                if skill_mentioned and word_overlap >= 0.4:
                    skill_evidence = Evidence(
                        skill=jd_req.skill,
                        section=best_skill.section,
                        quote=best_skill.context,
                        similarity=similarity,
                    )
                    evidence.append(skill_evidence)
                else:
                    # Log rejected matches for debugging
                    logger.warning(
                        "Rejected preferred skill match due to poor context support",
                        jd_skill=jd_req.skill,
                        resume_skill=best_skill.name,
                        similarity=similarity,
                        context=best_skill.context[:100],
                        skill_mentioned=skill_mentioned,
                        word_overlap=word_overlap
                    )
            
            preferred_matches.append(SkillMatch(
                jd_skill=jd_req.skill,
                resume_skill=best_skill,
                similarity=similarity,
                is_required=False,
                evidence=skill_evidence,
            ))
        
        # Identify missing and weakly supported skills
        missing_required = []
        missing_preferred = []
        weakly_supported = []
        
        for match in required_matches:
            if match.similarity < self.config["similarity_thresholds"]["required_hit"]:
                missing_required.append(match.jd_skill)
            elif match.similarity < self.config["similarity_thresholds"]["weak_support"]:
                weakly_supported.append(match.jd_skill)
        
        for match in preferred_matches:
            if match.similarity < self.config["similarity_thresholds"]["preferred_hit"]:
                missing_preferred.append(match.jd_skill)
        
        missing = MissingSkills(
            required=missing_required,
            preferred=missing_preferred,
        )
        
        # Generate suggestions (simple template-based for now)
        suggestions = self._generate_suggestions(
            missing_required, 
            weakly_supported,
            resume_entities
        )
        
        logger.info(
            "Skill matching completed",
            required_matches=len(required_matches),
            preferred_matches=len(preferred_matches),
            missing_required=len(missing_required),
            missing_preferred=len(missing_preferred),
            evidence_count=len(evidence),
        )
        
        return MatchResults(
            required_matches=required_matches,
            preferred_matches=preferred_matches,
            missing=missing,
            weakly_supported=weakly_supported,
            suggestions=suggestions,
            evidence=evidence,
        )
    
    def _generate_suggestions(
        self,
        missing_required: List[str],
        weakly_supported: List[str],
        resume_entities: ExtractedEntities
    ) -> List[Suggestion]:
        """Generate improvement suggestions."""
        suggestions = []
        
        # Suggest adding missing required skills
        for skill in missing_required[:3]:  # Limit to top 3
            suggestions.append(Suggestion(
                before="[Skills section]",
                after=f"Add '{skill}' to your skills section with specific examples",
                rationale=f"'{skill}' is a required skill that's missing from your resume"
            ))
        
        # Suggest strengthening weak skills
        for skill in weakly_supported[:2]:  # Limit to top 2
            suggestions.append(Suggestion(
                before="[Experience descriptions]",
                after=f"Include specific examples of using {skill} with measurable results",
                rationale=f"'{skill}' appears weakly supported - add concrete examples"
            ))
        
        # Suggest quantifying experience
        if resume_entities.experience:
            for exp in resume_entities.experience[:1]:  # Just first one
                if not any(char.isdigit() for char in exp.description):
                    suggestions.append(Suggestion(
                        before=exp.description[:50] + "...",
                        after="Add specific metrics and numbers to quantify your impact",
                        rationale="ATS systems favor quantified achievements with concrete numbers"
                    ))
        
        return suggestions


# Global matcher instance
_matcher = SkillMatcher()


def match_skills(
    resume_entities: ExtractedEntities,
    jd_requirements: JDRequirements
) -> MatchResults:
    """Match resume entities against job requirements."""
    return _matcher.match_skills(jd_requirements, resume_entities)
