from rest_framework import serializers
from .models import InvestmentProject, PaymentSchedule, ProjectPricing, ClientInvestment
from django.utils.timezone import now


class ProjectPricingSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name")
    plan_duration_days = serializers.IntegerField(source="plan.duration_days")
    payment_mode = serializers.CharField(source="plan.payment_mode")

    # Custom field to calculate readable ROI start based on plan duration
    roi_start_display = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPricing
        fields = [
            "id",
            "plan_name",
            "plan_duration_days",
            "payment_mode",
            "total_price",
            "minimum_deposit",
            "roi_start_display",
        ]

    def get_roi_start_display(self, obj):
        """
        Calculates when ROI starts relative to the plan.
        One-time = Project ROI start days.
        Installment = Plan duration + Project ROI start days.
        """
        base_wait = obj.project.roi_start_after_days

        if obj.plan.payment_mode == "one_time":
            days_wait = base_wait
        else:
            days_wait = obj.plan.duration_days + base_wait

        if days_wait <= 0:
            return "Immediate"
        elif days_wait < 30:
            return f"{days_wait} Days"
        else:
            months = round(days_wait / 30)
            return f"Month {months}"


class InvestmentProjectSerializer(serializers.ModelSerializer):
    pricing_options = ProjectPricingSerializer(many=True, read_only=True)

    # Pre-formatted string for the frontend header "Real Estate • Lagos, NG"
    category_display = serializers.SerializerMethodField()

    class Meta:
        model = InvestmentProject
        fields = [
            "id",
            "name", 
            "investment_type",
            "asset_type",
            "location",
            "category_display",
            "investment_detail",
            "roi_start_after_days",
            "project_img",
            "expected_roi_percent",
            "active",
            "pricing_options",
        ]

    def get_category_display(self, obj):
        return f"{obj.get_investment_type_display()} • {obj.location}"


class PaymentScheduleSerializer(serializers.ModelSerializer):
    formatted_date = serializers.SerializerMethodField()

    class Meta:
        model = PaymentSchedule
        fields = ["id", "title", "due_date", "formatted_date", "amount", "status"]

    def get_formatted_date(self, obj):
        return obj.due_date.strftime("%b %d, %Y")







class ClientInvestmentSerializer(serializers.ModelSerializer):
    # Flattened Project Data
    project_name = serializers.CharField(
        source="selected_option.project.name", read_only=True
    )
    project_image = serializers.ImageField(
        source="selected_option.project.project_img", read_only=True
    )
    location = serializers.CharField(
        source="selected_option.project.location", read_only=True
    )

    # Financials
    balance = serializers.ReadOnlyField()  # Pulls from @property in Model
    percentage_completion = serializers.SerializerMethodField()

    # Payment Tracking
    next_payment_data = serializers.SerializerMethodField()

    class Meta:
        model = ClientInvestment
        fields = [
            "id",
            "status",
            "project_name",
            "selected_option",
            "project_image",
            "agreed_amount",
            "location",
            "amount_paid",
            "balance",
            "percentage_completion",
            "next_payment_data",
        ]

    def get_percentage_completion(self, obj):
        if not obj.agreed_amount or obj.agreed_amount == 0:
            return 0
        return round((obj.amount_paid / obj.agreed_amount) * 100, 2)

    def get_next_payment_data(self, obj):
        """
        Grabs the next unpaid installment to show on the dashboard card.
        """
        next_sched = (
            obj.schedules.exclude(status="paid").order_by("installment_number").first()
        )
        if next_sched:
            return {
                "title": next_sched.title,
                "amount": next_sched.amount,
                "due_date": next_sched.due_date,
                "days_left": (next_sched.due_date - now().date()).days,
            }
        return None








class ClientInvestmentDetailSerializer(ClientInvestmentSerializer):
    """
    Detailed view including full payment history/schedules.
    """

    schedules = PaymentScheduleSerializer(many=True, read_only=True)
    roi = serializers.SerializerMethodField()

    class Meta(ClientInvestmentSerializer.Meta):
        fields = ClientInvestmentSerializer.Meta.fields + ["schedules", "roi"]

    def get_roi(self, obj):
        # Agriculture has no ROI based on your previous requirement
        if obj.selected_option.project.investment_type == "agriculture":
            return None
        return obj.selected_option.project.expected_roi_percent















class CreateInvestmentSerializer(serializers.ModelSerializer):
    # We map the frontend's 'pricing_id' directly to the model's 'selected_option'
    pricing_id = serializers.PrimaryKeyRelatedField(
        queryset=ProjectPricing.objects.all(),
        source='selected_option', 
        write_only=True
    )

    class Meta:
        model = ClientInvestment
        fields = ['pricing_id', 'id', 'status']
        read_only_fields = ['id', 'status']

    def validate_pricing_id(self, value):
        """
        Ensure the project associated with this pricing is actually active.
        """
        if not value.project.active:
            raise serializers.ValidationError("This investment project is currently closed.")
        return value

    def create(self, validated_data):
        # Inject the user from the request context
        validated_data['user'] = self.context['request'].user
        
        # We let the Model's save() method handle the auto-calculation 
        # of agreed_amount, installment_amount, etc.
        return super().create(validated_data)