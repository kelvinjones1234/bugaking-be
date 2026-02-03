from django.db import models
from django.utils.timezone import now
from account.models import User

# -------------------------------------------------------------------------
# Investment Plan
# -------------------------------------------------------------------------

class InvestmentPlan(models.Model):
    """
    Defines ONLY the structure of time, not the price.
    """
    PAYMENT_MODES = (
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("one_time", "One Time"),
    )

    name = models.CharField(max_length=255)
    duration_days = models.PositiveIntegerField()
    # Added db_index=True as plans are likely filtered by mode
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"


# -------------------------------------------------------------------------
# Investment Project
# -------------------------------------------------------------------------

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
        ("farmland", "Farmland"),
    )

    name = models.CharField(max_length=255, db_index=True) # Indexed for search
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPES, db_index=True)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    
    location = models.CharField(max_length=255)
    investment_detail = models.TextField()
    roi_start_after_days = models.PositiveIntegerField(
        help_text="Days after completion before ROI starts"
    )
    project_img = models.ImageField(upload_to="project_img/", null=True, blank=True)
    expected_roi_percent = models.DecimalField(max_digits=5, decimal_places=2)
    # Indexed to quickly filter valid projects
    active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.name


# -------------------------------------------------------------------------
# Project Pricing
# -------------------------------------------------------------------------

class ProjectPricing(models.Model):
    """
    Bridges Project and Plan.
    """
    project = models.ForeignKey(
        InvestmentProject, related_name="pricing_options", on_delete=models.CASCADE
    )
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    minimum_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        # Optimization: Prevent duplicate pricing for the same project/plan combo
        # and create a composite index for faster lookups.
        constraints = [
            models.UniqueConstraint(fields=['project', 'plan'], name='unique_project_plan')
        ]

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
        # Note: This triggers a DB hit if project/plan are not pre-fetched.
        # Handled generally via View optimization, but kept simple here.
        return f"{self.project.name} - {self.plan.name} @ {self.total_price}"


# -------------------------------------------------------------------------
# Client Investment
# -------------------------------------------------------------------------

class ClientInvestmentManager(models.Manager):
    """
    Custom manager to optimize queries by pre-fetching related tables.
    Solves N+1 issues when listing investments (e.g., in Admin or Dashboard).
    """
    def get_queryset(self):
        return super().get_queryset().select_related(
            'user', 
            'selected_option__project', 
            'selected_option__plan'
        )

class ClientInvestment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending Deposit"),
        ("paying", "Ongoing Payment"),
        ("completed", "Completed"),
        ("earning", "Earning Returns"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="investments", db_index=True)
    selected_option = models.ForeignKey(ProjectPricing, on_delete=models.PROTECT)
    agreed_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True)
    installment_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(default=now)
    next_payment_date = models.DateField(null=True, blank=True)
    # Index status for fast filtering of "Pending" vs "Completed"
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True) # Indexed for sorting
    updated_at = models.DateTimeField(auto_now=True)

    objects = ClientInvestmentManager() # Attach the optimized manager

    class Meta:
        verbose_name = "Client Investment"
        verbose_name_plural = "Client Investments"
        # Removing default ordering from Meta can speed up aggregation queries, 
        # but if you rely on it for UI, keep it. Since we indexed created_at, this is fast.
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
        # 1. Auto-Fill Financials
        if not self.agreed_amount:
            self.agreed_amount = self.selected_option.total_price

        if not self.installment_amount:
            plan = self.selected_option.plan
            if plan.payment_mode == "one_time":
                self.installment_amount = self.agreed_amount
            else:
                # Use simple division, ensure no ZeroDivisionError
                divider = 7 if plan.payment_mode == "weekly" else 30
                cycles = max(plan.duration_days // divider, 1)
                self.installment_amount = round(self.agreed_amount / cycles, 2)

        # 2. Status & Next Payment Logic
        if self.amount_paid >= self.agreed_amount:
            self.status = "completed"
            self.next_payment_date = None
        elif self.amount_paid > 0:
            self.status = "paying"

        super().save(*args, **kwargs)

    def update_schedule_statuses(self):
        """
        OPTIMIZED: Uses bulk_update to reduce DB writes from O(N) to O(1).
        """
        total_paid_acc = self.amount_paid
        today = now().date()
        
        # Fetch all schedules in one query
        schedules = list(self.schedules.all().order_by("installment_number"))
        
        schedules_to_update = []
        
        for schedule in schedules:
            original_status = schedule.status
            original_date_paid = schedule.date_paid
            
            # Logic calculation
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
            
            # Only add to update list if something actually changed
            if schedule.status != original_status or schedule.date_paid != original_date_paid:
                schedules_to_update.append(schedule)

        if schedules_to_update:
            PaymentSchedule.objects.bulk_update(
                schedules_to_update, 
                ['status', 'date_paid']
            )

    def __str__(self):
        # Because of ClientInvestmentManager, selected_option and project are pre-fetched.
        return f"{self.user.email} - {self.selected_option.project.name}"


# -------------------------------------------------------------------------
# Payment Schedule
# -------------------------------------------------------------------------

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
    # Index due_date for cron jobs checking for overdue payments
    due_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming", db_index=True)
    date_paid = models.DateField(null=True, blank=True)

    proof_of_payment = models.FileField(
        upload_to="payment_proofs/", null=True, blank=True
    )

    class Meta:
        ordering = ["installment_number"]
        unique_together = ["investment", "installment_number"]
        verbose_name = "Payment Schedule"
        verbose_name_plural = "Payment Schedules"
        # Composite index for common lookups (e.g., "Find all overdue schedules")
        indexes = [
            models.Index(fields=['status', 'due_date']),
        ]

    def __str__(self):
        return f"{self.investment.user.email} - {self.title} ({self.status})"