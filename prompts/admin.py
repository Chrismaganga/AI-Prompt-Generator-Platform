from django.contrib import admin
from .models import Category, Prompt, PromptImage, PromptReview, PromptPurchase, PromptDownload


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']


class PromptImageInline(admin.TabularInline):
    model = PromptImage
    extra = 1


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'price_type', 'price', 'status', 'views', 'downloads', 'purchases', 'created_at']
    list_filter = ['status', 'price_type', 'category', 'is_featured', 'created_at']
    search_fields = ['title', 'description', 'author__username', 'author__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views', 'downloads', 'purchases', 'created_at', 'updated_at', 'published_at']
    inlines = [PromptImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'content', 'preview_content')
        }),
        ('Pricing', {
            'fields': ('price_type', 'price')
        }),
        ('Metadata', {
            'fields': ('category', 'tags', 'author')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('views', 'downloads', 'purchases'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PromptImage)
class PromptImageAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'caption', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['prompt__title', 'caption']


@admin.register(PromptReview)
class PromptReviewAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['prompt__title', 'user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PromptPurchase)
class PromptPurchaseAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'buyer', 'seller', 'amount', 'purchased_at']
    list_filter = ['purchased_at']
    search_fields = ['prompt__title', 'buyer__username', 'seller__username']
    readonly_fields = ['purchased_at']


@admin.register(PromptDownload)
class PromptDownloadAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'user', 'downloaded_at']
    list_filter = ['downloaded_at']
    search_fields = ['prompt__title', 'user__username']
    readonly_fields = ['downloaded_at'] 