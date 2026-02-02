from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models, transaction


# 1. THE MANAGER
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)
        
        # Optimization: Use atomic transaction to ensure data integrity.
        # This acts faster and safer than relying on signals for Profile creation.
        with transaction.atomic():
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)

            # Optimization: Create Profile immediately. 
            # Eliminates the need for a slow 'post_save' signal receiver.
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)
                
            return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_approved", True) # Superusers are auto-approved

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# 2. THE USER MODEL (Authentication)
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True) # Explicit index
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True)

    # Financial/Platform specific flags
    # Optimization: Added db_index=True to boolean flags used in filtering
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_approved = models.BooleanField(
        default=False, db_index=True
    ) 

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        # Optimization: Default ordering helps pagination speed
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email


# 3. THE PROFILE MODEL (Information/Dashboard data)
class ProfileManager(models.Manager):
    """
    Optimization: Pre-fetches the related User object to prevent N+1 queries
    when listing profiles (e.g. in Admin or Dashboards).
    """
    def get_queryset(self):
        return super().get_queryset().select_related("user")

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", null=True, blank=True)
    
    # Attach optimized manager
    objects = ProfileManager()

    def __str__(self):
        # Because of ProfileManager, accessing self.user.email does not hit DB again
        return f"Profile of {self.user.email}"
    

