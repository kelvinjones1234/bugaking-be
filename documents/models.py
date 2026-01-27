import os
from django.db import models
from django.conf import settings


class Document(models.Model):
    CATEGORY_CHOICES = (
        ("agreement", "Investment Agreement"),
        ("deed", "Property Deed"),
        ("report", "Financial Report"),
        ("other", "Other"),
    )

    # 1. Ownership: Each document belongs to exactly one user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_documents"
    )

    # 2. File Information
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="secure_vault/%Y/%m/")
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="other"
    )

    # 3. Metadata (Auto-populated)
    file_size = models.CharField(max_length=50, blank=True)  # e.g., "2.4 MB"
    file_type = models.CharField(max_length=10, blank=True)  # e.g., "PDF"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user.email})"

    def save(self, *args, **kwargs):
        # Auto-calculate file size and type before saving
        if self.file:
            # Get extension (e.g., .pdf -> PDF)
            self.file_type = os.path.splitext(self.file.name)[1][1:].upper()

            # Calculate size
            if self.file.size < 1024 * 1024:
                self.file_size = f"{round(self.file.size / 1024, 1)} KB"
            else:
                self.file_size = f"{round(self.file.size / (1024 * 1024), 1)} MB"

        super().save(*args, **kwargs)
