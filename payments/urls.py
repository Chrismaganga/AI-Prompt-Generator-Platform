from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create/<int:prompt_id>/', views.create_payment, name='create_payment'),
    path('success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('cancel/<int:payment_id>/', views.payment_cancel, name='payment_cancel'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('history/', views.payment_history, name='payment_history'),
    path('connect/', views.connect_stripe_account, name='connect_stripe_account'),
    path('connect/return/', views.connect_stripe_return, name='connect_stripe_return'),
] 