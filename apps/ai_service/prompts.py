"""
AI Prompts for Local Notion Clone.
Centralized prompt templates for all AI features.
"""

# Summarization Prompts
SUMMARIZE_PROMPTS = {
    'concise': """
        Provide a concise 2-3 sentence summary of the following text.
        Focus on the main points and key takeaways.
        
        Text:
        {content}
        
        Summary:
    """,
    
    'detailed': """
        Provide a detailed summary of the following text.
        Include main arguments, supporting details, and conclusions.
        
        Text:
        {content}
        
        Detailed Summary:
    """,
    
    'bullets': """
        Summarize the following text in bullet points.
        Extract 3-5 key points that capture the essential information.
        
        Text:
        {content}
        
        Key Points:
        - 
    """,
    
    'executive': """
        Create an executive summary of the following text.
        Include: Purpose, Key Findings, and Recommendations.
        
        Text:
        {content}
        
        Executive Summary:
    """,
}

# Tag Generation Prompt
TAG_GENERATION_PROMPT = """
    Based on the following content, suggest 3-5 relevant tags.
    Return ONLY a JSON array of strings, nothing else.
    Tags should be lowercase, concise, and descriptive.
    
    Existing tags: {existing_tags}
    
    Content:
    {content}
    
    Return format: ["tag1", "tag2", "tag3"]
    Tags:
"""

# Writing Improvement Prompts
WRITING_IMPROVEMENT_PROMPTS = {
    'professional': """
        Improve the following text to be more professional and polished.
        Use formal language, proper structure, and business-appropriate tone.
        {preserve_instruction}
        
        Original:
        {content}
        
        Improved (Professional):
    """,
    
    'casual': """
        Rewrite the following text in a casual, conversational tone.
        Make it friendly and approachable while maintaining clarity.
        {preserve_instruction}
        
        Original:
        {content}
        
        Improved (Casual):
    """,
    
    'concise': """
        Make the following text more concise and to the point.
        Remove redundancy and unnecessary words without losing meaning.
        {preserve_instruction}
        
        Original:
        {content}
        
        Improved (Concise):
    """,
    
    'academic': """
        Enhance the following text to meet academic writing standards.
        Use scholarly language, proper citations format, and formal structure.
        {preserve_instruction}
        
        Original:
        {content}
        
        Improved (Academic):
    """,
    
    'creative': """
        Enhance the following text with creative and engaging language.
        Use vivid descriptions, metaphors, and compelling narrative.
        {preserve_instruction}
        
        Original:
        {content}
        
        Improved (Creative):
    """,
    
    'technical': """
        Improve the following text for technical documentation.
        Use precise terminology, clear structure, and instructional tone.
        {preserve_instruction}
        
        Original:
        {content}
        
        Improved (Technical):
    """,
}

# Research Analysis Prompt
RESEARCH_ANALYSIS_PROMPT = """
    You are a research analyst. Based on the query and provided context notes,
    provide a comprehensive analysis in JSON format.
    
    Query: {query}
    
    Context Notes:
    {context}
    
    Analysis Depth: {depth}
    
    Return a JSON object with these fields:
    {{
        "analysis": "Detailed analysis of the query based on context",
        "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
        "sources": ["Suggested source 1", "Suggested source 2"],
        "methodology_suggestions": "Suggested research methodology",
        "gaps_identified": ["Gap 1", "Gap 2"],
        "future_directions": "Suggested future research directions",
        "confidence_score": 0.0-1.0
    }}
    
    Analysis:
"""

# Sentiment Analysis Prompt
SENTIMENT_ANALYSIS_PROMPT = """
    Analyze the sentiment of the following text.
    Consider the overall tone and emotional content.
    
    Text:
    {content}
    
    Sentiment (positive/negative/neutral):
"""

# Keyword Extraction Prompt
KEYWORD_EXTRACTION_PROMPT = """
    Extract the most important keywords from the following text.
    Return ONLY a JSON array of 5-10 keywords or short phrases.
    
    Text:
    {content}
    
    Keywords (JSON array):
"""

# Topic Detection Prompt
TOPIC_DETECTION_PROMPT = """
    Identify the main topics discussed in the following text.
    Return ONLY a JSON array of 3-5 topic strings.
    
    Text:
    {content}
    
    Topics (JSON array):
"""

# Content Analysis Prompts
CONTENT_ANALYSIS_PROMPT = """
    Analyze the following content and provide insights in JSON format:
    {{
        "main_theme": "Primary theme or subject",
        "tone": "Overall tone (informative/persuasive/narrative/etc.)",
        "complexity": "simple/moderate/complex",
        "target_audience": "Who this content is for",
        "strengths": ["Strength 1", "Strength 2"],
        "improvements": ["Improvement 1", "Improvement 2"],
        "engagement_score": 0-100
    }}
    
    Content:
    {content}
    
    Analysis:
"""

# Note Improvement Prompts
NOTE_IMPROVEMENT_PROMPTS = {
    'structure': """
        Improve the structure of this note. Add headings, organize thoughts,
        and create a logical flow.
        
        Note:
        {content}
        
        Improved Structure:
    """,
    
    'clarity': """
        Improve the clarity of this note. Simplify complex sentences,
        define unclear terms, and enhance readability.
        
        Note:
        {content}
        
        Improved Clarity:
    """,
    
    'completeness': """
        Identify missing information and suggest additions to make
        this note more complete and comprehensive.
        
        Note:
        {content}
        
        Suggestions for Completion:
    """,
}

# Meeting Notes Prompts
MEETING_NOTES_PROMPT = """
    Convert the following meeting transcript/notes into organized meeting minutes:
    {{
        "meeting_title": "Title",
        "date": "Date",
        "attendees": ["Attendee 1", "Attendee 2"],
        "agenda": ["Item 1", "Item 2"],
        "key_discussions": ["Discussion 1", "Discussion 2"],
        "decisions_made": ["Decision 1", "Decision 2"],
        "action_items": [
            {{"task": "Task description", "assignee": "Name", "deadline": "Date"}}
        ],
        "next_steps": ["Step 1", "Step 2"],
        "next_meeting": "Date/Time"
    }}
    
    Raw Notes:
    {content}
    
    Meeting Minutes (JSON):
"""

# Task Extraction Prompt
TASK_EXTRACTION_PROMPT = """
    Extract action items and tasks from the following text.
    Return a JSON array of tasks with descriptions and priorities.
    
    Text:
    {content}
    
    Tasks (JSON array of {{"task": "...", "priority": "high/medium/low"}}):
"""