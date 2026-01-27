from rest_framework import generics, status, permissions

from account.models import Profile
from .models import Notification
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Notification
from account.models import Profile
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return all notifications for the current user
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({"status": "marked as read"}, status=status.HTTP_200_OK)


class MarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return Response({"status": "all marked as read"}, status=status.HTTP_200_OK)


# --- SPECIAL VIEW FOR YOUR HEADER COMPONENT ---
class HeaderDataView(APIView):
    """
    Returns profile image and notification status in one call.
    Perfect for the NotificationComponent.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # 1. Get Profile Image
        profile_img_url = None
        try:
            if hasattr(user, "profile") and user.profile.profile_picture:
                profile_img_url = request.build_absolute_uri(
                    user.profile.profile_picture.url
                )
        except Profile.DoesNotExist:
            pass

        # 2. Check for ANY unread notifications
        has_unread = Notification.objects.filter(user=user, is_read=False).exists()

        # 3. Get Count (optional, if you want to show a number)
        unread_count = Notification.objects.filter(user=user, is_read=False).count()

        return Response(
            {
                "profile_image": profile_img_url,
                "has_notifications": has_unread,
                "unread_count": unread_count,
            }
        )



