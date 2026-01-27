from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    # 1. Columns to display in the list view
    list_display = (
        "title",
        "user_email",
        "category",
        "file_type",
        "file_size",
        "created_at",
    )

    # 2. Sidebar filters for quick sorting
    list_filter = ("category", "file_type", "created_at")

    # 3. Search box functionality (searches title and the user's email)
    search_fields = ("title", "user__email", "user__first_name", "user__last_name")

    # 4. Fields that cannot be edited manually (since they are auto-calculated)
    readonly_fields = ("file_size", "file_type", "created_at", "updated_at")

    # 5. Organize the edit form into neat sections
    fieldsets = (
        ("Ownership & File", {"fields": ("user", "title", "file", "category")}),
        (
            "Auto-Generated Metadata",
            {
                "classes": ("collapse",),  # Collapsed by default to save space
                "fields": ("file_size", "file_type", "created_at", "updated_at"),
            },
        ),
    )

    # Helper method to show user email in list_display
    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User"
