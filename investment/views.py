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
