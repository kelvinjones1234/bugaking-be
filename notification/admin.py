from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


# 3. NOTIFICATION ADMIN
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__email")
    readonly_fields = ("created_at",)

    # Improve readability in list view
    list_per_page = 20

    # Coloring the status in the list view (Optional visual flair)
    def notification_type_colored(self, obj):
        colors = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "alert": "red",
        }
        color = colors.get(obj.notification_type, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_notification_type_display(),
        )
