import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timezone

from services.supabase_service import supabase_service
from services.summary_service import summary_service
from config import Config

logger = logging.getLogger(__name__)

class PersonalityService:
    def __init__(self):
        self.confidence_threshold = Config.MBTI_CONFIDENCE_THRESHOLD
        self.min_sessions = Config.MIN_SESSIONS_FOR_ANALYSIS
        self.supabase = supabase_service
    
    async def update_personality_from_session(self, user_id: str, session_transcript: List[Dict], session_summary: str) -> Dict:
        """Update user's personality profile based on new session data"""
        try:
            # Extract personality evidence from the session
            evidence = await summary_service.extract_personality_evidence(session_transcript, session_summary)
            
            # Get or create personality profile
            profile = self.supabase.get_or_create_personality_profile(user_id)
            
            # Update scores using Bayesian inference
            updated_scores = self._bayesian_update(profile, evidence)
            
            # Prepare updated profile data
            updated_profile = {
                'extroversion_score': updated_scores['extroversion']['score'],
                'sensing_score': updated_scores['sensing']['score'],
                'thinking_score': updated_scores['thinking']['score'],
                'judging_score': updated_scores['judging']['score'],
                'extroversion_confidence': updated_scores['extroversion']['confidence'],
                'sensing_confidence': updated_scores['sensing']['confidence'],
                'thinking_confidence': updated_scores['thinking']['confidence'],
                'judging_confidence': updated_scores['judging']['confidence'],
                'sessions_analyzed': profile.get('sessions_analyzed', 0) + 1
            }
            
            # Update evidence log
            evidence_log = profile.get('evidence_log', [])
            self._add_evidence_to_log(evidence_log, evidence, session_summary)
            updated_profile['evidence_log'] = evidence_log
            
            # Calculate overall confidence
            updated_profile['overall_confidence'] = self._calculate_overall_confidence(updated_profile)
            
            # Update profile in database
            self.supabase.update_personality_profile(user_id, updated_profile)
            
            # Calculate MBTI type
            mbti_type = self._calculate_mbti_type(updated_profile)
            
            return {
                'mbti_type': mbti_type,
                'scores': {
                    'extroversion': updated_profile['extroversion_score'],
                    'sensing': updated_profile['sensing_score'],
                    'thinking': updated_profile['thinking_score'],
                    'judging': updated_profile['judging_score']
                },
                'confidence': {
                    'overall': updated_profile['overall_confidence'],
                    'extroversion': updated_profile['extroversion_confidence'],
                    'sensing': updated_profile['sensing_confidence'],
                    'thinking': updated_profile['thinking_confidence'],
                    'judging': updated_profile['judging_confidence']
                },
                'sessions_analyzed': updated_profile['sessions_analyzed']
            }
            
        except Exception as e:
            logger.error(f"Error updating personality for user {user_id}: {str(e)}")
            return {}
    
    def _calculate_mbti_type(self, profile: Dict) -> str:
        """Calculate MBTI type string (e.g., 'ENTJ')"""
        e_or_i = 'E' if profile.get('extroversion_score', 0.5) > 0.5 else 'I'
        s_or_n = 'S' if profile.get('sensing_score', 0.5) > 0.5 else 'N'
        t_or_f = 'T' if profile.get('thinking_score', 0.5) > 0.5 else 'F'
        j_or_p = 'J' if profile.get('judging_score', 0.5) > 0.5 else 'P'
        return f"{e_or_i}{s_or_n}{t_or_f}{j_or_p}"
    
    def _bayesian_update(self, profile: Dict, evidence: Dict) -> Dict:
        """Update personality scores using Bayesian inference"""
        updated_scores = {}
        
        dimensions = ['extroversion', 'sensing', 'thinking', 'judging']
        
        for dim in dimensions:
            current_score = profile.get(f"{dim}_score", 0.5)
            current_confidence = profile.get(f"{dim}_confidence", 0.0)
            sessions_analyzed = profile.get('sessions_analyzed', 0)
            
            # Get evidence for this dimension
            dim_evidence = evidence.get(dim, {})
            new_evidence_score = dim_evidence.get('score', 0.5)
            evidence_strength = len(dim_evidence.get('evidence', []))
            
            # Calculate evidence weight based on strength (more evidence = higher weight)
            evidence_weight = min(evidence_strength * 0.1, 0.5)  # Cap at 0.5
            
            # Bayesian update formula
            # P(personality|evidence) ∝ P(evidence|personality) * P(personality)
            prior_weight = current_confidence * sessions_analyzed * 0.1
            total_weight = prior_weight + evidence_weight
            
            if total_weight > 0:
                updated_score = (current_score * prior_weight + new_evidence_score * evidence_weight) / total_weight
                updated_confidence = min(current_confidence + evidence_weight * 0.1, 1.0)
            else:
                updated_score = current_score
                updated_confidence = current_confidence
            
            # Ensure score stays in valid range
            updated_score = max(0.0, min(1.0, updated_score))
            
            updated_scores[dim] = {
                'score': updated_score,
                'confidence': updated_confidence
            }
        
        return updated_scores
    
    def _add_evidence_to_log(self, evidence_log: List, evidence: Dict, session_summary: str):
        """Add new evidence to the profile's evidence log"""
        evidence_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'session_summary': session_summary[:500],  # Truncate for storage
            'evidence': evidence
        }
        
        evidence_log.append(evidence_entry)
        
        # Keep only the last 50 evidence entries
        if len(evidence_log) > 50:
            evidence_log[:] = evidence_log[-50:]
    
    def _calculate_overall_confidence(self, profile: Dict) -> float:
        """Calculate overall confidence based on individual dimension confidences and sessions analyzed"""
        individual_confidences = [
            profile.get('extroversion_confidence', 0.0),
            profile.get('sensing_confidence', 0.0),
            profile.get('thinking_confidence', 0.0),
            profile.get('judging_confidence', 0.0)
        ]
        
        avg_confidence = sum(individual_confidences) / len(individual_confidences)
        
        # Apply session-based multiplier (more sessions = higher confidence)
        sessions_analyzed = profile.get('sessions_analyzed', 0)
        session_multiplier = min(sessions_analyzed / 10, 1.0)  # Max at 10 sessions
        
        return min(avg_confidence * session_multiplier, 1.0)
    
    async def get_personality_insights(self, user_id: str) -> Optional[Dict]:
        """Get comprehensive personality insights for a user"""
        try:
            profile = self.supabase.get_personality_profile(user_id)
            
            if not profile:
                return None
            
            # Calculate MBTI type
            mbti_type = self._calculate_mbti_type(profile)
            
            # Calculate personality type descriptions
            type_description = self._get_type_description(mbti_type)
            
            # Get recent evidence
            evidence_log = profile.get('evidence_log', [])
            recent_evidence = evidence_log[-5:] if evidence_log else []
            
            insights = {
                'mbti_type': mbti_type,
                'type_description': type_description,
                'scores': {
                    'extroversion': profile.get('extroversion_score', 0.5),
                    'sensing': profile.get('sensing_score', 0.5),
                    'thinking': profile.get('thinking_score', 0.5),
                    'judging': profile.get('judging_score', 0.5)
                },
                'confidence': {
                    'overall': profile.get('overall_confidence', 0.0),
                    'extroversion': profile.get('extroversion_confidence', 0.0),
                    'sensing': profile.get('sensing_confidence', 0.0),
                    'thinking': profile.get('thinking_confidence', 0.0),
                    'judging': profile.get('judging_confidence', 0.0)
                },
                'facet_bars': self._generate_facet_bars(profile),
                'sessions_analyzed': profile.get('sessions_analyzed', 0),
                'recent_evidence': recent_evidence,
                'created_at': profile.get('created_at'),
                'updated_at': profile.get('updated_at')
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting personality insights for user {user_id}: {str(e)}")
            return None
    
    def _get_type_description(self, mbti_type: str) -> str:
        """Get description for MBTI type"""
        descriptions = {
            'ENTJ': 'The Commander - Natural born leader with strategic thinking',
            'ENTP': 'The Debater - Quick-witted innovator of possibilities',
            'ENFJ': 'The Protagonist - Charismatic and inspiring leader',
            'ENFP': 'The Campaigner - Enthusiastic, creative and sociable free spirits',
            'ESTJ': 'The Executive - Excellent administrator, managing things and people',
            'ESTP': 'The Entrepreneur - Smart, energetic and highly perceptive',
            'ESFJ': 'The Consul - Extraordinarily caring, social and popular',
            'ESFP': 'The Entertainer - Spontaneous, energetic and enthusiastic',
            'INTJ': 'The Architect - Imaginative and strategic thinker',
            'INTP': 'The Thinker - Innovative inventor with unquenchable thirst for knowledge',
            'INFJ': 'The Advocate - Creative and insightful, inspired and independent',
            'INFP': 'The Mediator - Poetic, kind and altruistic, always eager to help',
            'ISTJ': 'The Logistician - Practical and fact-minded, reliable and responsible',
            'ISTP': 'The Virtuoso - Bold and practical experimenter, master of all tools',
            'ISFJ': 'The Protector - Warm-hearted and dedicated, always ready to protect loved ones',
            'ISFP': 'The Adventurer - Flexible and charming artist, always ready to explore new possibilities'
        }
        return descriptions.get(mbti_type, 'Unknown personality type')
    
    def _generate_facet_bars(self, profile: Dict) -> List[Dict]:
        """Generate facet bars for personality visualization"""
        return [
            {
                'dimension': 'Energy',
                'left_label': 'Introversion',
                'right_label': 'Extraversion',
                'score': profile.get('extroversion_score', 0.5),
                'confidence': profile.get('extroversion_confidence', 0.0)
            },
            {
                'dimension': 'Information',
                'left_label': 'Intuition',
                'right_label': 'Sensing',
                'score': profile.get('sensing_score', 0.5),
                'confidence': profile.get('sensing_confidence', 0.0)
            },
            {
                'dimension': 'Decisions',
                'left_label': 'Feeling',
                'right_label': 'Thinking',
                'score': profile.get('thinking_score', 0.5),
                'confidence': profile.get('thinking_confidence', 0.0)
            },
            {
                'dimension': 'Structure',
                'left_label': 'Perceiving',
                'right_label': 'Judging',
                'score': profile.get('judging_score', 0.5),
                'confidence': profile.get('judging_confidence', 0.0)
            }
        ]

# Global instance
personality_service = PersonalityService() 