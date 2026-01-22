from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import SignInView, SignUpView, UserProfileView

urlpatterns = [
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("signin/", SignInView.as_view(), name="signin"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    # path("password/change/", PasswordChangeAPIView.as_view(), name="password-change"),
    # path("account/disable/", DisableAccountAPIView.as_view(), name="disable-account"),
    # path("account/delete/", DeleteAccountAPIView.as_view(), name="delete-account"),
    # path(
    #     "password-reset/",
    #     PasswordResetRequestView.as_view(),
    #     name="password_reset_request",
    # ),
    # path(
    #     "reset-password/<uidb64>/<token>/",
    #     PasswordResetView.as_view(),
    #     name="password_reset_confirm",
    # ),
]
