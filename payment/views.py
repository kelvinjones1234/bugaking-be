import json
import hmac
import hashlib
from decimal import Decimal 
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils.timezone import now
from .models import ClientInvestment, Transaction
from core.settings import get_env_variable
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import TransactionSerializer



@csrf_exempt
@require_POST
def paystack_webhook(request):
    payload = request.body
    sig_header = request.headers.get('x-paystack-signature')
    
    if not sig_header: 
        return HttpResponse(status=400)

    secret = get_env_variable("PAYSTACK_SECRET_KEY", "fallback-secret")
    hash_obj = hmac.new(secret.encode('utf-8'), payload, hashlib.sha512)
    
    if hash_obj.hexdigest() != sig_header:
        return HttpResponse(status=400)

    event = json.loads(payload)

    if event['event'] == 'charge.success':
        data = event['data']
        reference = data['reference']
        
        # Paystack sends amount in Kobo. Convert to Decimal.
        amount_paid = Decimal(data['amount']) / Decimal(100)
        
        metadata = data.get('metadata', {})
        investment_id = metadata.get('investment_id')
        
        try:
            with transaction.atomic():
                # 1. Fetch Investment
                if investment_id:
                    investment = ClientInvestment.objects.select_related(
                        'user', 'selected_option__project'
                    ).get(id=investment_id)
                else:
                    customer_email = data['customer']['email']
                    investment = ClientInvestment.objects.filter(
                        user__email=customer_email, 
                        status__in=["pending", "paying"]
                    ).first()
                
                if not investment:
                    return HttpResponse(status=200)

                # 2. Find the schedule to pay
                next_schedule = investment.schedules.filter(
                    status__in=["upcoming", "pending", "overdue"]
                ).order_by("installment_number").first()
                
                if next_schedule:
                    # 3. Mark Schedule as Paid
                    # We ONLY update the schedule here. The signal will catch this save()
                    # and automatically update the parent Investment's totals.
                    next_schedule.status = "paid"
                    next_schedule.date_paid = now().date()
                    next_schedule.save() 
                    
                    # 4. Record Transaction History
                    Transaction.objects.create(
                        user=investment.user,
                        investment=investment,
                        amount=amount_paid,
                        installment_number=next_schedule.installment_number,
                        location=investment.selected_option.project.location,
                        payment_reference=reference
                    )
                    
        except Exception as e:
            print(f"Error processing webhook: {e}")

    return HttpResponse(status=200)





class TransactionListView(generics.ListAPIView):
    """
    Returns a paginated list of transactions for the logged-in user.
    Supports search and filtering.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Enable Search and Filtering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Fields to filter by exactly (for dropdowns)
    filterset_fields = [
        'investment__selected_option__project__investment_type', # Sector filter
    ]
    
    # Fields to search text (for search bar)
    search_fields = [
        'payment_reference', 
        'location', 
        'investment__selected_option__project__name'
    ]
    
    # Default ordering
    ordering = ['-timestamp']

    def get_queryset(self):
        # Only show transactions belonging to the logged-in user
        return Transaction.objects.filter(user=self.request.user).select_related(
            'investment', 
            'investment__selected_option__project'
        )

class TransactionStatsView(APIView):
    """
    Returns the total stats for the transaction page header.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Calculate total amount spent across all transactions
        total_invested = Transaction.objects.filter(user=user).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # You can add logic here for "percentage growth" if you have that data,
        # otherwise return a static or calculated value.
        
        return Response({
            "total_invested": total_invested,
            "currency": "NGN"
        })