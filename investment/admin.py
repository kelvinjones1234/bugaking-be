from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
from django.db import IntegrityError, transaction
from django.db import models
from .models import (
    InvestmentPlan,
    InvestmentProject,
    ProjectPricing,
    ClientInvestment,
    PaymentSchedule,
)



# --- 1. INVESTMENT PLAN ADMIN ---


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "payment_mode", "duration_days")
    list_filter = ("payment_mode",)
    search_fields = ("name",)


# --- 2. PROJECT PRICING ADMIN ---


@admin.register(ProjectPricing)
class ProjectPricingAdmin(admin.ModelAdmin):
    search_fields = ("project__name", "plan__name")
    list_display = (
        "project",
        "plan",
        "formatted_total_price",
        "formatted_minimum_deposit",
    )
    list_filter = ("plan", "project__investment_type")
    autocomplete_fields = ["project", "plan"]

    @admin.display(description="Total Price")
    def formatted_total_price(self, obj):
        return f"₦{obj.total_price:,.2f}"

    @admin.display(description="Minimum Deposit")
    def formatted_minimum_deposit(self, obj):
        return f"₦{obj.minimum_deposit:,.2f}"


# --- 3. PROJECT PRICING INLINE ---


class ProjectPricingInline(admin.TabularInline):
    model = ProjectPricing
    extra = 1
    fields = ("plan", "total_price", "minimum_deposit")
    autocomplete_fields = ["plan"]


# --- 4. INVESTMENT PROJECT ADMIN ---


@admin.register(InvestmentProject)
class InvestmentProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "investment_type", "asset_type", "location", "formatted_roi", "active")
    list_filter = ("investment_type", "active", "location")
    search_fields = ("name", "location")
    inlines = [ProjectPricingInline]

    @admin.display(description="Expected ROI")
    def formatted_roi(self, obj):
        return f"{obj.expected_roi_percent}%"


# --- 5. PAYMENT SCHEDULE INLINE ---


# class PaymentScheduleInline(admin.TabularInline):
#     model = PaymentSchedule
#     extra = 0
#     can_delete = False
#     fields = (
#         "installment_number",
#         "title",
#         "due_date",
#         "formatted_amount",
#         "status",
#         "date_paid",
#     )
#     readonly_fields = (
#         "installment_number",
#         "title",
#         "due_date",
#         "formatted_amount",
#         "status",
#         "date_paid",
#     )

#     def formatted_amount(self, obj):
#         return f"₦{obj.amount:,.2f}" if obj.amount else "₦0.00"

#     formatted_amount.short_description = "Amount"

#     def has_add_permission(self, request, obj=None):
#         return False

#     def get_max_num(self, request, obj=None, **kwargs):
#         """
#         FORCE the admin to show zero rows if the object hasn't been created yet.
#         This stops the Admin from sending empty formset data that causes the IntegrityError.
#         """
#         if obj is None:
#             return 0
#         return super().get_max_num(request, obj, **kwargs)





# --- 5. PAYMENT SCHEDULE INLINE ---

class PaymentScheduleInline(admin.TabularInline):
    model = PaymentSchedule
    extra = 0
    can_delete = False
    fields = (
        "installment_number",
        "title",
        "due_date",
        "formatted_amount",
        "status",
        "date_paid",
    )
    readonly_fields = (
        "installment_number",
        "title",
        "due_date",
        "formatted_amount",
    )

    def formatted_amount(self, obj):
        return f"₦{obj.amount:,.2f}" if obj.amount else "₦0.00"

    formatted_amount.short_description = "Amount"

    def has_add_permission(self, request, obj=None):
        return False

    def get_max_num(self, request, obj=None, **kwargs):
        if obj is None:
            return 0
        return super().get_max_num(request, obj, **kwargs)


# --- CLIENT INVESTMENT ADMIN ---
@admin.register(ClientInvestment)
class ClientInvestmentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "get_project_name",
        "formatted_agreed_amount",
        "formatted_amount_paid",
        "formatted_balance",
        "status_badge",
        "get_completion_percent",
        "schedule_count",
    )
    list_filter = ("status", "start_date", "selected_option__project__investment_type")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "selected_option__project__name",
    )
    autocomplete_fields = ["user", "selected_option"]
    inlines = [PaymentScheduleInline]

    readonly_fields = (
        "formatted_balance",
        "get_completion_percent",
        "created_at",
        "updated_at",
        "installment_amount",
        "formatted_amount_paid", # Make this readonly so admins don't edit it manually and break sync
    )

    fieldsets = (
        (
            "Client & Investment Details",
            {"fields": ("user", "selected_option", "start_date")},
        ),
        (
            "Financial Details",
            {
                "fields": (
                    "agreed_amount",
                    "installment_amount",
                    "formatted_amount_paid", # Display only
                    "formatted_balance",
                    "get_completion_percent",
                )
            },
        ),
        (
            "Status & Tracking",
            {"fields": ("status", "next_payment_date", "created_at", "updated_at")},
        ),
    )

    actions = ["regenerate_schedules_action", "mark_as_completed"]

    @admin.display(description="Project")
    def get_project_name(self, obj):
        return obj.selected_option.project.name

    @admin.display(description="Balance")
    def formatted_balance(self, obj):
        return f"₦{obj.balance:,.2f}"

    @admin.display(description="Total Price")
    def formatted_agreed_amount(self, obj):
        return f"₦{obj.agreed_amount:,.2f}"

    @admin.display(description="Amount Paid")
    def formatted_amount_paid(self, obj):
        return f"₦{obj.amount_paid:,.2f}"

    @admin.display(description="Progress")
    def get_completion_percent(self, obj):
        return f"{obj.percentage_completion}%"

    @admin.display(description="Installments")
    def schedule_count(self, obj):
        total = obj.schedules.count()
        paid = obj.schedules.filter(status="paid").count()
        return f"{paid}/{total}"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "pending": "#ff9800",
            "paying": "#2196F3",
            "completed": "#4CAF50",
            "earning": "#9C27B0",
        }
        color = colors.get(obj.status, "#757575")
        return format_html(
            '<span style="color: white; background-color: {}; padding: 4px 10px; '
            'border-radius: 12px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display().upper(),
        )

    @admin.action(description="🔄 Refresh Schedule Status")
    def regenerate_schedules_action(self, request, queryset):
        for investment in queryset:
            # We trigger the signal logic manually for older records
            stats = investment.schedules.filter(status='paid').aggregate(total=models.Sum('amount'))
            investment.amount_paid = stats['total'] or 0
            investment.save()
        self.message_user(
            request, f"Recalculated financials for {queryset.count()} investment(s)."
        )

    @admin.action(description="✅ Mark as Completed")
    def mark_as_completed(self, request, queryset):
        queryset.update(status="completed", next_payment_date=None)
        self.message_user(request, "Selected investments marked as completed.")

    def save_model(self, request, obj, form, change):
        """
        Wrap the save in a transaction.
        CRITICAL FIX: Refresh from DB after save to reflect signal updates.
        """
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
                # If we changed something in the investment that might trigger signals,
                # or if inline edits happened, we want to see the result of the signals immediately.
                if change:
                    obj.refresh_from_db()
        except IntegrityError:
            obj.refresh_from_db()


# --- 7. PAYMENT SCHEDULE ADMIN (Standalone View) ---


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "get_investment_user",
        "get_project_name",
        "title",
        "installment_number",
        "due_date",
        "formatted_amount",
        "status_badge",
    )
    list_filter = ("status", "due_date", "investment__selected_option__project")

    search_fields = (
        "investment__user__email",
        "title",
        "investment__selected_option__project__name",
    )
    readonly_fields = (
        "investment",
        "title",
        "installment_number",
        "due_date",
        "amount",
    )
    list_select_related = (
        "investment",
        "investment__user",
        "investment__selected_option__project",
    )

    @admin.display(description="User")
    def get_investment_user(self, obj):
        return obj.investment.user.email

    @admin.display(description="Project")
    def get_project_name(self, obj):
        return obj.investment.selected_option.project.name

    @admin.display(description="Amount")
    def formatted_amount(self, obj):
        return f"₦{obj.amount:,.2f}"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "paid": "#4CAF50",
            "overdue": "#F44336",
            "pending": "#FF9800",
            "upcoming": "#9E9E9E",
        }
        color = colors.get(obj.status, "#757575")
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; '
            'border-radius: 10px; font-weight: bold; font-size: 10px;">{}</span>',
            color,
            obj.get_status_display().upper(),
        )

    def has_add_permission(self, request):
        return False
