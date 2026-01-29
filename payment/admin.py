from django.contrib import admin
from django.utils.html import format_html
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # 1. Columns shown in the list view
    list_display = (
        "timestamp",
        "user_email",
        "project_name",
        "location",
        "installment_number",
        "formatted_amount",
        "reference_link",
    )

    # 2. Filters on the right sidebar
    list_filter = (
        "timestamp", 
        "investment__selected_option__project", 
        "investment__selected_option__project__investment_type", 
    )

    # 3. Search functionality
    search_fields = (
        "user__email", 
        "user__first_name", 
        "payment_reference", 
        "investment__selected_option__project__name"
    )

    # 4. Read-only fields
    readonly_fields = ("timestamp", "location", "user", "investment", "amount", "payment_reference")

    # 5. Organization of the detail page
    fieldsets = (
        ("Payment Info", {
            "fields": ("timestamp", "payment_reference", "amount")
        }),
        ("Customer & Asset", {
            "fields": ("user", "investment", "location")
        }),
    )

    # --- Helper Methods ---

    @admin.display(description="User")
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description="Project")
    def project_name(self, obj):
        if obj.investment and obj.investment.selected_option:
            return obj.investment.selected_option.project.name
        return "-"

    @admin.display(description="Amount Paid")
    def formatted_amount(self, obj):
        if obj.amount is None:
            return "-"
            
        # FIX: Format the number purely as a string first
        amount_str = f"₦{obj.amount:,.2f}"
        
        # Then pass the string to format_html with a simple placeholder
        return format_html(
            '<b style="color: #2e7d32;">{}</b>', 
            amount_str
        )

    @admin.display(description="Ref #")
    def reference_link(self, obj):
        if obj.payment_reference:
            return format_html(
                '<code style="background: #eee; padding: 2px 5px; border-radius: 4px;">{}</code>', 
                obj.payment_reference
            )
        return "-"

    def has_add_permission(self, request):
        return False