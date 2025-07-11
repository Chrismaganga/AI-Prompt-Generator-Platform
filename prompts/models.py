from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from taggit.managers import TaggableManager
from ckeditor.fields import RichTextField
from star_ratings.models import Rating

User = get_user_model()


class Category(models.Model):
    """Category model for organizing prompts."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    color = models.CharField(max_length=7, default="#3B82F6", help_text="Hex color code")
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Prompt(models.Model):
    """Main prompt model for AI prompts."""
    PRICE_CHOICES = [
        ('free', 'Free'),
        ('paid', 'Paid'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    content = RichTextField()
    preview_content = models.TextField(help_text="Sample output or preview")
    
    # Pricing
    price_type = models.CharField(max_length=10, choices=PRICE_CHOICES, default='free')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Metadata
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='prompts')
    tags = TaggableManager(blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompts')
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    
    # Statistics
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    purchases = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('prompt_detail', kwargs={'slug': self.slug})
    
    @property
    def average_rating(self):
        """Get average rating for this prompt."""
        try:
            rating = Rating.objects.get(object_id=self.id, content_type__model='prompt')
            return rating.average
        except Rating.DoesNotExist:
            return 0
    
    @property
    def total_ratings(self):
        """Get total number of ratings for this prompt."""
        try:
            rating = Rating.objects.get(object_id=self.id, content_type__model='prompt')
            return rating.count
        except Rating.DoesNotExist:
            return 0


class PromptImage(models.Model):
    """Model for storing prompt preview images."""
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='prompt_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'created_at']
    
    def __str__(self):
        return f"{self.prompt.title} - {self.caption or 'Image'}"


class PromptReview(models.Model):
    """Model for user reviews on prompts."""
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['prompt', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.prompt.title} ({self.rating}/5)"


class PromptPurchase(models.Model):
    """Model for tracking prompt purchases."""
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='purchase_records')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchased_prompts')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sold_prompts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"{self.buyer.username} purchased {self.prompt.title}"


class PromptDownload(models.Model):
    """Model for tracking free prompt downloads."""
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='download_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloaded_prompts')
    downloaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['prompt', 'user']
        ordering = ['-downloaded_at']
    
    def __str__(self):
        return f"{self.user.username} downloaded {self.prompt.title}" 