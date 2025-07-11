import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

from .models import Payment, StripeAccount
from prompts.models import Prompt, PromptPurchase

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_payment(request, prompt_id):
    """Create a payment intent for purchasing a prompt."""
    prompt = get_object_or_404(Prompt, id=prompt_id, status='published')
    
    # Check if user already purchased
    if PromptPurchase.objects.filter(prompt=prompt, buyer=request.user).exists():
        messages.info(request, 'You have already purchased this prompt.')
        return redirect('prompts:prompt_detail', slug=prompt.slug)
    
    # Check if user is trying to buy their own prompt
    if prompt.author == request.user:
        messages.error(request, 'You cannot purchase your own prompt.')
        return redirect('prompts:prompt_detail', slug=prompt.slug)
    
    try:
        # Create or get Stripe customer
        if not request.user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=request.user.full_name,
            )
            request.user.stripe_customer_id = customer.id
            request.user.save()
        
        # Create payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(prompt.price * 100),  # Convert to cents
            currency='usd',
            customer=request.user.stripe_customer_id,
            metadata={
                'prompt_id': prompt.id,
                'user_id': request.user.id,
                'prompt_title': prompt.title,
            }
        )
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            prompt=prompt,
            amount=prompt.price,
            stripe_payment_intent_id=payment_intent.id,
            stripe_customer_id=request.user.stripe_customer_id,
        )
        
        return render(request, 'payments/checkout.html', {
            'prompt': prompt,
            'payment': payment,
            'client_secret': payment_intent.client_secret,
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        })
        
    except stripe.error.StripeError as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('prompts:prompt_detail', slug=prompt.slug)


@login_required
def payment_success(request, payment_id):
    """Handle successful payment."""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status == 'completed':
        messages.success(request, 'Payment completed successfully!')
        return redirect('prompts:prompt_detail', slug=payment.prompt.slug)
    
    # Update payment status
    payment.status = 'completed'
    payment.completed_at = timezone.now()
    payment.save()
    
    # Create purchase record
    PromptPurchase.objects.create(
        prompt=payment.prompt,
        buyer=request.user,
        seller=payment.prompt.author,
        amount=payment.amount,
        stripe_payment_intent_id=payment.stripe_payment_intent_id,
    )
    
    # Update prompt purchase count
    payment.prompt.purchases += 1
    payment.prompt.save(update_fields=['purchases'])
    
    messages.success(request, 'Payment completed successfully! You can now access the prompt.')
    return redirect('prompts:prompt_detail', slug=payment.prompt.slug)


@login_required
def payment_cancel(request, payment_id):
    """Handle cancelled payment."""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status == 'pending':
        payment.status = 'cancelled'
        payment.save()
    
    messages.info(request, 'Payment was cancelled.')
    return redirect('prompts:prompt_detail', slug=payment.prompt.slug)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_payment_success(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_failure(payment_intent)
    
    return HttpResponse(status=200)


def handle_payment_success(payment_intent):
    """Handle successful payment from webhook."""
    try:
        payment = Payment.objects.get(
            stripe_payment_intent_id=payment_intent.id
        )
        
        if payment.status != 'completed':
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.save()
            
            # Create purchase record if it doesn't exist
            if not PromptPurchase.objects.filter(
                prompt=payment.prompt,
                buyer=payment.user,
                stripe_payment_intent_id=payment.stripe_payment_intent_id
            ).exists():
                PromptPurchase.objects.create(
                    prompt=payment.prompt,
                    buyer=payment.user,
                    seller=payment.prompt.author,
                    amount=payment.amount,
                    stripe_payment_intent_id=payment.stripe_payment_intent_id,
                )
                
                # Update prompt purchase count
                payment.prompt.purchases += 1
                payment.prompt.save(update_fields=['purchases'])
    
    except Payment.DoesNotExist:
        pass


def handle_payment_failure(payment_intent):
    """Handle failed payment from webhook."""
    try:
        payment = Payment.objects.get(
            stripe_payment_intent_id=payment_intent.id
        )
        payment.status = 'failed'
        payment.save()
    except Payment.DoesNotExist:
        pass


@login_required
def payment_history(request):
    """Display user's payment history."""
    payments = Payment.objects.filter(user=request.user).select_related('prompt').order_by('-created_at')
    
    return render(request, 'payments/payment_history.html', {
        'payments': payments,
    })


@login_required
def connect_stripe_account(request):
    """Initiate Stripe Connect onboarding for creators."""
    if not request.user.is_creator:
        messages.error(request, 'You must be a creator to connect a Stripe account.')
        return redirect('prompts:user_dashboard')
    
    try:
        # Create account link for onboarding
        account_link = stripe.AccountLink.create(
            account=request.user.stripe_account_id,
            refresh_url=request.build_absolute_uri(reverse('payments:connect_stripe_account')),
            return_url=request.build_absolute_uri(reverse('payments:connect_stripe_return')),
            type='account_onboarding',
        )
        
        return redirect(account_link.url)
        
    except stripe.error.StripeError as e:
        messages.error(request, f'Error connecting Stripe account: {str(e)}')
        return redirect('prompts:user_dashboard')


@login_required
def connect_stripe_return(request):
    """Handle return from Stripe Connect onboarding."""
    messages.success(request, 'Stripe account connected successfully!')
    return redirect('prompts:user_dashboard') 