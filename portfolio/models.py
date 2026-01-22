from django.conf import settings
from django.db import models
from account.models import User


class Portfolio(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Portfolio - {self.owner.email}"
