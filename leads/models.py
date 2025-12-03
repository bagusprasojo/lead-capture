import uuid
from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

User = get_user_model()


class BusinessProfile(models.Model):
    """Stores business level metadata and embed identifiers."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='business_profile',
    )
    business_name = models.CharField(max_length=255)
    public_id = models.CharField(
        max_length=12,
        unique=True,
        editable=False,
    )
    notification_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['business_name']

    def __str__(self) -> str:
        return self.business_name or self.user.get_username()

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = uuid.uuid4().hex[:12]
        super().save(*args, **kwargs)

    def public_form_url(self):
        return reverse('leads:public_form', args=[self.public_id])

    def embed_script_url(self):
        return reverse('leads:embed_script', args=[self.public_id])


class Lead(models.Model):
    """Represents a capture submission belonging to a single owner."""

    STATUS_NEW = 'NEW'
    STATUS_CONTACTED = 'CONTACTED'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_CONTACTED, 'Contacted'),
        (STATUS_CLOSED, 'Closed'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leads',
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    message = models.TextField(validators=[MaxLengthValidator(2000)])
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} ({self.email})'

    def get_absolute_url(self):
        return reverse('leads:dashboard')


@receiver(post_save, sender=User)
def ensure_business_profile(sender, instance, created, **_):
    """Create a blank profile for any new user."""
    if created:
        BusinessProfile.objects.create(
            user=instance,
            business_name=instance.get_username(),
            notification_email=getattr(instance, 'email', ''),
        )
