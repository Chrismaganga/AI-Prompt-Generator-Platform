from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class CustomUser(AbstractUser):
    """Custom user model for the prompt platform."""
    
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_creator = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_account_id = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.email
    
    def get_absolute_url(self):
        return reverse('user_profile', kwargs={'username': self.username})
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username 