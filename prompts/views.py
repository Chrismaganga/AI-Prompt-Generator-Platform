from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg, Sum, F
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models.functions import Coalesce
from datetime import timedelta
import json

from .models import Prompt, Category, Tag, Review, PromptDownload, PromptPurchase, UserFavorite, PromptAnalytics
from .forms import PromptForm, ReviewForm, SearchForm
from payments.models import StripeAccount

class PromptListView(ListView):
    model = Prompt
    template_name = 'prompts/prompt_list.html'
    context_object_name = 'prompts'
    paginate_by = 12

    def get_queryset(self):
        queryset = Prompt.objects.filter(
            status='published',
            is_active=True
        ).select_related('author', 'category').prefetch_related('tags')

        # Apply search filters
        search_form = SearchForm(self.request.GET)
        if search_form.is_valid():
            q = search_form.cleaned_data.get('q')
            category = search_form.cleaned_data.get('category')
            price_type = search_form.cleaned_data.get('price_type')
            sort_by = search_form.cleaned_data.get('sort_by')

            if q:
                queryset = queryset.filter(
                    Q(title__icontains=q) |
                    Q(description__icontains=q) |
                    Q(tags__name__icontains=q) |
                    Q(category__name__icontains=q)
                ).distinct()

            if category:
                queryset = queryset.filter(category=category)

            if price_type:
                queryset = queryset.filter(price_type=price_type)

            # Apply sorting
            if sort_by == 'newest':
                queryset = queryset.order_by('-created_at')
            elif sort_by == 'oldest':
                queryset = queryset.order_by('created_at')
            elif sort_by == 'popular':
                queryset = queryset.annotate(
                    engagement_score=Coalesce(F('views') + F('downloads') + F('purchases'), 0)
                ).order_by('-engagement_score')
            elif sort_by == 'rating':
                queryset = queryset.annotate(
                    avg_rating=Coalesce(Avg('reviews__rating'), 0.0)
                ).order_by('-avg_rating')
            elif sort_by == 'price_low':
                queryset = queryset.order_by('price')
            elif sort_by == 'price_high':
                queryset = queryset.order_by('-price')
            else:
                queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add search form
        context['search_form'] = SearchForm(self.request.GET)
        
        # Add categories
        context['categories'] = Category.objects.filter(is_active=True).annotate(
            prompt_count=Count('prompts', filter=Q(prompts__status='published', prompts__is_active=True))
        ).order_by('-prompt_count')[:10]
        
        # Add featured prompts
        context['featured_prompts'] = Prompt.objects.filter(
            status='published',
            is_active=True
        ).annotate(
            avg_rating=Coalesce(Avg('reviews__rating'), 0.0),
            engagement_score=Coalesce(F('views') + F('downloads') + F('purchases'), 0)
        ).filter(
            avg_rating__gte=4.0
        ).order_by('-engagement_score')[:6]
        
        # Add trending prompts
        week_ago = timezone.now() - timedelta(days=7)
        context['trending_prompts'] = Prompt.objects.filter(
            status='published',
            is_active=True,
            promptdownload_set__created_at__gte=week_ago
        ).annotate(
            recent_downloads=Count('promptdownload_set', filter=Q(promptdownload_set__created_at__gte=week_ago))
        ).filter(recent_downloads__gte=5).order_by('-recent_downloads')[:6]
        
        # Add popular tags
        context['popular_tags'] = Tag.objects.annotate(
            prompt_count=Count('prompts', filter=Q(prompts__status='published', prompts__is_active=True))
        ).filter(prompt_count__gt=0).order_by('-prompt_count')[:20]
        
        return context

class PromptDetailView(DetailView):
    model = Prompt
    template_name = 'prompts/prompt_detail.html'
    context_object_name = 'prompt'

    def get_queryset(self):
        return Prompt.objects.filter(
            status='published',
            is_active=True
        ).select_related('author', 'category').prefetch_related('tags', 'reviews__user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prompt = self.get_object()
        
        # Increment view count
        prompt.increment_views()
        
        # Add reviews
        context['reviews'] = prompt.reviews.select_related('user').order_by('-created_at')[:10]
        
        # Add user review if exists
        if self.request.user.is_authenticated:
            context['user_review'] = prompt.reviews.filter(user=self.request.user).first()
            context['has_downloaded'] = prompt.promptdownload_set.filter(user=self.request.user).exists()
            context['has_purchased'] = prompt.promptpurchase_set.filter(
                user=self.request.user,
                payment_status='completed'
            ).exists()
            context['is_favorited'] = prompt.user_favorites.filter(user=self.request.user).exists()
        
        # Add related prompts
        context['related_prompts'] = prompt.get_related_prompts()
        
        # Add usage statistics
        context['usage_stats'] = prompt.get_usage_statistics(days=30)
        
        # Add analytics data
        context['analytics'] = prompt.analytics.order_by('-date')[:7]
        
        return context

class PromptCreateView(LoginRequiredMixin, CreateView):
    model = Prompt
    form_class = PromptForm
    template_name = 'prompts/prompt_form.html'
    success_url = reverse_lazy('prompts:prompt_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Prompt created successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        return context

class PromptUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Prompt
    form_class = PromptForm
    template_name = 'prompts/prompt_form.html'
    success_url = reverse_lazy('prompts:prompt_list')

    def test_func(self):
        prompt = self.get_object()
        return self.request.user == prompt.author

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Prompt updated successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

class PromptDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Prompt
    template_name = 'prompts/prompt_confirm_delete.html'
    success_url = reverse_lazy('prompts:prompt_list')

    def test_func(self):
        prompt = self.get_object()
        return self.request.user == prompt.author

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Prompt deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
def download_prompt(request, slug):
    prompt = get_object_or_404(Prompt, slug=slug, status='published', is_active=True)
    
    if prompt.price_type == 'paid':
        messages.error(request, 'This prompt requires purchase.')
        return redirect('prompts:prompt_detail', slug=slug)
    
    # Check if already downloaded
    if prompt.promptdownload_set.filter(user=request.user).exists():
        messages.info(request, 'You have already downloaded this prompt.')
        return redirect('prompts:prompt_detail', slug=slug)
    
    # Create download record
    PromptDownload.objects.create(
        prompt=prompt,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    messages.success(request, 'Prompt downloaded successfully!')
    return redirect('prompts:prompt_detail', slug=slug)

@login_required
def purchase_prompt(request, slug):
    prompt = get_object_or_404(Prompt, slug=slug, status='published', is_active=True)
    
    if prompt.price_type == 'free':
        messages.error(request, 'This prompt is free. Use download instead.')
        return redirect('prompts:prompt_detail', slug=slug)
    
    # Check if already purchased
    if prompt.promptpurchase_set.filter(
        user=request.user,
        payment_status='completed'
    ).exists():
        messages.info(request, 'You have already purchased this prompt.')
        return redirect('prompts:prompt_detail', slug=slug)
    
    # Redirect to checkout
    return redirect('payments:checkout', slug=slug)

@login_required
def add_review(request, slug):
    prompt = get_object_or_404(Prompt, slug=slug, status='published', is_active=True)
    
    # Check if user has already reviewed
    if prompt.reviews.filter(user=request.user).exists():
        messages.error(request, 'You have already reviewed this prompt.')
        return redirect('prompts:prompt_detail', slug=slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.prompt = prompt
            review.user = request.user
            review.is_verified_purchase = prompt.promptpurchase_set.filter(
                user=request.user,
                payment_status='completed'
            ).exists()
            review.save()
            messages.success(request, 'Review added successfully!')
            return redirect('prompts:prompt_detail', slug=slug)
    else:
        form = ReviewForm()
    
    return render(request, 'prompts/review_form.html', {
        'form': form,
        'prompt': prompt
    })

@login_required
@require_POST
def toggle_favorite(request, slug):
    prompt = get_object_or_404(Prompt, slug=slug, status='published', is_active=True)
    
    favorite, created = UserFavorite.objects.get_or_create(
        user=request.user,
        prompt=prompt
    )
    
    if not created:
        favorite.delete()
        action = 'removed from'
    else:
        action = 'added to'
    
    return JsonResponse({
        'success': True,
        'action': action,
        'favorites_count': prompt.favorites
    })

@login_required
def user_dashboard(request):
    user = request.user
    
    # User's prompts
    user_prompts = Prompt.objects.filter(author=user).order_by('-created_at')
    
    # User's downloads
    user_downloads = PromptDownload.objects.filter(user=user).select_related('prompt').order_by('-created_at')
    
    # User's purchases
    user_purchases = PromptPurchase.objects.filter(
        user=user,
        payment_status='completed'
    ).select_related('prompt').order_by('-created_at')
    
    # User's favorites
    user_favorites = UserFavorite.objects.filter(user=user).select_related('prompt').order_by('-created_at')
    
    # Analytics
    total_earnings = user_prompts.filter(
        price_type='paid',
        promptpurchase_set__payment_status='completed'
    ).aggregate(
        total=Sum('promptpurchase_set__amount')
    )['total'] or 0
    
    total_downloads = user_prompts.aggregate(
        total=Sum('downloads')
    )['total'] or 0
    
    total_purchases = user_prompts.aggregate(
        total=Sum('purchases')
    )['total'] or 0
    
    # Monthly earnings
    current_month = timezone.now().month
    monthly_earnings = user_prompts.filter(
        price_type='paid',
        promptpurchase_set__payment_status='completed',
        promptpurchase_set__created_at__month=current_month
    ).aggregate(
        total=Sum('promptpurchase_set__amount')
    )['total'] or 0
    
    context = {
        'user_prompts': user_prompts,
        'user_downloads': user_downloads,
        'user_purchases': user_purchases,
        'user_favorites': user_favorites,
        'total_earnings': total_earnings,
        'total_downloads': total_downloads,
        'total_purchases': total_purchases,
        'monthly_earnings': monthly_earnings,
    }
    
    return render(request, 'prompts/user_dashboard.html', context)

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    prompts = Prompt.objects.filter(
        category=category,
        status='published',
        is_active=True
    ).select_related('author').prefetch_related('tags').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(prompts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'prompts': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'prompts/category_detail.html', context)

def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    prompts = Prompt.objects.filter(
        tags=tag,
        status='published',
        is_active=True
    ).select_related('author', 'category').prefetch_related('tags').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(prompts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'prompts': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'prompts/tag_detail.html', context)

def search_prompts(request):
    """Search prompts with filters and sorting."""
    form = SearchForm(request.GET)
    prompts = Prompt.objects.none()
    page_obj = None
    
    if form.is_valid():
        query = form.cleaned_data.get('q', '')
        category = form.cleaned_data.get('category')
        price_type = form.cleaned_data.get('price_type')
        sort_by = form.cleaned_data.get('sort_by', 'newest')
        
        # Start with published and active prompts
        prompts = Prompt.objects.filter(
            status='published',
            is_active=True
        )
        
        # Apply search query
        if query:
            prompts = prompts.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        # Apply category filter
        if category:
            prompts = prompts.filter(category=category)
        
        # Apply price type filter
        if price_type:
            prompts = prompts.filter(price_type=price_type)
        
        # Apply sorting
        if sort_by == 'newest':
            prompts = prompts.order_by('-created_at')
        elif sort_by == 'oldest':
            prompts = prompts.order_by('created_at')
        elif sort_by == 'popular':
            prompts = prompts.annotate(
                engagement_score=Coalesce(F('views') + F('downloads') + F('purchases'), 0)
            ).order_by('-engagement_score')
        elif sort_by == 'rating':
            prompts = prompts.annotate(
                avg_rating=Coalesce(Avg('reviews__rating'), 0.0)
            ).order_by('-avg_rating')
        elif sort_by == 'price_low':
            prompts = prompts.order_by('price')
        elif sort_by == 'price_high':
            prompts = prompts.order_by('-price')
        
        # Paginate results
        paginator = Paginator(prompts, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'prompts': page_obj if page_obj else prompts,
        'page_obj': page_obj,
        'query': request.GET.get('q', ''),
    }
    
    return render(request, 'prompts/search_results.html', context)

@login_required
def analytics_dashboard(request):
    user = request.user
    
    # Get user's prompts
    user_prompts = Prompt.objects.filter(author=user)
    
    # Overall statistics
    total_prompts = user_prompts.count()
    published_prompts = user_prompts.filter(status='published').count()
    total_earnings = user_prompts.filter(
        price_type='paid',
        promptpurchase_set__payment_status='completed'
    ).aggregate(
        total=Sum('promptpurchase_set__amount')
    )['total'] or 0
    
    # Monthly statistics
    current_month = timezone.now().month
    monthly_earnings = user_prompts.filter(
        price_type='paid',
        promptpurchase_set__payment_status='completed',
        promptpurchase_set__created_at__month=current_month
    ).aggregate(
        total=Sum('promptpurchase_set__amount')
    )['total'] or 0
    
    # Top performing prompts
    top_prompts = user_prompts.filter(
        promptpurchase_set__payment_status='completed'
    ).annotate(
        total_revenue=Sum('promptpurchase_set__amount')
    ).order_by('-total_revenue')[:5]
    
    # Recent activity
    recent_downloads = PromptDownload.objects.filter(
        prompt__author=user
    ).select_related('prompt', 'user').order_by('-created_at')[:10]
    
    recent_purchases = PromptPurchase.objects.filter(
        prompt__author=user,
        payment_status='completed'
    ).select_related('prompt', 'user').order_by('-created_at')[:10]
    
    # Chart data (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    daily_stats = []
    for i in range(30):
        date = start_date + timedelta(days=i)
        downloads = PromptDownload.objects.filter(
            prompt__author=user,
            created_at__date=date
        ).count()
        purchases = PromptPurchase.objects.filter(
            prompt__author=user,
            payment_status='completed',
            created_at__date=date
        ).count()
        revenue = PromptPurchase.objects.filter(
            prompt__author=user,
            payment_status='completed',
            created_at__date=date
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'downloads': downloads,
            'purchases': purchases,
            'revenue': float(revenue)
        })
    
    context = {
        'total_prompts': total_prompts,
        'published_prompts': published_prompts,
        'total_earnings': total_earnings,
        'monthly_earnings': monthly_earnings,
        'top_prompts': top_prompts,
        'recent_downloads': recent_downloads,
        'recent_purchases': recent_purchases,
        'daily_stats': daily_stats,
    }
    
    return render(request, 'prompts/analytics_dashboard.html', context)

@csrf_exempt
def api_search(request):
    """API endpoint for AJAX search."""
    if request.method == 'GET':
        query = request.GET.get('q', '')
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        prompts = Prompt.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query),
            status='published',
            is_active=True
        ).distinct()[:10]
        
        results = []
        for prompt in prompts:
            results.append({
                'id': prompt.id,
                'title': prompt.title,
                'description': prompt.description[:100] + '...' if len(prompt.description) > 100 else prompt.description,
                'url': reverse('prompts:prompt_detail', kwargs={'slug': prompt.slug}),
                'price_type': prompt.price_type,
                'price': str(prompt.price),
                'category': prompt.category.name if prompt.category else '',
                'views': prompt.views,
                'downloads': prompt.downloads,
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def export_prompts(request):
    """Export user's prompts as JSON"""
    user = request.user
    prompts = Prompt.objects.filter(author=user)
    
    data = []
    for prompt in prompts:
        data.append({
            'title': prompt.title,
            'description': prompt.description,
            'content': prompt.content,
            'category': prompt.category.name,
            'price_type': prompt.price_type,
            'price': float(prompt.price),
            'status': prompt.status,
            'created_at': prompt.created_at.isoformat(),
            'views': prompt.views,
            'downloads': prompt.downloads,
            'purchases': prompt.purchases,
            'earnings': float(prompt.total_earnings),
        })
    
    response = JsonResponse(data, safe=False)
    response['Content-Disposition'] = f'attachment; filename="my_prompts_{timezone.now().strftime("%Y%m%d")}.json"'
    return response 