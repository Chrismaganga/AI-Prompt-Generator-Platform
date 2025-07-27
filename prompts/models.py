from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#3B82F6")  # Hex color
    icon = models.CharField(max_length=50, default="fas fa-folder")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        return reverse('prompts:category_detail', kwargs={'slug': self.slug})

    @property
    def prompt_count(self):
        return self.prompts.filter(is_active=True).count()

    @property
    def total_earnings(self):
        return self.prompts.filter(
            is_active=True, 
            price_type='paid'
        ).aggregate(
            total=Sum('purchases__amount')
        )['total'] or 0

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('prompts:tag_detail', kwargs={'slug': self.slug})

class Prompt(models.Model):
    PRICE_TYPES = [
        ('free', 'Free'),
        ('paid', 'Paid'),
    ]

    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('moderated', 'Under Review'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    content = models.TextField(help_text="The full prompt content")
    preview_content = models.TextField(help_text="A preview of the prompt output")
    
    # Author and Category
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='prompts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='prompts')
    
    # Pricing and Status
    price_type = models.CharField(max_length=10, choices=PRICE_TYPES, default='free')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    
    # Metadata
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='intermediate')
    estimated_tokens = models.PositiveIntegerField(default=0, help_text="Estimated token count for the prompt")
    ai_model_compatibility = models.JSONField(default=list, help_text="List of compatible AI models")
    use_cases = models.JSONField(default=list, help_text="List of use cases for this prompt")
    
    # Analytics
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    purchases = models.PositiveIntegerField(default=0)
    favorites = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO and Discovery
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title (max 60 characters)")
    meta_description = models.TextField(blank=True, help_text="SEO description (max 160 characters)")
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for SEO")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-generate meta fields if not provided
        if not self.meta_title:
            self.meta_title = self.title[:60]
        if not self.meta_description:
            self.meta_description = self.description[:160]
        
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('prompts:prompt_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    def increment_downloads(self):
        self.downloads += 1
        self.save(update_fields=['downloads'])

    def increment_purchases(self):
        self.purchases += 1
        self.save(update_fields=['purchases'])

    def increment_favorites(self):
        self.favorites += 1
        self.save(update_fields=['favorites'])

    def decrement_favorites(self):
        if self.favorites > 0:
            self.favorites -= 1
            self.save(update_fields=['favorites'])

    @property
    def total_engagement(self):
        """Total engagement (views + downloads + purchases + favorites)"""
        return self.views + self.downloads + self.purchases + self.favorites

    @property
    def conversion_rate(self):
        """Conversion rate from views to purchases/downloads"""
        if self.views == 0:
            return 0
        return ((self.downloads + self.purchases) / self.views) * 100

    @property
    def average_rating(self):
        """Average rating from reviews"""
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

    @property
    def total_ratings(self):
        """Total number of reviews"""
        return self.reviews.count()

    @property
    def total_earnings(self):
        """Total earnings from this prompt"""
        if self.price_type == 'free':
            return 0
        return self.purchases * self.price

    @property
    def is_featured(self):
        """Check if prompt should be featured based on performance"""
        return (
            self.status == 'published' and
            self.is_active and
            self.total_engagement > 100 and
            self.average_rating >= 4.0
        )

    @property
    def is_trending(self):
        """Check if prompt is trending (high engagement in last 7 days)"""
        week_ago = timezone.now() - timedelta(days=7)
        recent_engagement = (
            self.promptdownload_set.filter(created_at__gte=week_ago).count() +
            self.promptpurchase_set.filter(created_at__gte=week_ago).count()
        )
        return recent_engagement >= 10

    def get_related_prompts(self, limit=6):
        """Get related prompts based on category and tags"""
        return Prompt.objects.filter(
            category=self.category,
            tags__in=self.tags.all(),
            status='published',
            is_active=True
        ).exclude(id=self.id).distinct()[:limit]

    def get_usage_statistics(self, days=30):
        """Get usage statistics for the last N days"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        downloads = self.promptdownload_set.filter(
            created_at__range=(start_date, end_date)
        ).count()
        
        purchases = self.promptpurchase_set.filter(
            created_at__range=(start_date, end_date)
        ).count()
        
        return {
            'downloads': downloads,
            'purchases': purchases,
            'total': downloads + purchases
        }

class Review(models.Model):
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    helpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['prompt', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s review of {self.prompt.title}"

    def increment_helpful_votes(self):
        self.helpful_votes += 1
        self.save(update_fields=['helpful_votes'])

    @property
    def is_verified(self):
        """Check if this is a verified purchase review"""
        return self.is_verified_purchase or self.prompt.promptpurchase_set.filter(user=self.user).exists()

class PromptDownload(models.Model):
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='promptdownload_set')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloads')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['prompt', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} downloaded {self.prompt.title}"

    def save(self, *args, **kwargs):
        # Increment prompt download count
        if not self.pk:  # Only on creation
            self.prompt.increment_downloads()
        super().save(*args, **kwargs)

class PromptPurchase(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='promptpurchase_set')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} purchased {self.prompt.title} for ${self.amount}"

    def save(self, *args, **kwargs):
        # Increment prompt purchase count when payment is completed
        if self.payment_status == 'completed' and not self.pk:
            self.prompt.increment_purchases()
        super().save(*args, **kwargs)

    @property
    def is_successful(self):
        return self.payment_status == 'completed'

    def refund(self):
        """Mark purchase as refunded"""
        self.payment_status = 'refunded'
        self.save(update_fields=['payment_status'])

class UserFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='user_favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'prompt']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} favorited {self.prompt.title}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.prompt.increment_favorites()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.prompt.decrement_favorites()
        super().delete(*args, **kwargs)

class PromptAnalytics(models.Model):
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    purchases = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['prompt', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"Analytics for {self.prompt.title} on {self.date}"

    @classmethod
    def update_daily_analytics(cls, prompt, date=None):
        """Update daily analytics for a prompt"""
        if date is None:
            date = timezone.now().date()
        
        analytics, created = cls.objects.get_or_create(
            prompt=prompt,
            date=date,
            defaults={
                'views': 0,
                'downloads': 0,
                'purchases': 0,
                'revenue': 0.00
            }
        )
        
        # Update counts for the day
        analytics.views = prompt.promptdownload_set.filter(
            created_at__date=date
        ).count()
        
        analytics.downloads = prompt.promptdownload_set.filter(
            created_at__date=date
        ).count()
        
        analytics.purchases = prompt.promptpurchase_set.filter(
            created_at__date=date,
            payment_status='completed'
        ).count()
        
        analytics.revenue = prompt.promptpurchase_set.filter(
            created_at__date=date,
            payment_status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0.00
        
        analytics.save()
        return analytics 