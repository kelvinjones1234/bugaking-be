from rest_framework import serializers
from django.db import transaction
from .models import User, Profile

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        # Remove password_confirm before passing to the manager
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        # The optimized UserManager handles hashing and Profile creation transactionally
        user = User.objects.create_user(password=password, **validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    # Flatten user fields for easier frontend consumption
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    phone_number = serializers.CharField(source="user.phone_number", required=False)
    email = serializers.EmailField(source="user.email", read_only=True)
    is_approved = serializers.BooleanField(source="user.is_approved", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "is_approved",
            "profile_picture",
        ]

    def update(self, instance, validated_data):
        # Extract user data to update the related User model
        user_data = validated_data.pop("user", {})
        
        # Use atomic transaction to ensure both User and Profile update successfully
        with transaction.atomic():
            # 1. Update Profile fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # 2. Update User fields if provided
            if user_data:
                user = instance.user
                for attr, value in user_data.items():
                    setattr(user, attr, value)
                user.save()

        return instance


class PasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.CharField()


