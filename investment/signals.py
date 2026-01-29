# from django.db import transaction, models
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from datetime import timedelta
# from .models import ClientInvestment, PaymentSchedule

# # --- SIGNAL 1: GENERATE SCHEDULES ON CREATION ---
# @receiver(post_save, sender=ClientInvestment)
# def handle_investment_creation(sender, instance, created, **kwargs):
#     if created:
#         transaction.on_commit(lambda: generate_schedules(instance))

# def generate_schedules(instance):
#     if instance.schedules.exists():
#         return

#     plan = instance.selected_option.plan
#     total_amount = float(instance.agreed_amount)
    
#     if plan.payment_mode == "one_time":
#         cycles, interval = 1, 0
#     elif plan.payment_mode == "weekly":
#         cycles, interval = max(plan.duration_days // 7, 1), 7
#     else: # monthly
#         cycles, interval = max(plan.duration_days // 30, 1), 30

#     schedules = []
#     base_amt = round(total_amount / cycles, 2)
    
#     for i in range(1, cycles + 1):
#         due = instance.start_date + timedelta(days=interval * (i - 1))
        
#         if i == cycles:
#             amt = round(total_amount - (base_amt * (cycles - 1)), 2)
#         else:
#             amt = base_amt
        
#         schedules.append(PaymentSchedule(
#             investment=instance,
#             installment_number=i,
#             title=f"Installment {i}" if cycles > 1 else "Full Payment",
#             due_date=due,
#             amount=amt,
#             status='upcoming'
#         ))
    
#     PaymentSchedule.objects.bulk_create(schedules, ignore_conflicts=True)

# # --- SIGNAL 2: UPDATE BALANCE ON PAYMENT ---
# @receiver(post_save, sender=PaymentSchedule)
# def sync_investment_on_payment(sender, instance, **kwargs):
#     """
#     Whenever a schedule is marked as 'paid', we update the 
#     parent ClientInvestment's amount_paid and status.
#     """
#     investment = instance.investment
#     # Sum all schedules marked as 'paid'
#     paid_total = investment.schedules.filter(status='paid').aggregate(
#         total=models.Sum('amount'))['total'] or 0
    
#     investment.amount_paid = paid_total
    
#     # Auto-update status
#     if investment.amount_paid >= investment.agreed_amount:
#         investment.status = "completed"
#     elif investment.amount_paid > 0:
#         investment.status = "paying"
        
#     # Save only the relevant fields to avoid infinite loops
#     investment.save(update_fields=['amount_paid', 'status'])















from django.db import transaction, models
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from datetime import timedelta
from .models import ClientInvestment, PaymentSchedule

# --- SIGNAL 1: GENERATE SCHEDULES ON CREATION ---
@receiver(post_save, sender=ClientInvestment)
def handle_investment_creation(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: generate_schedules(instance))

def generate_schedules(instance):
    if instance.schedules.exists():
        return

    plan = instance.selected_option.plan
    total_amount = float(instance.agreed_amount)
    
    if plan.payment_mode == "one_time":
        cycles, interval = 1, 0
    elif plan.payment_mode == "weekly":
        cycles, interval = max(plan.duration_days // 7, 1), 7
    else: # monthly
        cycles, interval = max(plan.duration_days // 30, 1), 30

    schedules = []
    base_amt = round(total_amount / cycles, 2)
    
    for i in range(1, cycles + 1):
        due = instance.start_date + timedelta(days=interval * (i - 1))
        
        # Handle rounding errors on the last cycle
        if i == cycles:
            amt = round(total_amount - (base_amt * (cycles - 1)), 2)
        else:
            amt = base_amt
        
        schedules.append(PaymentSchedule(
            investment=instance,
            installment_number=i,
            title=f"Installment {i}" if cycles > 1 else "Full Payment",
            due_date=due,
            amount=amt,
            status='upcoming'
        ))
    
    PaymentSchedule.objects.bulk_create(schedules, ignore_conflicts=True)

# --- SIGNAL 2: UPDATE BALANCE ON PAYMENT ---
@receiver(post_save, sender=PaymentSchedule)
def sync_investment_on_payment(sender, instance, **kwargs):
    """
    Consolidated Logic:
    Whenever a schedule changes, we recalculate the parent Investment's 
    total 'amount_paid' by summing all schedules marked as 'paid'.
    """
    investment = instance.investment
    
    # 1. Calculate the true total from DB rows (Single Source of Truth)
    # We use aggregate to avoid race conditions with python variables
    stats = investment.schedules.filter(status='paid').aggregate(
        total_paid=models.Sum('amount')
    )
    
    # Handle None if no schedules are paid yet
    current_total_paid = stats['total_paid'] or Decimal('0.00')
    
    # 2. Update the parent Investment
    investment.amount_paid = current_total_paid
    
    # 3. Update Status based on the new total
    # We use a small epsilon for float comparison safety if needed, 
    # but Decimal handles equality well.
    if investment.amount_paid >= investment.agreed_amount:
        investment.status = "completed"
        investment.next_payment_date = None
    elif investment.amount_paid > 0:
        investment.status = "paying"
        
    # 4. Save specifically these fields to prevent recursion
    investment.save(update_fields=['amount_paid', 'status', 'next_payment_date'])















