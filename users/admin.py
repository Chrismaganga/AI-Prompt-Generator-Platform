from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_creator', 'is_staff', 'is_active']
    list_filter = ['is_creator', 'is_staff', 'is_active', 'date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {'fields': ('bio', 'avatar', 'website', 'location', 'is_creator')}),
        ('Stripe Info', {'fields': ('stripe_customer_id', 'stripe_account_id')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile Info', {'fields': ('bio', 'avatar', 'website', 'location', 'is_creator')}),
    )
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined'] 