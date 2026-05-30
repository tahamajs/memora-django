"""
App configuration for Git Service.
"""
from django.apps import AppConfig


class GitServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.git_service'
    verbose_name = 'Git Service'
    
    def ready(self):
        """
        Initialize Git service when app is ready.
        """
        try:
            from .services import GitService
            # Initialize Git repository
            GitService.initialize()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Git Service initialization warning: {e}")