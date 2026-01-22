from django.contrib import admin
from django.utils.html import format_html
from .models import InvestorDocuments


@admin.register(InvestorDocuments)
class InvestorDocumentsAdmin(admin.ModelAdmin):
    list_display = (
        "document_type_display", 
        "client_email", 
        "unlocked", 
        "uploaded_at",
        "view_file_button"
    )
    
    list_filter = ("document_type", "unlocked", "uploaded_at")
    
    # Enable searching by user info
    search_fields = (
        "investor__email", 
        "investor__first_name", 
        "investor__last_name"
    )
    
    readonly_fields = ("uploaded_at",)
    list_editable = ("unlocked",)  # Quick toggle without entering edit page
    
    actions = ["unlock_documents", "lock_documents"]

    # --- Custom Columns ---

    def client_email(self, obj):
        return obj.investor.email
    client_email.short_description = "Client"

    def document_type_display(self, obj):
        return obj.get_document_type_display()
    document_type_display.short_description = "Document Type"

    def view_file_button(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" style="background-color: #4CAF50; color: white; padding: 3px 10px; text-decoration: none; border-radius: 3px;">View</a>',
                obj.file.url
            )
        return "No File"
    view_file_button.short_description = "File"

    # --- Bulk Actions ---

    @admin.action(description="Unlock selected documents (Make visible to user)")
    def unlock_documents(self, request, queryset):
        updated = queryset.update(unlocked=True)
        self.message_user(request, f"{updated} documents have been successfully unlocked.")

    @admin.action(description="Lock selected documents (Hide from user)")
    def lock_documents(self, request, queryset):
        updated = queryset.update(unlocked=False)
        self.message_user(request, f"{updated} documents have been locked.")
