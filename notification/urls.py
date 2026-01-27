from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from .views import (
    HeaderDataView,
    MarkAllReadView,
    MarkNotificationReadView,
    NotificationListView,
)

urlpatterns = [
    # Notifications
    path("notifications/", NotificationListView.as_view(), name="notifications-list"),
    path(
        "notifications/<int:pk>/read/",
        MarkNotificationReadView.as_view(),
        name="notification-read",
    ),
    path(
        "notifications/read-all/",
        MarkAllReadView.as_view(),
        name="notifications-read-all",
    ),
    # Header Data (Image + Badge Status)
    path("header-data/", HeaderDataView.as_view(), name="header-data"),
]
