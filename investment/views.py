from rest_framework import generics, permissions, status
from .models import InvestmentProject, ClientInvestment
from .serializers import (
    ClientInvestmentDetailSerializer,
    CreateInvestmentSerializer,
    InvestmentProjectSerializer,
    ClientInvestmentSerializer,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404


class InvestmentProjectListView(generics.ListAPIView):
    serializer_class = InvestmentProjectSerializer
    queryset = InvestmentProject.objects.filter(active=True)


class CreateInvestmentView(generics.CreateAPIView):
    serializer_class = CreateInvestmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        investment = serializer.save()

        # Return a custom response structure matching your Frontend Interface
        return Response(
            {
                "message": "Investment initiated successfully",
                "investment_id": investment.id,
                "status": investment.status,
            },
            status=status.HTTP_201_CREATED,
        )


class ClientInvestmentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # 1. Base Query: User's investments
        queryset = ClientInvestment.objects.filter(user=request.user).order_by(
            "-start_date"
        )

        # 2. Filter Logic
        category = request.query_params.get(
            "category"
        )  # e.g., 'agriculture' or 'real_estate'

        if category:
            category = category.lower()

            queryset = queryset.filter(
                selected_option__project__investment_type=category
            )

        # 3. Serialize
        serializer = ClientInvestmentSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClientInvestmentDetailView(APIView):
    """
    GET: Retrieve details of a specific investment.
    Ensures the user can only view their own investment.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        # 1. Get object or 404, strictly filtering by user=request.user
        # This prevents User A from guessing User B's investment ID
        investment = get_object_or_404(ClientInvestment, pk=pk, user=request.user)

        # 2. Serialize the single object
        serializer = ClientInvestmentDetailSerializer(investment)

        # 3. Return JSON response
        return Response(serializer.data, status=status.HTTP_200_OK)












from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg
from django.utils.timezone import now
from .models import ClientInvestment, PaymentSchedule
from .serializers import DashboardSummarySerializer

class InvestorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = now().date()

        # 1. Base Query
        investments = ClientInvestment.objects.filter(user=user)

        # 2. Aggregates
        total_invested = investments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        portfolio_value = investments.aggregate(Sum('agreed_amount'))['agreed_amount__sum'] or 0
        
        # Calculate Average ROI
        avg_roi = investments.aggregate(
            Avg('selected_option__project__expected_roi_percent')
        )['selected_option__project__expected_roi_percent__avg'] or 0

        # 3. Next Payment Logic (Find the earliest upcoming schedule)
        next_schedule = PaymentSchedule.objects.filter(
            investment__user=user,
            status__in=['upcoming', 'pending', 'overdue']
        ).order_by('due_date').first()

        next_payment_data = None
        if next_schedule:
            days_left = (next_schedule.due_date - today).days
            next_payment_data = {
                "title": next_schedule.title,
                "amount": next_schedule.amount,
                "due_date": next_schedule.due_date,
                # Ensure days_left isn't negative for the "Days Left" display, 
                # though you might want to handle 'overdue' logic in frontend
                "days_left": max(days_left, 0) 
            }

        # 4. Recent Transactions (Last 5 paid items)
        recent_transactions = PaymentSchedule.objects.filter(
            investment__user=user,
            status='paid'
        ).select_related('investment__selected_option__project').order_by('-date_paid')[:5]

        # 5. Active Portfolio items
        # Note: We assign this to 'portfolio_items'
        portfolio_items = investments.exclude(status='completed').select_related('selected_option__project')[:3]

        # 6. Assemble Data
        data = {
            "total_invested": total_invested,
            "portfolio_value": portfolio_value,
            
            # Fix 1: Ensure this key matches DashboardSummarySerializer field name exactly
            "projected_roi_percentage": avg_roi, 
            
            "next_payment": next_payment_data,
            "recent_transactions": recent_transactions,
            
            # Fix 2: Use the variable defined in Step 5 ('portfolio_items'), not 'active_portfolio'
            "portfolio_items": portfolio_items 
        }

        # Note: context={'request': request} is added to ensure ImageFields generate full URLs
        serializer = DashboardSummarySerializer(data, context={'request': request})
        return Response(serializer.data)