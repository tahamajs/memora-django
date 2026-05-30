import secrets
import hashlib
from datetime import datetime, timedelta
from django.utils import timezone
from apps.users.models import APIKey

class APIKeyService:
    def generate_key(self, user, name: str, scopes: list) -> str:
        raw_key = "mem_" + secrets.token_hex(32)
        hashed = hashlib.sha256(raw_key.encode()).hexdigest()
        APIKey.objects.create(
            user=user,
            name=name,
            key_hash=hashed,
            scopes=','.join(scopes),
            expires_at=timezone.now() + timedelta(days=365)
        )
        return raw_key

    def validate_key(self, raw_key: str):
        hashed = hashlib.sha256(raw_key.encode()).hexdigest()
        try:
            return APIKey.objects.get(key_hash=hashed, revoked=False, expires_at__gt=timezone.now())
        except APIKey.DoesNotExist:
            return None
