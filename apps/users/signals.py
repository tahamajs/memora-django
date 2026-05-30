"""
Signals for user management.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile, UserActivity

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """Log user creation activity."""
    if created:
        UserActivity.objects.create(
            user=instance,
            action=UserActivity.ActionType.CREATE,
            entity_type='user',
            entity_id=str(instance.id),
        )


@receiver(pre_save, sender=User)
def update_user_stats(sender, instance, **kwargs):
    """Update user statistics before save."""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if old_instance.is_active and not instance.is_active:
                # User is being deactivated
                pass
        except User.DoesNotExist:
            pass