from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.forms import Textarea
from django.db import models

from .models import User, Profile


# ----------------------------
# PROFILE INLINE (User → Profile)
# ----------------------------
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


# ----------------------------
# CUSTOM USER ADMIN
# ----------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    # Fields shown in admin list view
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_approved",
        "is_active",
        "date_joined",
    )

    # Filters on right sidebar
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "is_approved",
        "date_joined",
    )

    # Search bar
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)

    # Fields layout in edit page
    fieldsets = (
        (None, {"fields": ("email", "phone_number", "password")}),
        ("Personal Information", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_approved",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    # Fields layout in add user page
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ),
            },
        ),
    )

    readonly_fields = ("date_joined", "last_login")
    filter_horizontal = ("groups", "user_permissions")


# ----------------------------
# PROFILE ADMIN (Optional standalone)
# ----------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__email",)
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 3})},
    }
