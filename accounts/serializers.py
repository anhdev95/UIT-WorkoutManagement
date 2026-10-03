from datetime import date

from django.db import transaction
from rest_framework import serializers

from .models import User, UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']
        read_only_fields = ['id', 'role']
        extra_kwargs = {'email': {'required': True}}

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email đã được sử dụng.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        # Register always creates a normal USER; role sent by client is ignored.
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=User.Role.USER,
        )
        UserProfile.objects.create(user=user)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'role',
            'full_name', 'gender', 'date_of_birth', 'height_cm',
            'fitness_goal', 'activity_level',
        ]

    def validate_height_cm(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Chiều cao phải lớn hơn 0.')
        return value

    def validate_date_of_birth(self, value):
        if value and value > date.today():
            raise serializers.ValidationError('Ngày sinh không được ở tương lai.')
        return value


class AdminUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_active', 'date_joined', 'profile']
        read_only_fields = fields


class UserStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
