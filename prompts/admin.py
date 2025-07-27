from django.contrib import admin
from .models import Category, Tag, Prompt, Review, PromptDownload, PromptPurchase, UserFavorite, PromptAnalytics

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'prompt_count', 'total_earnings', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['prompt_count', 'total_earnings']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'usage_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['usage_count']

@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'category', 'price_type', 'price', 'status',
        'views', 'downloads', 'purchases', 'favorites', 'average_rating',
        'total_engagement', 'conversion_rate', 'created_at'
    ]
    list_filter = [
        'status', 'price_type', 'difficulty_level', 'category', 'is_active',
        'created_at', 'published_at'
    ]
    search_fields = ['title', 'description', 'author__username', 'category__name']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'views', 'downloads', 'purchases', 'favorites', 'average_rating',
        'total_ratings', 'total_engagement', 'conversion_rate', 'total_earnings',
        'is_featured', 'is_trending'
    ]
    filter_horizontal = ['tags']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'author', 'category', 'tags')
        }),
        ('Content', {
            'fields': ('content', 'preview_content')
        }),
        ('Pricing & Status', {
            'fields': ('price_type', 'price', 'status', 'is_active')
        }),
        ('Metadata', {
            'fields': ('difficulty_level', 'estimated_tokens', 'ai_model_compatibility', 'use_cases')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'keywords')
        }),
        ('Analytics', {
            'fields': ('views', 'downloads', 'purchases', 'favorites', 'average_rating', 'total_ratings'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category').prefetch_related('tags')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'user', 'rating', 'title', 'is_verified', 'helpful_votes', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['prompt__title', 'user__username', 'title', 'comment']
    readonly_fields = ['is_verified', 'helpful_votes']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('prompt', 'user')

@admin.register(PromptDownload)
class PromptDownloadAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'user', 'ip_address', 'created_at']
    list_filter = ['created_at']
    search_fields = ['prompt__title', 'user__username', 'ip_address']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('prompt', 'user')

@admin.register(PromptPurchase)
class PromptPurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'prompt', 'user', 'amount', 'payment_status', 'transaction_id',
        'is_successful', 'created_at'
    ]
    list_filter = ['payment_status', 'created_at']
    search_fields = ['prompt__title', 'user__username', 'stripe_payment_intent_id', 'transaction_id']
    readonly_fields = ['transaction_id', 'is_successful', 'created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('prompt', 'user')

@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'prompt', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'prompt__title']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'prompt')

@admin.register(PromptAnalytics)
class PromptAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'date', 'views', 'downloads', 'purchases', 'revenue']
    list_filter = ['date', 'prompt__category']
    search_fields = ['prompt__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('prompt') 