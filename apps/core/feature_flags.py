from django.conf import settings

class FeatureFlags:
    @staticmethod
    def is_enabled(flag: str) -> bool:
        return getattr(settings, f'FEATURE_{flag.upper()}', False)
