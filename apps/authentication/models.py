import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import TimeStampedModel


class UserRole(models.TextChoices):
    FREELANCER = 'FREELANCER', 'Freelancer'
    CLIENT = 'CLIENT', 'Client'
    ADMIN = 'ADMIN', 'Admin'

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('Email address', unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.FREELANCER,
        db_index=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_freelancer(self) -> bool:
        return self.role == UserRole.FREELANCER or self.is_superuser

    @property
    def is_client_user(self) -> bool:
        return self.role == UserRole.CLIENT


class FreelancerProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    business_name = models.CharField(max_length=255, blank=True, default='')
    logo = models.ImageField(upload_to='profiles/logos/', blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, default='', help_text='GST / VAT / Tax ID')
    address = models.TextField(blank=True, default='')
    currency = models.CharField(max_length=10, default='USD')
    default_payment_terms_days = models.PositiveIntegerField(default=14, help_text='Default payment window in days')
    bank_details = models.TextField(blank=True, default='', help_text='Bank Account / Wire transfer details')
    upi_id = models.CharField(max_length=100, blank=True, default='', help_text='UPI ID for instant transfers')
    brand_color = models.CharField(max_length=7, default='#6366F1', help_text='Hex color code for branding')
    timezone = models.CharField(max_length=50, default='UTC')
    onboarding_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.business_name or self.user.get_full_name() or self.user.email

    @property
    def display_name(self):
        return self.business_name or self.user.get_full_name() or self.user.username


@receiver(post_save, sender=User)
def create_or_update_freelancer_profile(sender, instance, created, **kwargs):
    """Automatically create FreelancerProfile for newly created Freelancers."""
    if created and instance.role == UserRole.FREELANCER:
        FreelancerProfile.objects.create(
            user=instance,
            business_name=f"{instance.first_name} {instance.last_name}".strip() or instance.username
        )


class NotificationType(models.TextChoices):
    INFO = 'INFO', 'Information'
    SUCCESS = 'SUCCESS', 'Success'
    WARNING = 'WARNING', 'Warning'
    INVOICE = 'INVOICE', 'Invoice'
    MILESTONE = 'MILESTONE', 'Milestone'
    PAYMENT = 'PAYMENT', 'Payment'
    PROJECT = 'PROJECT', 'Project'


class Notification(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    url = models.CharField(max_length=500, blank=True, default='')
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        db_index=True
    )
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title}"


def create_notification(user, title, message, url='', notification_type=NotificationType.INFO):
    """Utility to spawn an in-app alert notification."""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        url=url,
        notification_type=notification_type
    )

