from django.db import models

from account.models import User
from investment.models import ClientInvestment
from django.utils.timezone import now


# -------------------------------------------------------------------------
# Transactions
# -------------------------------------------------------------------------


class Transaction(models.Model):
    """
    Records every individual payment made by a user for an investment.
    """

    # 1. Who paid
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions", db_index=True
    )
 
    # 2. What investment was paid for
    investment = models.ForeignKey(
        ClientInvestment, on_delete=models.CASCADE, related_name="transaction_history"
    )

    # 3. Investment Location (Captured as a snapshot in case project location changes)
    location = models.CharField(max_length=255)

    # 4. Amount Paid
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    installment_number = models.PositiveIntegerField(null=True, blank=True)
    # 5. Date and Time it was paid
    # Using db_index for fast history sorting and reporting
    timestamp = models.DateTimeField(default=now, db_index=True)

    # 6. Metadata (Optional but recommended for payment tracking)
    payment_reference = models.CharField(
        max_length=100, unique=True, null=True, blank=True
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"₦{self.amount} - {self.user.email} ({self.investment.selected_option.project.name})"

    def save(self, *args, **kwargs):
        # Automatically capture the project location if not manually set
        if not self.location and self.investment:
            self.location = self.investment.selected_option.project.location
        super().save(*args, **kwargs)
 