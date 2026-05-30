"""
Views for user management.
"""
from rest_framework import status, permissions, viewsets, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.cache import cache
import logging

from .models import User, UserProfile, UserActivity
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    UserActivitySerializer,
    APIKeySerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Log activity
        self._log_activity(user, UserActivity.ActionType.CREATE, 'user', str(user.id))
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    
    def _log_activity(self, user, action, entity_type, entity_id):
        try:
            UserActivity.objects.create(
                user=user,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            )
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management."""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_object(self):
        """Get current user or specified user."""
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Update last active
        if instance == request.user:
            instance.update_last_active()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile."""
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({'message': 'Password updated successfully'})
    
    @action(detail=False, methods=['post'])
    def generate_api_key(self, request):
        """Generate new API key."""
        api_key = request.user.generate_api_key()
        return Response({'api_key': api_key})
    
    @action(detail=False, methods=['get'])
    def api_key(self, request):
        """Get current API key."""
        return Response({'api_key': request.user.api_key})
    
    @action(detail=False, methods=['delete'])
    def delete_account(self, request):
        """Delete user account."""
        user = request.user
        user.is_active = False
        user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            action=UserActivity.ActionType.DELETE,
            entity_type='user',
            entity_id=str(user.id),
        )
        
        return Response(
            {'message': 'Account deactivated successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics."""
        user = request.user
        
        from django.db.models import Sum, Count, Q
        from apps.notes.models import Note
        
        notes = Note.objects.filter(author=user)
        
        stats = {
            'total_notes': notes.count(),
            'published_notes': notes.filter(status='published').count(),
            'draft_notes': notes.filter(status='draft').count(),
            'archived_notes': notes.filter(status='archived').count(),
            'favorite_notes': notes.filter(is_favorite=True).count(),
            'total_words': notes.aggregate(Sum('word_count'))['word_count__sum'] or 0,
            'avg_words_per_note': notes.aggregate(Avg('word_count'))['word_count__avg'] or 0,
            'total_attachments': sum(note.attachments.count() for note in notes),
            'total_tags': Tag.objects.filter(notes__author=user).distinct().count(),
            'most_used_tags': list(
                Tag.objects.filter(notes__author=user)
                .annotate(count=Count('notes'))
                .order_by('-count')[:10]
                .values('name', 'count', 'color')
            ),
            'notes_this_week': notes.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'notes_this_month': notes.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'streak_days': self._calculate_streak(user),
            'storage_used': user.storage_used,
        }
        
        return Response(stats)
    
    def _calculate_streak(self, user):
        """Calculate consecutive days of activity."""
        from datetime import timedelta
        from django.utils import timezone
        
        activities = UserActivity.objects.filter(
            user=user,
            action__in=['create', 'update'],
            created_at__gte=timezone.now() - timedelta(days=365)
        ).dates('created_at', 'day')
        
        if not activities:
            return 0
        
        streak = 0
        current_date = timezone.now().date()
        
        for activity_date in sorted(activities, reverse=True):
            if activity_date == current_date or activity_date == current_date - timedelta(days=streak + 1):
                streak += 1
                current_date = activity_date
            else:
                break
        
        return streak
    
    @action(detail=False, methods=['get'])
    def activity(self, request):
        """Get user activity history."""
        activities = UserActivity.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]
        
        page = self.paginate_queryset(activities)
        if page is not None:
            serializer = UserActivitySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user profiles."""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user.profile
        return super().get_object()


class LogoutView(generics.GenericAPIView):
    """User logout endpoint."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action=UserActivity.ActionType.LOGOUT,
                entity_type='user',
                entity_id=str(request.user.id),
            )
            
            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )