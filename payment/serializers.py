from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    # Flatten related data for easier frontend consumption
    project_name = serializers.CharField(
        source="investment.selected_option.project.name", read_only=True
    )
    investment_type = serializers.CharField(
        source="investment.selected_option.project.investment_type", read_only=True
    )
    project_image = serializers.ImageField(
        source="investment.selected_option.project.project_img", read_only=True
    )
    
    # Format the timestamp for display if you prefer backend formatting, 
    # though frontend formatting (new Date()) is usually more flexible.
    formatted_date = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "timestamp",
            "formatted_date",
            "formatted_time",
            "payment_reference",
            "amount",
            "location",
            "installment_number",
            "project_name",
            "investment_type",
            "project_image",
        ]

    def get_formatted_date(self, obj):
        return obj.timestamp.strftime("%b %d, %Y")

    def get_formatted_time(self, obj):
        return obj.timestamp.strftime("%H:%M:%S GMT")