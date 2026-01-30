from django.urls import path
from . import views
from .views import TransactionListView, TransactionStatsView

# urls.py
urlpatterns = [
    path("webhooks/paystack/", views.paystack_webhook, name="paystack_webhook"),
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path(
        "transactions/stats/", TransactionStatsView.as_view(), name="transaction-stats"
    ),
]
