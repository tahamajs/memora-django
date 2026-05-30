"""
Views for AI service endpoints.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import logging

from .services import (
    SummarizationService,
    TagGenerationService,
    WritingImprovementService,
    ResearchAnalysisService,
    ContentAnalysisService,
    WritingStyle,
    AIResponse,
)
from .prompts import (
    MEETING_NOTES_PROMPT,
    TASK_EXTRACTION_PROMPT,
)

logger = logging.getLogger(__name__)


class AIRateThrottle(UserRateThrottle):
    """Custom throttle for AI endpoints."""
    rate = '30/minute'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def summarize_text(request):
    """
    Generate a summary of the provided text.
    
    Request body:
    {
        "content": "Text to summarize",
        "style": "concise|detailed|bullets|executive" (optional)
    }
    """
    content = request.data.get('content', '')
    style = request.data.get('style', 'concise')
    
    if not content:
        return Response(
            {'error': 'Content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = SummarizationService()
        result = service.summarize(content, style)
        
        return Response({
            'summary': result.content,
            'model': result.model,
            'tokens_used': result.tokens_used,
            'cost': result.cost,
        })
        
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return Response(
            {'error': 'AI service temporarily unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def generate_tags(request):
    """
    Generate relevant tags for content.
    
    Request body:
    {
        "content": "Text to analyze",
        "existing_tags": ["tag1", "tag2"] (optional)
    }
    """
    content = request.data.get('content', '')
    existing_tags = request.data.get('existing_tags', [])
    
    if not content:
        return Response(
            {'error': 'Content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = TagGenerationService()
        result = service.generate_tags(content, existing_tags)
        
        return Response({
            'tags': result.metadata.get('tags', []),
            'model': result.model,
            'tokens_used': result.tokens_used,
            'cost': result.cost,
        })
        
    except Exception as e:
        logger.error(f"Tag generation error: {e}")
        return Response(
            {'error': 'AI service temporarily unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def improve_writing(request):
    """
    Improve writing style of the provided text.
    
    Request body:
    {
        "content": "Text to improve",
        "style": "professional|casual|concise|academic|creative|technical",
        "preserve_tone": true/false (optional)
    }
    """
    content = request.data.get('content', '')
    style_str = request.data.get('style', 'professional')
    preserve_tone = request.data.get('preserve_tone', True)
    
    if not content:
        return Response(
            {'error': 'Content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        style = WritingStyle(style_str)
        service = WritingImprovementService()
        result = service.improve_text(content, style, preserve_tone)
        
        return Response({
            'improved_content': result.content,
            'style': style.value,
            'metadata': result.metadata,
            'model': result.model,
            'tokens_used': result.tokens_used,
            'cost': result.cost,
        })
        
    except ValueError:
        return Response(
            {'error': f'Invalid style. Choose from: {[s.value for s in WritingStyle]}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Writing improvement error: {e}")
        return Response(
            {'error': 'AI service temporarily unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def research_analysis(request):
    """
    Perform research analysis using AI.
    
    Request body:
    {
        "query": "Research question",
        "context_notes": [{"title": "...", "content": "..."}],
        "depth": "comprehensive|summary" (optional)
    }
    """
    query = request.data.get('query', '')
    context_notes = request.data.get('context_notes', [])
    depth = request.data.get('depth', 'comprehensive')
    
    if not query:
        return Response(
            {'error': 'Query is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = ResearchAnalysisService()
        result = service.analyze_research(query, context_notes, depth)
        
        return Response({
            'analysis': result.metadata,
            'model': result.model,
            'tokens_used': result.tokens_used,
            'cost': result.cost,
        })
        
    except Exception as e:
        logger.error(f"Research analysis error: {e}")
        return Response(
            {'error': 'AI service temporarily unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def analyze_content(request):
    """
    Perform comprehensive content analysis.
    
    Request body:
    {
        "content": "Text to analyze"
    }
    """
    content = request.data.get('content', '')
    
    if not content:
        return Response(
            {'error': 'Content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = ContentAnalysisService()
        analysis = service.analyze_content(content)
        
        return Response(analysis)
        
    except Exception as e:
        logger.error(f"Content analysis error: {e}")
        return Response(
            {'error': 'AI service temporarily unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def organize_meeting_notes(request):
    """
    Convert raw meeting notes into organized minutes.
    
    Request body:
    {
        "content": "Raw meeting notes/transcript"
    }
    """
    content = request.data.get('content', '')
    
    if not content:
        return Response(
            {'error': 'Content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from .services import AIServiceManager
        client = AIServiceManager.get_openai_client()
        
        prompt = MEETING_NOTES_PROMPT.format(content=content[:4000])
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert meeting note organizer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        
        import json
        meeting_notes = json.loads(response.choices[0].message.content)
        
        return Response(meeting_notes)
        
    except Exception as e:
        logger.error(f"Meeting notes organization error: {e}")
        return Response(
            {'error': 'AI service temporarily unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def extract_tasks(request):
    """
    Extract tasks and action items from text.
    
    Request body:
    {
        "content": "Text containing tasks"
    }
    """
    content = request.data.get('content', '')
    
    if not content:
        return Response(
            {'error': 'Content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from .services import AIServiceManager
        client = AIServiceManager.get_openai_client()
        
        prompt = TASK_EXTRACTION_PROMPT.format(content=content[:3000])
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at identifying tasks and action items."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
        )
        
        import json
        tasks = json.loads(response.choices[0].message.content)
        
        return Response({'tasks': tasks})
        
    except Exception as e:
        logger.error(f"Task extraction error: {e}")
        return Response(
            {'error': 'AI service temporarily unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def ai_status(request):
    """
    Check AI service availability and status.
    """
    from .services import AIServiceManager
    
    try:
        is_available = AIServiceManager.is_available()
        
        status_info = {
            'available': is_available,
            'openai_configured': bool(AIServiceManager._openai_client),
            'anthropic_configured': bool(AIServiceManager._anthropic_client),
            'models_available': [
                model.value for model in AIModel
            ] if is_available else [],
        }
        
        return Response(status_info)
        
    except Exception as e:
        return Response({
            'available': False,
            'error': str(e)
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usage_stats(request):
    """
    Get AI usage statistics for the current user.
    """
    # This would typically query a database for usage stats
    # For now, return cached stats or empty stats
    stats = cache.get(f'ai_usage_{request.user.id}') or {
        'total_requests': 0,
        'total_tokens': 0,
        'total_cost': 0.0,
        'requests_by_type': {},
        'last_used': None,
    }
    
    return Response(stats)