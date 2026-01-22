# from django.contrib import admin
# from .models import InvestmentPlan, InvestmentProject


# @admin.register(InvestmentPlan)
# class InvestmentPlanAdmin(admin.ModelAdmin):
#     list_display = (
#         "name",
#         "payment_mode",
#         "duration_days",
#         "amount_per_time",
#         "active",
#         "created_at",
#     )

#     list_filter = (
#         "payment_mode",
#         "active",
#         "allows_early_completion",
#         "created_at",
#     )

#     search_fields = ("name",)

#     readonly_fields = ("created_at",)

#     fieldsets = (
#         (
#             "Basic Information",
#             {
#                 "fields": (
#                     "name",
#                     "payment_mode",
#                     "duration_days",
#                     "active",
#                 )
#             },
#         ),
#         (
#             "Investment Limits",
#             {
#                 "fields": (
#                     "amount_per_time",
#                 )
#             },
#         ),
#         (
#             "Returns & ROI",
#             {"fields": ("allows_early_completion",)},
#         ),
#         ("System Info", {"fields": ("created_at",)}),
#     )


# @admin.register(InvestmentProject)
# class InvestmentProjectAdmin(admin.ModelAdmin):
#     list_display = (
#         "name",
#         "investment_type",
#         "location",
#         "payment_plan",
#         "expected_roi_percent",
#         "roi_start_after_days",
#         "active",
#     )

#     list_filter = (
#         "investment_type",
#         "active",
#         "location",
#     )

#     search_fields = (
#         "name",
#         "location",
#     )

#     list_select_related = ("payment_plan",)

#     fieldsets = (
#         (
#             "Project Information",
#             {
#                 "fields": (
#                     "name",
#                     "investment_type",
#                     "location",
#                     "active",
#                 )
#             },
#         ),
#         (
#             "Investment Details",
#             {
#                 "fields": (
#                     "payment_plan",
#                     "expected_roi_percent",
#                     "roi_start_after_days",
#                 )
#             },
#         ),
#     )






from django.contrib import admin
from .models import (
    InvestmentPlan, 
    InvestmentProject, 
    ProjectPricing, 
    ClientInvestment, 
    # PaymentTransaction
)

# 1. INVESTMENT PLAN ADMIN
@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "payment_mode",
        "duration_days",
    )
    
    list_filter = (
        "payment_mode",
    )
    
    search_fields = ("name",)
    
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "payment_mode",
                    "duration_days",
                )
            },
        ),
    )


# 2. PROJECT PRICING ADMIN (FIXED)
# This was missing and caused the SystemCheckError.
# It acts as the search engine for the autocomplete box in ClientInvestment.
@admin.register(ProjectPricing)
class ProjectPricingAdmin(admin.ModelAdmin):
    search_fields = ("project__name", "plan__name")
    list_display = ("project", "plan", "total_price")
    list_filter = ("plan",)


# 3. PROJECT PRICING INLINE
# Allows adding multiple price options directly inside the InvestmentProject page
class ProjectPricingInline(admin.TabularInline):
    model = ProjectPricing
    extra = 1
    fields = ('plan', 'total_price', 'minimum_deposit')
    autocomplete_fields = ['plan'] 


# 4. INVESTMENT PROJECT ADMIN
@admin.register(InvestmentProject)
class InvestmentProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "investment_type",
        "location",
        "expected_roi_percent",
        "active",
    )

    list_filter = (
        "investment_type",
        "active",
        "location",
    )

    search_fields = (
        "name",
        "location",
    )

    inlines = [ProjectPricingInline]

    fieldsets = (
        (
            "Project Information",
            {
                "fields": (
                    "name",
                    "investment_type",
                    "location",
                    "active",
                )
            },
        ),
        (
            "Returns Configuration",
            {
                "fields": (
                    "expected_roi_percent",
                    "roi_start_after_days",
                )
            },
        ),
    )


# 5. TRANSACTIONS INLINE
# Shows payment history inside the Client Investment page
# class PaymentTransactionInline(admin.TabularInline):
#     model = PaymentTransaction
#     extra = 0
#     readonly_fields = ('date_paid',)
#     can_delete = False


# 6. CLIENT INVESTMENT ADMIN
@admin.register(ClientInvestment)
class ClientInvestmentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "get_project_name",
        "agreed_amount",
        "amount_paid",
        "get_balance",
        "status",
        "start_date",
    )

    list_filter = ("status", "start_date")
    
    search_fields = ("user__email", "user__first_name", "selected_option__project__name")
    
    # These must be registered admins with 'search_fields' defined
    autocomplete_fields = ['user', 'selected_option']
    
    # inlines = [PaymentTransactionInline]
    
    readonly_fields = ("get_balance", "get_completion_percent", "start_date")

    fieldsets = (
        ("Client Details", {
            "fields": ("user", "selected_option")
        }),
        ("Financials", {
            "fields": ("agreed_amount", "amount_paid", "get_balance", "get_completion_percent")
        }),
        ("Status", {
            "fields": ("status", "next_payment_date", "start_date")
        })
    )

    @admin.display(description='Project')
    def get_project_name(self, obj):
        return obj.selected_option.project.name

    @admin.display(description='Balance')
    def get_balance(self, obj):
        return obj.balance

    @admin.display(description='Completion %')
    def get_completion_percent(self, obj):
        return f"{obj.percentage_completion}%"


# 7. PAYMENT TRANSACTION ADMIN
# @admin.register(PaymentTransaction)
# class PaymentTransactionAdmin(admin.ModelAdmin):
#     list_display = ("investment", "amount", "reference", "is_verified", "date_paid")
#     list_filter = ("is_verified", "date_paid")
#     search_fields = ("reference", "investment__user__email")







