"""
URL patterns for AI service endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Summarization
    path('summarize/', views.summarize_text, name='ai-summarize'),
    
    # Tag generation
    path('generate-tags/', views.generate_tags, name='ai-generate-tags'),
    
    # Writing improvement
    path('improve-writing/', views.improve_writing, name='ai-improve-writing'),
    
    # Research analysis
    path('research/', views.research_analysis, name='ai-research'),
    
    # Content analysis
    path('analyze/', views.analyze_content, name='ai-analyze'),
    
    # Meeting notes organization
    path('organize-meeting/', views.organize_meeting_notes, name='ai-organize-meeting'),
    
    # Task extraction
    path('extract-tasks/', views.extract_tasks, name='ai-extract-tasks'),
    
    # Status and stats
    path('status/', views.ai_status, name='ai-status'),
    path('usage/', views.usage_stats, name='ai-usage'),
]