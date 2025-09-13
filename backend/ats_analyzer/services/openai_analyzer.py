"""OpenAI-powered resume analysis service."""

import json
from typing import Dict, List, Optional
import structlog
from openai import OpenAI

from ats_analyzer.api.dto import Score, MissingSkills, Suggestion, Evidence, ATSWarnings
from ats_analyzer.core.config import get_settings

logger = structlog.get_logger(__name__)


class OpenAIAnalyzer:
    """OpenAI-powered resume analyzer."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        
    def _get_client(self) -> OpenAI:
        """Get OpenAI client, lazy initialized."""
        if self.client is None:
            if not self.settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for AI-powered analysis")
            self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        return self.client
    
    def analyze_resume(self, resume_text: str, jd_text: str) -> Dict:
        """Analyze resume against job description using OpenAI."""
        logger.info("Starting OpenAI-powered resume analysis")
        
        try:
            client = self._get_client()
            
            # Create comprehensive analysis prompt
            prompt = self._create_analysis_prompt(resume_text, jd_text)
            max_tokens = 2000
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert ATS (Applicant Tracking System) and resume analyst. Provide accurate, harsh but fair analysis of resume-job fit."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=max_tokens
            )
            
            # Parse the response
            analysis_text = response.choices[0].message.content
            analysis = self._parse_analysis_response(analysis_text)
            
            logger.info("OpenAI analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error("OpenAI analysis failed", error=str(e))
            # Fallback to a basic analysis
            return self._create_fallback_analysis()
    
    def _create_analysis_prompt(self, resume_text: str, jd_text: str) -> str:
        """Create comprehensive analysis prompt for OpenAI."""
        return f"""
Analyze this resume against the job description and provide a detailed assessment.

**RESUME:**
{resume_text}

**JOB DESCRIPTION:**
{jd_text}

Please provide your analysis in the following JSON format (be very strict and harsh in your evaluation):

{{
    "score": {{
        "overall": <0-100 integer, be very harsh - most candidates should score low>,
        "coverage": <0-100 integer, skill match percentage>,
        "experience": <0-100 integer, experience relevance - be harsh about seniority mismatches>,
        "education": <0-100 integer, education fit>
    }},
    "missing_skills": {{
        "required": [<list of missing required skills>],
        "preferred": [<list of missing preferred skills>]
    }},
    "matched_skills": [
        {{
            "skill": "<skill name>",
            "evidence": "<specific quote from resume showing this skill>",
            "confidence": <0.0-1.0 confidence score>
        }}
    ],
    "suggestions": [
        {{
            "issue": "<specific problem>",
            "recommendation": "<specific fix>",
            "priority": "<high/medium/low>"
        }}
    ],
    "ats_warnings": [
        "<specific ATS compatibility issues>"
    ],
    "ats_passes": [
        "<things that are good for ATS>"
    ]
}}

Key areas to analyze:
1. Technical skills match (be very strict about exact skill matches)
2. Experience level and relevance (be harsh about seniority requirements)
3. Education requirements (strict matching)
4. ATS compatibility issues (formatting, keywords, structure)
5. Missing critical qualifications

Remember:
1. Most candidates should score below 50% overall - be very selective
2. Only give high coverage scores if there's strong evidence
3. Be strict about experience relevance - years matter
4. Be harsh but constructive in assessment
5. Consider both obvious and subtle factors
6. Provide specific, actionable recommendations

Provide ONLY the JSON response, no additional text.
"""
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse OpenAI response into structured analysis."""
        try:
            # Try to extract JSON from the response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            analysis = json.loads(response_text)
            
            # Convert to our expected format
            return {
                "score": Score(
                    overall=analysis["score"]["overall"],
                    coverage=analysis["score"]["coverage"], 
                    experience=analysis["score"]["experience"],
                    education=analysis["score"]["education"]
                ),
                "missing": MissingSkills(
                    required=analysis.get("missing_skills", {}).get("required", []),
                    preferred=analysis.get("missing_skills", {}).get("preferred", [])
                ),
                "evidence": [
                    Evidence(
                        skill=match["skill"],
                        section="analysis",
                        quote=match["evidence"],
                        similarity=match["confidence"]
                    ) for match in analysis.get("matched_skills", [])
                ],
                "suggestions": [
                    Suggestion(
                        before=suggestion["issue"],
                        after=suggestion["recommendation"],
                        rationale=f"Priority: {suggestion['priority']}"
                    ) for suggestion in analysis.get("suggestions", [])
                ],
                "ats": ATSWarnings(
                    warnings=analysis.get("ats_warnings", []),
                    passes=analysis.get("ats_passes", [])
                ),
                "weakly_supported": []  # OpenAI provides confidence scores instead
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse OpenAI response", error=str(e), response=response_text[:200])
            return self._create_fallback_analysis()
    
    def _create_fallback_analysis(self) -> Dict:
        """Create fallback analysis when OpenAI fails."""
        return {
            "score": Score(overall=0, coverage=0, experience=0, education=0),
            "missing": MissingSkills(required=["Analysis unavailable"], preferred=[]),
            "evidence": [],
            "suggestions": [
                Suggestion(
                    before="OpenAI analysis failed",
                    after="Please check your OpenAI API key and try again",
                    rationale="Technical issue with AI analysis"
                )
            ],
            "ats": ATSWarnings(
                warnings=["AI analysis unavailable - please check configuration"],
                passes=[]
            ),
            "weakly_supported": []
        }


# Global analyzer instance
_analyzer = OpenAIAnalyzer()


def analyze_with_openai(resume_text: str, jd_text: str) -> Dict:
    """Analyze resume using OpenAI."""
    return _analyzer.analyze_resume(resume_text, jd_text)