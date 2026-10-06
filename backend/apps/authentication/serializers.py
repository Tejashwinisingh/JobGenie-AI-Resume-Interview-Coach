"""
apps/authentication/serializers.py

All serializers for the authentication module:
  - UserRegistrationSerializer  : Register a new user
  - UserLoginSerializer         : Validate login credentials
  - UserProfileSerializer       : Read & update user profile
  - ChangePasswordSerializer    : Change password (future use)
"""
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
# pyrefly: ignore [missing-import]
from rest_framework import serializers

from .models import User


# ─── Registration ─────────────────────────────────────────────────────────────

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serialize a new user registration request."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'password', 'password_confirm')
        extra_kwargs = {
            'full_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


# ─── Login ────────────────────────────────────────────────────────────────────

class UserLoginSerializer(serializers.Serializer):
    """Validate login credentials and return the authenticated user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Email and password are required.')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')

        attrs['user'] = user
        return attrs


# ─── Profile ──────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    """Read and update the authenticated user's profile."""

    email = serializers.EmailField(read_only=True)  # email cannot be changed via profile update

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'full_name',
            'bio',
            'profile_picture',
            'date_joined',
        )
        read_only_fields = ('id', 'email', 'date_joined')

    def update(self, instance, validated_data):
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.bio = validated_data.get('bio', instance.bio)
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']
        instance.save()
        return instance
