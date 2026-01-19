# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.forms import ModelForm
# from django import forms

# from .models import User


# class UserChangeForm(ModelForm):
#     """Form for updating users in admin (password is read-only)"""

#     class Meta:
#         model = User
#         fields = "__all__"


# class UserCreationForm(ModelForm):
#     """Form for creating users in admin"""

#     password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
#     password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

#     class Meta:
#         model = User
#         fields = ("email", "first_name", "last_name")

#     def clean(self):
#         cleaned_data = super().clean()
#         password1 = cleaned_data.get("password1")
#         password2 = cleaned_data.get("password2")

#         if password1 and password2 and password1 != password2:
#             raise forms.ValidationError("Passwords do not match")
#         return cleaned_data

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.set_password(self.cleaned_data["password1"])
#         if commit:
#             user.save()
#         return user


# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     model = User

#     form = UserChangeForm
#     add_form = UserCreationForm

#     list_display = (
#         "email",
#         "first_name",
#         "last_name",
#         "is_staff",
#         "is_active",
#         "is_approved",
#         "date_joined",
#     )

#     list_filter = ("is_staff", "is_active", "is_approved")
#     search_fields = ("email", "first_name", "last_name")
#     ordering = ("-date_joined",)

#     fieldsets = (
#         (None, {"fields": ("email", "password")}),
#         ("Personal Info", {"fields": ("first_name", "last_name")}),
#         (
#             "Permissions",
#             {
#                 "fields": (
#                     "is_active",
#                     "is_staff",
#                     "is_superuser",
#                     "is_approved",
#                     "groups",
#                     "user_permissions",
#                 )
#             },
#         ),
#         ("Important dates", {"fields": ("last_login", "date_joined")}),
#     )

#     add_fieldsets = (
#         (
#             None,
#             {
#                 "classes": ("wide",),
#                 "fields": (
#                     "email",
#                     "first_name",
#                     "last_name",
#                     "password1",
#                     "password2",
#                     "is_active",
#                     "is_staff",
#                     "is_approved",
#                 ),
#             },
#         ),
#     )

#     filter_horizontal = ("groups", "user_permissions")


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
        (None, {"fields": ("email", "password")}),
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
    list_display = ("user", "phone_number")
    search_fields = ("user__email", "phone_number")
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 3})},
    }
