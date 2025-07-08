import openai
from typing import Dict, List, Optional
import logging
import json
from textblob import TextBlob
from config import Config

logger = logging.getLogger(__name__)

class SummaryService:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key must be configured")
        
        openai.api_key = Config.OPENAI_API_KEY
    
    async def generate_session_summary(self, transcript: List[Dict]) -> str:
        """Generate a concise topic summary of the conversation"""
        try:
            # Combine all messages into a conversation string
            conversation = self._format_transcript(transcript)
            
            prompt = f"""
            Analyze this conversation transcript and provide a concise summary focusing on:
            1. Main topics discussed
            2. User's emotional state and concerns
            3. Personality traits that emerged
            4. Communication style observations
            
            Conversation:
            {conversation}
            
            Provide a structured summary in 2-3 paragraphs:
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert conversational analyst specializing in personality assessment."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating session summary: {str(e)}")
            return "Unable to generate summary"
    
    async def analyze_sentiment(self, transcript: List[Dict]) -> Dict:
        """Analyze sentiment and emotions in the conversation"""
        try:
            conversation = self._format_transcript(transcript)
            
            # Basic sentiment using TextBlob
            blob = TextBlob(conversation)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Enhanced emotion analysis with OpenAI
            prompt = f"""
            Analyze the emotional content of this conversation. Identify:
            1. Primary emotions expressed (joy, sadness, anger, fear, surprise, disgust)
            2. Emotional intensity (1-10 scale)
            3. Emotional stability/volatility
            4. Overall emotional tone
            
            Conversation:
            {conversation}
            
            Return JSON format:
            {{
                "primary_emotions": ["emotion1", "emotion2"],
                "intensity": 7,
                "stability": "stable/volatile",
                "tone": "positive/negative/neutral",
                "confidence": 0.85
            }}
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert emotion analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.2
            )
            
            ai_analysis = json.loads(response.choices[0].message.content.strip())
            
            return {
                "overall_sentiment": polarity,
                "subjectivity": subjectivity,
                "emotions": ai_analysis.get("primary_emotions", []),
                "intensity": ai_analysis.get("intensity", 5),
                "stability": ai_analysis.get("stability", "stable"),
                "tone": ai_analysis.get("tone", "neutral"),
                "confidence": ai_analysis.get("confidence", 0.7)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                "overall_sentiment": 0.0,
                "subjectivity": 0.5,
                "emotions": [],
                "intensity": 5,
                "stability": "unknown",
                "tone": "neutral",
                "confidence": 0.0
            }
    
    async def extract_personality_evidence(self, transcript: List[Dict], summary: str) -> Dict:
        """Extract MBTI-relevant evidence from conversation"""
        try:
            conversation = self._format_transcript(transcript)
            
            prompt = f"""
            Analyze this conversation for MBTI personality indicators. Extract evidence for each dimension:
            
            EXTROVERSION vs INTROVERSION:
            - Energy source (social vs solitary)
            - Communication style (outward vs inward focused)
            - Processing style (external vs internal)
            
            SENSING vs INTUITION:
            - Information preference (concrete vs abstract)
            - Focus (present/practical vs future/possibilities)
            - Details vs big picture
            
            THINKING vs FEELING:
            - Decision making (logic vs values)
            - Conflict approach (objective vs personal)
            - Priorities (efficiency vs harmony)
            
            JUDGING vs PERCEIVING:
            - Structure preference (planned vs flexible)
            - Decision timing (decisive vs exploratory)
            - Lifestyle (organized vs adaptable)
            
            Conversation:
            {conversation}
            
            Summary:
            {summary}
            
            Return JSON with evidence and confidence scores (0-1):
            {{
                "extroversion": {{"evidence": ["quote1", "quote2"], "score": 0.7}},
                "sensing": {{"evidence": ["quote1", "quote2"], "score": 0.3}},
                "thinking": {{"evidence": ["quote1", "quote2"], "score": 0.8}},
                "judging": {{"evidence": ["quote1", "quote2"], "score": 0.6}}
            }}
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert MBTI analyst. Return only valid JSON with specific evidence."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            return json.loads(response.choices[0].message.content.strip())
            
        except Exception as e:
            logger.error(f"Error extracting personality evidence: {str(e)}")
            return {
                "extroversion": {"evidence": [], "score": 0.5},
                "sensing": {"evidence": [], "score": 0.5},
                "thinking": {"evidence": [], "score": 0.5},
                "judging": {"evidence": [], "score": 0.5}
            }
    
    def _format_transcript(self, transcript: List[Dict]) -> str:
        """Format transcript into readable conversation"""
        if not transcript:
            return ""
        
        conversation_lines = []
        for message in transcript:
            speaker = message.get('speaker', 'User')
            content = message.get('content', message.get('text', ''))
            timestamp = message.get('timestamp', '')
            
            conversation_lines.append(f"{speaker}: {content}")
        
        return "\n".join(conversation_lines)

# Global instance
summary_service = SummaryService() 