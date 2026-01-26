from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from account.models import User


class InvestmentPlan(models.Model):
    """
    Defines ONLY the structure of time, not the price.
    Example: 'Weekly 3 Months', 'Outright Payment'
    """

    PAYMENT_MODES = (
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("one_time", "One Time"),
    )

    name = models.CharField(max_length=255)
    duration_days = models.PositiveIntegerField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES)

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"


class InvestmentProject(models.Model):
    """
    The Asset itself.
    """

    INVESTMENT_TYPES = (
        ("agriculture", "Agriculture"),
        ("real-estate", "Real Estate"),
    )


    ASSET_TYPES = (
        ("terrace", "Terrace"),
    )

    name = models.CharField(max_length=255)
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPES)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)

    location = models.CharField(max_length=255)
    investment_detail = models.TextField()
    roi_start_after_days = models.PositiveIntegerField(
        help_text="Days after completion before ROI starts"
    )
    project_img = models.ImageField(upload_to="project_img/", null=True, blank=True)
    expected_roi_percent = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ProjectPricing(models.Model):
    """
    Bridges Project and Plan.
    Auto-calculates the entry barrier (minimum_deposit) based on the plan duration.
    """

    project = models.ForeignKey(
        InvestmentProject, related_name="pricing_options", on_delete=models.CASCADE
    )
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    minimum_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if self.minimum_deposit == 0:
            if self.plan.payment_mode == "one_time":
                self.minimum_deposit = self.total_price
            else:
                cycles = 1
                if self.plan.payment_mode == "weekly":
                    cycles = self.plan.duration_days // 7
                elif self.plan.payment_mode == "monthly":
                    cycles = self.plan.duration_days // 30

                cycles = max(cycles, 1)
                self.minimum_deposit = round(self.total_price / cycles, 2)

        super().save(*args, **kwargs)

    def installment_amount(self):
        return self.minimum_deposit

    def __str__(self):
        return f"{self.project.name} - {self.plan.name} @ {self.total_price}"


class ClientInvestment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending Deposit"),
        ("paying", "Ongoing Payment"),
        ("completed", "Completed"),
        ("earning", "Earning Returns"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="investments")
    selected_option = models.ForeignKey(ProjectPricing, on_delete=models.PROTECT)
    agreed_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True)
    installment_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(default=now)
    next_payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client Investment"
        verbose_name_plural = "Client Investments"
        ordering = ["-created_at"]

    @property
    def balance(self):
        return max((self.agreed_amount or 0) - self.amount_paid, 0)

    @property
    def percentage_completion(self):
        if not self.agreed_amount or self.agreed_amount == 0:
            return 0
        return round((self.amount_paid / self.agreed_amount) * 100, 2)

    def save(self, *args, **kwargs):
        # 1. Auto-Fill Financials before saving
        if not self.agreed_amount:
            self.agreed_amount = self.selected_option.total_price

        if not self.installment_amount:
            plan = self.selected_option.plan
            if plan.payment_mode == "one_time":
                self.installment_amount = self.agreed_amount
            else:
                cycles = max(
                    plan.duration_days // (7 if plan.payment_mode == "weekly" else 30),
                    1,
                )
                self.installment_amount = round(self.agreed_amount / cycles, 2)

        # 2. Status & Next Payment Logic
        if self.amount_paid >= self.agreed_amount:
            self.status = "completed"
            self.next_payment_date = None
        elif self.amount_paid > 0:
            self.status = "paying"

        super().save(*args, **kwargs)

    def update_schedule_statuses(self):
        """Updates existing schedules based on payments made"""
        total_paid_acc = self.amount_paid
        today = now().date()
        for schedule in self.schedules.all().order_by("installment_number"):
            if total_paid_acc >= schedule.amount:
                schedule.status = "paid"
                if not schedule.date_paid:
                    schedule.date_paid = today
                total_paid_acc -= schedule.amount
            else:
                if schedule.due_date < today:
                    schedule.status = "overdue"
                else:
                    schedule.status = "upcoming"
            schedule.save()

    def __str__(self):
        return f"{self.user.email} - {self.selected_option.project.name}"


class PaymentSchedule(models.Model): 
    STATUS_CHOICES = (
        ("upcoming", "Upcoming"),
        ("pending", "Pending (Due)"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
    )

    investment = models.ForeignKey(
        ClientInvestment, related_name="schedules", on_delete=models.CASCADE
    )

    title = models.CharField(max_length=100)
    installment_number = models.PositiveIntegerField(default=1)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    date_paid = models.DateField(null=True, blank=True)

    proof_of_payment = models.FileField(
        upload_to="payment_proofs/", null=True, blank=True
    )

    class Meta:
        ordering = ["installment_number"]
        unique_together = ["investment", "installment_number"]
        verbose_name = "Payment Schedule"
        verbose_name_plural = "Payment Schedules"

    def __str__(self):
        return f"{self.investment.user.email} - {self.title} ({self.status})"
