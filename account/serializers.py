from rest_framework import serializers
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
            "password",
            "password_confirm",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        # Profile is created automatically by signal
        return user


from rest_framework import serializers
from .models import Profile, User






class ProfileSerializer(serializers.ModelSerializer):
    # We explicitly define these to allow updating User model fields via this serializer
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    is_approved = serializers.CharField(source="user.is_approved")
    email = serializers.EmailField(
        source="user.email", read_only=True
    )  # Email should usually be read-only here

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
        # 1. Extract User data if present
        user_data = validated_data.pop("user", {})

        # 2. Update the User model (First/Last Name)
        user = instance.user
        if "first_name" in user_data:
            user.first_name = user_data.get("first_name")
        if "last_name" in user_data:
            user.last_name = user_data.get("last_name")
        user.save()

        # 3. Update the Profile model (Phone, Address, Image) with remaining data
        return super().update(instance, validated_data)















class PasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.CharField()
