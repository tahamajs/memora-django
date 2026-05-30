"""
AI Service implementations for Local Notion Clone.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import openai
from anthropic import Anthropic
import tiktoken
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AIModel(Enum):
    """Available AI models."""
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"


class WritingStyle(Enum):
    """Writing improvement styles."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    CONCISE = "concise"
    ACADEMIC = "academic"
    CREATIVE = "creative"
    TECHNICAL = "technical"


@dataclass
class AIConfig:
    """AI service configuration."""
    model: AIModel = AIModel.GPT35_TURBO
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model': self.model.value,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'stream': self.stream,
        }


@dataclass
class AIResponse:
    """AI response wrapper."""
    content: str
    model: str
    tokens_used: int
    cost: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIServiceManager:
    """Manager for AI services."""
    
    _openai_client = None
    _anthropic_client = None
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize AI service clients."""
        if cls._initialized:
            return
        
        # Initialize OpenAI
        if settings.OPENAI_API_KEY:
            cls._openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        
        # Initialize Anthropic
        if settings.ANTHROPIC_API_KEY:
            cls._anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("Anthropic client initialized")
        
        cls._initialized = True
    
    @classmethod
    def get_openai_client(cls):
        """Get OpenAI client instance."""
        if not cls._openai_client:
            raise ValueError("OpenAI API key not configured")
        return cls._openai_client
    
    @classmethod
    def get_anthropic_client(cls):
        """Get Anthropic client instance."""
        if not cls._anthropic_client:
            raise ValueError("Anthropic API key not configured")
        return cls._anthropic_client
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if any AI service is available."""
        return bool(cls._openai_client or cls._anthropic_client)


class AIService:
    """Base AI service with common functionality."""
    
    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self.manager = AIServiceManager
        
    def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """Count tokens in text."""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback: approximate token count
            return len(text.split()) * 1.3
    
    def estimate_cost(self, tokens_used: int, model: str) -> float:
        """Estimate API cost based on tokens used."""
        costs = {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
        }
        
        cost_per_1k = costs.get(model, {'input': 0.001, 'output': 0.002})
        return (tokens_used / 1000) * cost_per_1k['output']
    
    def cache_response(self, key: str, response: AIResponse, timeout: int = 3600):
        """Cache AI response."""
        cache.set(f'ai_response_{key}', response, timeout)
    
    def get_cached_response(self, key: str) -> Optional[AIResponse]:
        """Get cached AI response."""
        return cache.get(f'ai_response_{key}')


class SummarizationService(AIService):
    """Service for text summarization."""
    
    def __init__(self, config: Optional[AIConfig] = None):
        if config is None:
            config = AIConfig(
                model=AIModel.GPT35_TURBO,
                temperature=0.3,
                max_tokens=150
            )
        super().__init__(config)
    
    def summarize(self, content: str, style: str = "concise") -> AIResponse:
        """Generate summary of content."""
        cache_key = f'summarize_{hash(content)}_{style}'
        cached = self.get_cached_response(cache_key)
        if cached:
            return cached
        
        from .prompts import SUMMARIZE_PROMPTS
        
        prompt_template = SUMMARIZE_PROMPTS.get(style, SUMMARIZE_PROMPTS['concise'])
        prompt = prompt_template.format(content=content[:4000])  # Limit input size
        
        try:
            client = self.manager.get_openai_client()
            response = client.chat.completions.create(
                model=self.config.model.value,
                messages=[
                    {"role": "system", "content": "You are an expert summarizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            result = AIResponse(
                content=response.choices[0].message.content.strip(),
                model=self.config.model.value,
                tokens_used=response.usage.total_tokens,
                cost=self.estimate_cost(
                    response.usage.total_tokens, 
                    self.config.model.value
                ),
            )
            
            self.cache_response(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            raise
    
    def summarize_batch(self, contents: List[str]) -> List[AIResponse]:
        """Summarize multiple texts."""
        results = []
        for content in contents:
            try:
                result = self.summarize(content)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch summarization failed for content: {e}")
                results.append(AIResponse(
                    content=f"Error: {str(e)}",
                    model="error",
                    tokens_used=0,
                    cost=0
                ))
        return results


class TagGenerationService(AIService):
    """Service for automatic tag generation."""
    
    def __init__(self, config: Optional[AIConfig] = None):
        if config is None:
            config = AIConfig(
                model=AIModel.GPT35_TURBO,
                temperature=0.5,
                max_tokens=100
            )
        super().__init__(config)
    
    def generate_tags(self, content: str, existing_tags: List[str] = None) -> AIResponse:
        """Generate relevant tags for content."""
        cache_key = f'tags_{hash(content)}'
        cached = self.get_cached_response(cache_key)
        if cached:
            return cached
        
        from .prompts import TAG_GENERATION_PROMPT
        
        existing_str = ', '.join(existing_tags) if existing_tags else 'None'
        prompt = TAG_GENERATION_PROMPT.format(
            content=content[:3000],
            existing_tags=existing_str
        )
        
        try:
            client = self.manager.get_openai_client()
            response = client.chat.completions.create(
                model=self.config.model.value,
                messages=[
                    {"role": "system", "content": "You are an expert at content categorization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            # Parse tags from response
            tags_text = response.choices[0].message.content.strip()
            tags = self._parse_tags(tags_text)
            
            result = AIResponse(
                content=json.dumps(tags),
                model=self.config.model.value,
                tokens_used=response.usage.total_tokens,
                cost=self.estimate_cost(
                    response.usage.total_tokens,
                    self.config.model.value
                ),
                metadata={'tags': tags}
            )
            
            self.cache_response(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Tag generation failed: {e}")
            raise
    
    def _parse_tags(self, text: str) -> List[str]:
        """Parse tags from AI response."""
        try:
            # Try JSON parsing first
            tags = json.loads(text)
            if isinstance(tags, list):
                return [t.lower().strip() for t in tags][:10]
        except json.JSONDecodeError:
            pass
        
        # Fallback: extract comma-separated words
        tags = [t.strip().strip('#').lower() 
                for t in text.replace('[', '').replace(']', '')
                           .replace('"', '').replace("'", '')
                           .split(',')]
        return [t for t in tags if t and len(t) > 1][:10]


class WritingImprovementService(AIService):
    """Service for writing improvement."""
    
    def __init__(self, config: Optional[AIConfig] = None):
        if config is None:
            config = AIConfig(
                model=AIModel.GPT4_TURBO,
                temperature=0.7,
                max_tokens=2000
            )
        super().__init__(config)
    
    def improve_text(
        self, 
        content: str, 
        style: WritingStyle = WritingStyle.PROFESSIONAL,
        preserve_tone: bool = True
    ) -> AIResponse:
        """Improve writing style of content."""
        cache_key = f'improve_{hash(content)}_{style.value}'
        cached = self.get_cached_response(cache_key)
        if cached:
            return cached
        
        from .prompts import WRITING_IMPROVEMENT_PROMPTS
        
        prompt_template = WRITING_IMPROVEMENT_PROMPTS.get(
            style.value, 
            WRITING_IMPROVEMENT_PROMPTS['professional']
        )
        
        preserve_instruction = "Maintain the original tone and voice." if preserve_tone else ""
        prompt = prompt_template.format(
            content=content[:5000],
            preserve_instruction=preserve_instruction
        )
        
        try:
            client = self.manager.get_openai_client()
            response = client.chat.completions.create(
                model=self.config.model.value,
                messages=[
                    {"role": "system", "content": "You are an expert writing coach and editor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            result = AIResponse(
                content=response.choices[0].message.content.strip(),
                model=self.config.model.value,
                tokens_used=response.usage.total_tokens,
                cost=self.estimate_cost(
                    response.usage.total_tokens,
                    self.config.model.value
                ),
                metadata={
                    'style': style.value,
                    'original_length': len(content),
                    'improved_length': len(response.choices[0].message.content),
                }
            )
            
            self.cache_response(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Writing improvement failed: {e}")
            raise


class ResearchAnalysisService(AIService):
    """Service for research analysis."""
    
    def __init__(self, config: Optional[AIConfig] = None):
        if config is None:
            config = AIConfig(
                model=AIModel.GPT4,
                temperature=0.7,
                max_tokens=2000
            )
        super().__init__(config)
    
    def analyze_research(
        self,
        query: str,
        context_notes: List[Dict[str, str]],
        depth: str = "comprehensive"
    ) -> AIResponse:
        """Analyze research query with context from notes."""
        cache_key = f'research_{hash(query)}_{depth}'
        cached = self.get_cached_response(cache_key)
        if cached:
            return cached
        
        from .prompts import RESEARCH_ANALYSIS_PROMPT
        
        # Build context from notes
        context_text = "\n\n".join([
            f"Note: {note.get('title', 'Untitled')}\n"
            f"Content: {note.get('content', '')[:1000]}"
            for note in context_notes[:5]
        ])
        
        prompt = RESEARCH_ANALYSIS_PROMPT.format(
            query=query,
            context=context_text,
            depth=depth
        )
        
        try:
            client = self.manager.get_openai_client()
            response = client.chat.completions.create(
                model=self.config.model.value,
                messages=[
                    {"role": "system", "content": "You are an expert research analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            # Parse structured response
            analysis = self._parse_analysis(response.choices[0].message.content)
            
            result = AIResponse(
                content=json.dumps(analysis),
                model=self.config.model.value,
                tokens_used=response.usage.total_tokens,
                cost=self.estimate_cost(
                    response.usage.total_tokens,
                    self.config.model.value
                ),
                metadata=analysis
            )
            
            self.cache_response(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Research analysis failed: {e}")
            raise
    
    def _parse_analysis(self, text: str) -> Dict[str, Any]:
        """Parse structured analysis from AI response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback structure
            return {
                'analysis': text,
                'key_findings': [],
                'sources': [],
                'methodology_suggestions': '',
                'gaps_identified': [],
                'future_directions': []
            }


class ContentAnalysisService(AIService):
    """Service for content analysis and insights."""
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Perform comprehensive content analysis."""
        analyses = {}
        
        # Sentiment analysis
        analyses['sentiment'] = self._analyze_sentiment(content)
        
        # Keyword extraction
        analyses['keywords'] = self._extract_keywords(content)
        
        # Reading level
        analyses['reading_level'] = self._assess_reading_level(content)
        
        # Topic detection
        analyses['topics'] = self._detect_topics(content)
        
        return analyses
    
    def _analyze_sentiment(self, content: str) -> str:
        """Analyze sentiment of content."""
        from .prompts import SENTIMENT_ANALYSIS_PROMPT
        
        try:
            client = self.manager.get_openai_client()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analyze sentiment. Return only: positive, negative, or neutral."},
                    {"role": "user", "content": SENTIMENT_ANALYSIS_PROMPT.format(content=content[:2000])}
                ],
                temperature=0.1,
                max_tokens=10,
            )
            return response.choices[0].message.content.strip().lower()
        except Exception:
            return "neutral"
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content."""
        from .prompts import KEYWORD_EXTRACTION_PROMPT
        
        try:
            client = self.manager.get_openai_client()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract keywords as JSON array."},
                    {"role": "user", "content": KEYWORD_EXTRACTION_PROMPT.format(content=content[:2000])}
                ],
                temperature=0.3,
                max_tokens=100,
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return []
    
    def _assess_reading_level(self, content: str) -> str:
        """Assess reading level of content."""
        # Simple Flesch-Kincaid approximation
        words = content.split()
        sentences = content.replace('!', '.').replace('?', '.').split('.')
        sentences = [s for s in sentences if s.strip()]
        
        if not words or not sentences:
            return "Unknown"
        
        avg_words_per_sentence = len(words) / len(sentences)
        
        if avg_words_per_sentence < 10:
            return "Very Easy"
        elif avg_words_per_sentence < 15:
            return "Easy"
        elif avg_words_per_sentence < 20:
            return "Moderate"
        elif avg_words_per_sentence < 25:
            return "Difficult"
        else:
            return "Very Difficult"
    
    def _detect_topics(self, content: str) -> List[str]:
        """Detect main topics in content."""
        from .prompts import TOPIC_DETECTION_PROMPT
        
        try:
            client = self.manager.get_openai_client()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Detect topics as JSON array."},
                    {"role": "user", "content": TOPIC_DETECTION_PROMPT.format(content=content[:2000])}
                ],
                temperature=0.5,
                max_tokens=100,
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return ["General"]