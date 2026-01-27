from django.urls import path
from .views import (
    ClientInvestmentDetailView,
    ClientInvestmentListView,
    CreateInvestmentView,
    InvestmentProjectListView,
    InvestorDashboardView
)

urlpatterns = [
    path("investments/", InvestmentProjectListView.as_view(), name="investments"),
    path(
        "investments/create/", CreateInvestmentView.as_view(), name="investment-create"
    ),
    path(
        "client-investments/",
        ClientInvestmentListView.as_view(),
        name="investment-list",
    ),
    # Endpoint for the Detail Page (Single card data)
    path(
        "client-investments/<int:pk>/",
        ClientInvestmentDetailView.as_view(),
        name="investment-detail",
    ),

     path(
        "dashboard/summary/",
        InvestorDashboardView.as_view(),
        name="investment-detail",
    ),

]






