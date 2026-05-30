"""
Serializers for user models.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from .models import User, UserProfile, UserActivity

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password2',
            'first_name', 'last_name'
        ]
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        
        # Create profile
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'}
    )


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user model."""
    profile = UserProfileSerializer(read_only=True)
    note_count = serializers.IntegerField(read_only=True)
    storage_used = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'bio', 'avatar', 'website', 'location', 'company', 'job_title',
            'role', 'theme', 'language', 'timezone',
            'email_notifications', 'ai_features_enabled', 'git_sync_enabled',
            'auto_save', 'auto_save_interval',
            'profile', 'note_count', 'storage_used',
            'last_active', 'total_notes_created', 'total_words_written',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'role', 'last_active', 'total_notes_created',
            'total_words_written', 'note_count', 'storage_used',
            'created_at', 'updated_at',
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user."""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'bio', 'website',
            'location', 'company', 'job_title', 'theme',
            'language', 'timezone', 'email_notifications',
            'ai_features_enabled', 'git_sync_enabled',
            'auto_save', 'auto_save_interval',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, validators=[validate_password]
    )
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activity."""
    user = serializers.StringRelatedField()
    
    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class APIKeySerializer(serializers.Serializer):
    """Serializer for API key operations."""
    api_key = serializers.CharField(read_only=True)