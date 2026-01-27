# from rest_framework.views import APIView
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework import generics, status, permissions
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from .models import User, Profile
# from .serializers import UserRegistrationSerializer
# from .serializers import ProfileSerializer



# class SignInView(APIView):
#     """
#     API endpoint for user login.
#     Returns JWT access and refresh tokens upon successful authentication.
#     """

#     permission_classes = [AllowAny]

#     def post(self, request, *args, **kwargs):
#         serializer = TokenObtainPairSerializer(data=request.data)

#         try:
#             serializer.is_valid(raise_exception=True)
#             user = serializer.user
#             profile = getattr(user, "profile", None)

#             return Response(
#                 {
#                     "tokens": serializer.validated_data,
#                     "user": {
#                         "email": user.email,
#                         "first_name": user.first_name,
#                         "last_name": user.last_name,
#                         "phone_number": user.phone_number,
#                         "is_approved": user.is_approved,

#                         "profile": {
#                             "address": profile.address if profile else None,
#                             "profile_picture": (
#                                 profile.profile_picture.url
#                                 if profile and profile.profile_picture
#                                 else None
#                             ),
#                         },
#                     },
#                     "message": "Login successful",
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except Exception as e:
#             # Useful during development
#             print("Login Error:", e)

#             return Response(
#                 {"error": "Invalid email or password"},
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )









# class SignUpView(generics.CreateAPIView):
#     """
#     API endpoint for user registration.
#     """

#     permission_classes = [AllowAny]
#     serializer_class = UserRegistrationSerializer

#     def create(self, request, *args, **kwargs):
#         email = request.data.get("email")

#         # Check if email already exists
#         if User.objects.filter(email=email).exists():
#             return Response(
#                 {"error": "An account with this email already exists"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()

#         return Response(
#             {
#                 "user": {
#                     "email": user.email,
#                     "first_name": user.first_name,
#                     "last_name": user.last_name,
#                 },
#                 "message": "User registered successfully",
#             },
#             status=status.HTTP_201_CREATED,
#         )






# class UserProfileView(generics.RetrieveUpdateAPIView):
#     serializer_class = ProfileSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_object(self):
#         # This ensures the view returns the profile of the CURRENT user
#         # It handles the case where a profile might not exist by creating one (safety net)
#         profile, created = Profile.objects.get_or_create(user=self.request.user)
#         return profile












from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .models import User, Profile
from .serializers import (
    UserRegistrationSerializer, 
    ProfileSerializer
)

class SignInView(APIView):
    """
    API endpoint for user login.
    Returns JWT tokens and user details.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TokenObtainPairSerializer(data=request.data)

        try:
            # 1. Authenticate credentials
            serializer.is_valid(raise_exception=True)
            
            # 2. Retrieve User instance (provided by simplejwt)
            user = serializer.user
            
            # 3. Safe Profile Retrieval
            # We use getattr to safely handle the edge case where a user exists but has no profile
            # (e.g. legacy data or creation error).
            profile = getattr(user, "profile", None)

            # 4. Construct Response
            # We build this manually to avoid the overhead of calling a full Serializer 
            # just for the login response structure.
            response_data = {
                "tokens": serializer.validated_data,
                "user": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number,
                    "is_approved": user.is_approved,
                    "profile": {
                        "address": profile.address if profile else "",
                        "profile_picture": (
                            profile.profile_picture.url 
                            if profile and profile.profile_picture 
                            else None
                        ),
                    },
                },
                "message": "Login successful",
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except (TokenError, InvalidToken):
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            # Log the actual error for debugging, return generic error to user
            print(f"Login Internal Error: {e}")
            return Response(
                {"error": "An error occurred during login"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SignUpView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        # Optimization: We removed the manual 'User.objects.filter(email=...)' check.
        # The serializer automatically checks unique constraints faster.
        
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
    """
    Endpoint to view or update the current user's profile.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Optimization: select_related('user')
        # This fetches the Profile AND User data in a single SQL query.
        # This prevents N+1 queries since our Serializer reads user.first_name/last_name.
        try:
            return Profile.objects.select_related('user').get(user=self.request.user)
        except Profile.DoesNotExist:
            # Fallback: Create profile if it is missing (Safety Net)
            return Profile.objects.create(user=self.request.user)