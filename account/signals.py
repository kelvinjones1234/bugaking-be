from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, User 

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # FIX: Wrap in try/except to handle users who don't have a profile yet
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # If the profile is missing, create it now
        Profile.objects.create(user=instance)