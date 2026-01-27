from django.urls import path
from .views import DocumentListView, DocumentStatsView

urlpatterns = [
    path("documents/", DocumentListView.as_view(), name="document-list"),
    path("documents/stats/", DocumentStatsView.as_view(), name="document-stats"),
]
