from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import generics, status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import User, Profile
from .serializers import UserRegistrationSerializer
from .serializers import ProfileSerializer



class SignInView(APIView):
    """
    API endpoint for user login.
    Returns JWT access and refresh tokens upon successful authentication.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TokenObtainPairSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            profile = getattr(user, "profile", None)

            return Response(
                {
                    "tokens": serializer.validated_data,
                    "user": {
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "phone_number": user.phone_number,
                        "is_approved": user.is_approved,

                        "profile": {
                            "address": profile.address if profile else None,
                            "profile_picture": (
                                profile.profile_picture.url
                                if profile and profile.profile_picture
                                else None
                            ),
                        },
                    },
                    "message": "Login successful",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            # Useful during development
            print("Login Error:", e)

            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )









class SignUpView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        email = request.data.get("email")

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "An account with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "user": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "message": "User registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )






class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # This ensures the view returns the profile of the CURRENT user
        # It handles the case where a profile might not exist by creating one (safety net)
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile