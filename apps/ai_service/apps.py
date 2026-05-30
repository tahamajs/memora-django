"""
App configuration for AI Service.
"""
from django.apps import AppConfig


class AIServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_service'
    verbose_name = 'AI Service'
    
    def ready(self):
        """
        Initialize AI service connections when app is ready.
        """
        try:
            from .services import AIServiceManager
            # Pre-load AI service configurations
            AIServiceManager.initialize()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"AI Service initialization warning: {e}")