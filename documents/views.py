from rest_framework import generics, permissions, filters
from .models import Document
from .serializers import DocumentSerializer
from rest_framework.views import APIView
from rest_framework.response import Response


class DocumentListView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Enable search and filtering functionality
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "category"]
    ordering_fields = ["created_at", "title"]

    def get_queryset(self):
        """
        This is the critical part:
        Return ONLY documents belonging to the currently logged-in user.
        """
        return Document.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        When uploading, automatically assign the document to the current user.
        """
        serializer.save(user=self.request.user)


class DocumentStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_docs = Document.objects.filter(user=request.user)

        return Response(
            {
                "total": user_docs.count(),
                "agreements": user_docs.filter(category="agreement").count(),
                "deeds": user_docs.filter(category="deed").count(),
                "reports": user_docs.filter(category="report").count(),
            }
        )
