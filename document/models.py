from django.db import models
from account.models import User


class InvestorDocuments(models.Model):
    DOCUMENT_TYPES = (
        ("allocation", "Allocation Letter"),
        ("contract", "Contract"),
        ("certificate", "Investment Certificate"),
        ("title", "Land Title"),
    )

    investor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to="investment_documents/")
    unlocked = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} - {self.investor}"
