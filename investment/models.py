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
    
    # We removed 'amount_per_time'. Prices belong to the Project, not the Plan template.

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"


class InvestmentProject(models.Model):
    """
    The Asset itself.
    """
    INVESTMENT_TYPES = (
        ("farmland", "Farmland"),
        ("terrace", "Terrace"),
    )

    name = models.CharField(max_length=255)
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPES)
    location = models.CharField(max_length=255)
    
    # ROI Logic
    roi_start_after_days = models.PositiveIntegerField(help_text="Days after completion before ROI starts")
    expected_roi_percent = models.DecimalField(max_digits=5, decimal_places=2)
    
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name




class ProjectPricing(models.Model):
    """
    Bridges Project and Plan. 
    Auto-calculates the entry barrier (minimum_deposit) based on the plan duration.
    """
    project = models.ForeignKey(InvestmentProject, related_name="pricing_options", on_delete=models.CASCADE)
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # This will now be auto-filled if left as 0
    minimum_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Auto-compute Minimum Deposit if not manually set
        if self.minimum_deposit == 0:
            if self.plan.payment_mode == 'one_time':
                # For outright payment, the minimum deposit is the full price
                self.minimum_deposit = self.total_price
            else:
                # For installment plans, minimum deposit = cost of ONE cycle
                cycles = 1
                if self.plan.payment_mode == 'weekly':
                    cycles = self.plan.duration_days // 7
                elif self.plan.payment_mode == 'monthly':
                    cycles = self.plan.duration_days // 30
                
                # Prevent division by zero and ensure at least 1 cycle
                cycles = max(cycles, 1)
                
                # Calculate one installment
                self.minimum_deposit = round(self.total_price / cycles, 2)

        super().save(*args, **kwargs)

    def installment_amount(self):
        """Helper method to show what the user pays per cycle"""
        # We can reuse minimum_deposit logic since they are usually the same
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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(ProjectPricing, on_delete=models.PROTECT)
    
    # 1. Total Agreed Price (Auto-filled)
    agreed_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True)
    
    # 2. Deposit Per Time / Installment Amount (Auto-filled)
    # This stores exactly how much they should pay per week/month.
    installment_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    start_date = models.DateField(default=now)
    next_payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    @property
    def balance(self):
        if self.agreed_amount is None:
            return 0
        return max(self.agreed_amount - self.amount_paid, 0)

    @property
    def percentage_completion(self):
        if not self.agreed_amount or self.agreed_amount == 0: 
            return 0
        return round((self.amount_paid / self.agreed_amount) * 100, 2)

    def save(self, *args, **kwargs):
        # --- A. Auto-Fill Financials ---
        
        # 1. Fill Agreed Amount from Pricing Option if missing
        if not self.agreed_amount:
            self.agreed_amount = self.selected_option.total_price

        # 2. Calculate "Deposit Per Time" (Installment Amount)
        if not self.installment_amount:
            plan = self.selected_option.plan
            
            if plan.payment_mode == 'one_time':
                self.installment_amount = self.agreed_amount
            else:
                # Calculate number of cycles (e.g., 90 days / 30 = 3 months)
                if plan.payment_mode == 'weekly':
                    cycles = plan.duration_days // 7
                elif plan.payment_mode == 'monthly':
                    cycles = plan.duration_days // 30
                else:
                    cycles = 1
                
                # Prevent division by zero
                cycles = max(cycles, 1)
                self.installment_amount = round(self.agreed_amount / cycles, 2)

        # --- B. Dynamic Date Scheduling ---
        
        # Only calculate next date if the investment is active/pending and not fully paid
        if self.status in ['pending', 'paying'] and self.installment_amount > 0:
            
            # If they have paid everything (or more due to slight overpayment), stop scheduling
            if self.amount_paid >= self.agreed_amount:
                self.next_payment_date = None
            else:
                plan_mode = self.selected_option.plan.payment_mode
                
                if plan_mode == 'one_time':
                    # For one-time, it is always due immediately (start_date) until paid
                    self.next_payment_date = self.start_date
                else:
                    # Determine interval in days
                    interval_days = 7 if plan_mode == 'weekly' else 30
                    
                    # LOGIC: How many full installments have been covered?
                    # Example: Installment=100. Paid=250. 
                    # They covered Installment 1 and 2. They are now working on Installment 3.
                    cycles_covered = int(self.amount_paid // self.installment_amount)
                    
                    # The next payment is due at the end of the NEXT cycle
                    # Cycle 1 ends: Start + 7 days
                    # Cycle 2 ends: Start + 14 days
                    next_due_cycle = cycles_covered + 1
                    days_until_due = next_due_cycle * interval_days
                    
                    self.next_payment_date = self.start_date + timedelta(days=days_until_due)

        # --- C. Status Updates ---
        
        if self.agreed_amount and self.amount_paid >= self.agreed_amount:
            if self.status != 'earning':
                self.status = 'completed'
                self.next_payment_date = None
        
        elif self.amount_paid > 0 and self.amount_paid < self.agreed_amount:
            self.status = 'paying'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.selected_option.project.name}"