from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .models import User, Profile
from .serializers import (
    PasswordResetRequestSerializer,
    PasswordResetSerializer,
    UserRegistrationSerializer,
    ProfileSerializer,
)
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from core.settings import get_env_variable


# In views.py


class SignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # 1. Inspect what the frontend sent
        # print(f"Login Attempt Payload: {request.data}")

        serializer = TokenObtainPairSerializer(data=request.data)

        try:
            # 2. This raises a ValidationError (400) or AuthenticationFailed (401)
            # if the password doesn't match the hash in the DB.
            serializer.is_valid(raise_exception=True)

            user = serializer.user
            profile = getattr(user, "profile", None)

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

        except Exception as e:
            # 3. Print the actual failure reason
            print(f"Login Failed: {e}")
            # If it's a validation error, print the details
            if hasattr(e, "detail"):
                print(f"Error Detail: {e.detail}")

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
            return Profile.objects.select_related("user").get(user=self.request.user)
        except Profile.DoesNotExist:
            # Fallback: Create profile if it is missing (Safety Net)
            return Profile.objects.create(user=self.request.user)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                # Update this to your production URL variable
                reset_link = f"http://localhost:3000/authentication/reset-password/{uid}/{token}/"

                # Branding Colors
                COLOR_BG = "#f8f7f6"
                COLOR_DARK = "#171512"
                COLOR_GOLD = "#d0a539"
                COLOR_WHITE = "#ffffff"

                # Dynamic Name (Fall back to 'Investor' if no name)
                greeting_name = user.first_name if user.first_name else "Investor"

                # Inline HTML email
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Password Reset</title>
                </head>
                <body style="margin: 0; padding: 0; background-color: {COLOR_BG}; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
                    
                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td align="center" style="padding: 40px 0;">
                                
                                <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: {COLOR_WHITE}; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(23, 21, 18, 0.05); border: 1px solid rgba(23, 21, 18, 0.05);">
                                    
                                    <tr>
                                        <td align="center" style="padding: 40px 40px 30px 40px; border-bottom: 1px solid rgba(23, 21, 18, 0.05);">
                                            <p style="margin: 0; color: {COLOR_GOLD}; font-size: 10px; font-weight: 900; text-transform: uppercase; letter-spacing: 4px;">BugaKing Group</p>
                                        </td>
                                    </tr>

                                    <tr>
                                        <td style="padding: 40px 40px;">
                                            <h1 style="margin: 0 0 20px 0; color: {COLOR_DARK}; font-size: 24px; font-weight: 900; line-height: 1.2; letter-spacing: -0.5px;">
                                                Reset Your Password.
                                            </h1>
                                            
                                            <p style="margin: 0 0 30px 0; color: rgba(23, 21, 18, 0.7); font-size: 16px; line-height: 1.6;">
                                                Hello {greeting_name},
                                            </p>
                                            
                                            <p style="margin: 0 0 40px 0; color: rgba(23, 21, 18, 0.7); font-size: 16px; line-height: 1.6;">
                                                We received a request to access your investment portfolio. To ensure your assets remain secure, please set a new password by clicking the button below.
                                            </p>

                                            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                <tr>
                                                    <td align="center">
                                                        <a href="{reset_link}" style="display: inline-block; background-color: {COLOR_GOLD}; color: {COLOR_DARK}; font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; text-decoration: none; padding: 18px 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(208, 165, 57, 0.3);">
                                                            Reset Password
                                                        </a>
                                                    </td>
                                                </tr>
                                            </table>

                                            <p style="margin: 40px 0 0 0; color: rgba(23, 21, 18, 0.5); font-size: 14px; line-height: 1.6; text-align: center;">
                                                Or copy this link into your browser:<br>
                                                <a href="{reset_link}" style="color: {COLOR_GOLD}; text-decoration: none; font-weight: bold; word-break: break-all;">{reset_link}</a>
                                            </p>
                                        </td>
                                    </tr>

                                    <tr>
                                        <td style="background-color: #faf9f8; padding: 30px 40px;">
                                            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                <tr>
                                                    <td valign="top" width="20" style="padding-top: 2px;">
                                                        <span style="font-size: 16px;">🔒</span>
                                                    </td>
                                                    <td style="padding-left: 15px;">
                                                        <p style="margin: 0; color: {COLOR_DARK}; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">
                                                            Security Notice
                                                        </p>
                                                        <p style="margin: 0; color: rgba(23, 21, 18, 0.6); font-size: 13px; line-height: 1.5;">
                                                            This link expires in 24 hours. If you did not request this change, please ignore this email or contact your portfolio manager immediately.
                                                        </p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>

                                </table>

                                <table width="600" border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td align="center" style="padding: 30px 0;">
                                            <p style="margin: 0; color: rgba(23, 21, 18, 0.4); font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">
                                                © 2026 BugaKing Group
                                            </p>
                                            <p style="margin: 10px 0 0 0; color: rgba(23, 21, 18, 0.4); font-size: 12px;">
                                                <a href="mailto:support@bugaking.com" style="color: rgba(23, 21, 18, 0.4); text-decoration: underline;">Contact Support</a>
                                            </p>
                                        </td>
                                    </tr>
                                </table>

                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """

                # Send the reset link via email
                subject = "Action Required: Reset Your Dashboard Password"
                message = f"Click the link below to reset your password:\n{reset_link}"
                # Ensure you change this to your actual sender
                from_email = get_env_variable(
                    "EMAIL_HOST_USER", "security@bugaking.com"
                )
                recipient_list = [email]

                send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    fail_silently=False,
                    html_message=html_content,
                )

                return Response(
                    {"message": "Password reset link has been sent to your email"},
                    status=status.HTTP_200_OK,
                )
            except User.DoesNotExist:
                # Security best practice: Don't reveal if user exists or not,
                # but for dev/UX we often return specific errors.
                return Response(
                    {"error": "No account associated with this email address"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token, *args, **kwargs):

        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            uid = force_str(urlsafe_base64_decode(uidb64))
            try:
                user = User.objects.get(pk=uid)
                if default_token_generator.check_token(user, token):
                    user.set_password(serializer.validated_data["password"])
                    user.save()
                    return Response(
                        {"message": "Password has been reset successfully"},
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
                    )
            except User.DoesNotExist:
                return Response(
                    {"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
