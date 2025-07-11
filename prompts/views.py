from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import Prompt, Category, PromptReview, PromptPurchase, PromptDownload
from .forms import PromptForm, PromptReviewForm, PromptSearchForm


class PromptListView(ListView):
    """View for listing all prompts with search and filtering."""
    model = Prompt
    template_name = 'prompts/prompt_list.html'
    context_object_name = 'prompts'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Prompt.objects.filter(status='published').select_related('author', 'category')
        
        # Search functionality
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__name__icontains=q) |
                Q(author__username__icontains=q)
            ).distinct()
        
        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Price type filter
        price_type = self.request.GET.get('price_type')
        if price_type:
            queryset = queryset.filter(price_type=price_type)
        
        # Sorting
        sort_by = self.request.GET.get('sort_by', 'newest')
        if sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-views', '-downloads', '-purchases')
        elif sort_by == 'rating':
            queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
        elif sort_by == 'price_low':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_form'] = PromptSearchForm(self.request.GET)
        context['featured_prompts'] = Prompt.objects.filter(
            status='published', is_featured=True
        ).select_related('author', 'category')[:6]
        return context


class PromptDetailView(DetailView):
    """View for displaying prompt details."""
    model = Prompt
    template_name = 'prompts/prompt_detail.html'
    context_object_name = 'prompt'
    
    def get_queryset(self):
        return Prompt.objects.filter(status='published').select_related('author', 'category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prompt = self.get_object()
        
        # Increment view count
        prompt.views += 1
        prompt.save(update_fields=['views'])
        
        # Check if user has purchased/downloaded this prompt
        if self.request.user.is_authenticated:
            context['has_purchased'] = PromptPurchase.objects.filter(
                prompt=prompt, buyer=self.request.user
            ).exists()
            context['has_downloaded'] = PromptDownload.objects.filter(
                prompt=prompt, user=self.request.user
            ).exists()
            context['user_review'] = PromptReview.objects.filter(
                prompt=prompt, user=self.request.user
            ).first()
        
        # Get reviews
        context['reviews'] = PromptReview.objects.filter(prompt=prompt).select_related('user')[:5]
        context['review_form'] = PromptReviewForm()
        
        # Related prompts
        context['related_prompts'] = Prompt.objects.filter(
            category=prompt.category,
            status='published'
        ).exclude(id=prompt.id)[:4]
        
        return context


class PromptCreateView(LoginRequiredMixin, CreateView):
    """View for creating new prompts."""
    model = Prompt
    form_class = PromptForm
    template_name = 'prompts/prompt_form.html'
    success_url = reverse_lazy('prompt_list')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Prompt created successfully! It will be reviewed before publication.')
        return super().form_valid(form)


class PromptUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for editing prompts."""
    model = Prompt
    form_class = PromptForm
    template_name = 'prompts/prompt_form.html'
    
    def test_func(self):
        prompt = self.get_object()
        return prompt.author == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Prompt updated successfully!')
        return super().form_valid(form)


class PromptDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for deleting prompts."""
    model = Prompt
    template_name = 'prompts/prompt_confirm_delete.html'
    success_url = reverse_lazy('prompt_list')
    
    def test_func(self):
        prompt = self.get_object()
        return prompt.author == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Prompt deleted successfully!')
        return super().delete(request, *args, **kwargs)


class CategoryDetailView(DetailView):
    """View for displaying prompts by category."""
    model = Category
    template_name = 'prompts/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        # Get prompts in this category
        prompts = Prompt.objects.filter(
            category=category,
            status='published'
        ).select_related('author').order_by('-created_at')
        
        # Pagination
        paginator = Paginator(prompts, 12)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['prompts'] = page_obj
        return context


@login_required
def add_review(request, slug):
    """View for adding a review to a prompt."""
    prompt = get_object_or_404(Prompt, slug=slug, status='published')
    
    if request.method == 'POST':
        form = PromptReviewForm(request.POST)
        if form.is_valid():
            review, created = PromptReview.objects.get_or_create(
                prompt=prompt,
                user=request.user,
                defaults=form.cleaned_data
            )
            if not created:
                review.rating = form.cleaned_data['rating']
                review.comment = form.cleaned_data['comment']
                review.save()
            
            messages.success(request, 'Review submitted successfully!')
            return redirect('prompt_detail', slug=slug)
    else:
        form = PromptReviewForm()
    
    return render(request, 'prompts/add_review.html', {
        'form': form,
        'prompt': prompt
    })


@login_required
def download_prompt(request, slug):
    """View for downloading free prompts."""
    prompt = get_object_or_404(Prompt, slug=slug, status='published')
    
    if prompt.price_type != 'free':
        messages.error(request, 'This prompt is not free.')
        return redirect('prompt_detail', slug=slug)
    
    # Check if user already downloaded
    if PromptDownload.objects.filter(prompt=prompt, user=request.user).exists():
        messages.info(request, 'You have already downloaded this prompt.')
        return redirect('prompt_detail', slug=slug)
    
    # Create download record
    PromptDownload.objects.create(prompt=prompt, user=request.user)
    prompt.downloads += 1
    prompt.save(update_fields=['downloads'])
    
    messages.success(request, 'Prompt downloaded successfully!')
    return redirect('prompt_detail', slug=slug)


@login_required
def purchase_prompt(request, slug):
    """View for purchasing paid prompts."""
    prompt = get_object_or_404(Prompt, slug=slug, status='published')
    
    if prompt.price_type != 'paid':
        messages.error(request, 'This prompt is not for sale.')
        return redirect('prompt_detail', slug=slug)
    
    # Check if user already purchased
    if PromptPurchase.objects.filter(prompt=prompt, buyer=request.user).exists():
        messages.info(request, 'You have already purchased this prompt.')
        return redirect('prompt_detail', slug=slug)
    
    # Check if user is trying to buy their own prompt
    if prompt.author == request.user:
        messages.error(request, 'You cannot purchase your own prompt.')
        return redirect('prompt_detail', slug=slug)
    
    # Redirect to payment view
    return redirect('payment_create', prompt_id=prompt.id)


def search_prompts(request):
    """View for searching prompts."""
    form = PromptSearchForm(request.GET)
    prompts = Prompt.objects.filter(status='published').select_related('author', 'category')
    
    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        price_type = form.cleaned_data.get('price_type')
        sort_by = form.cleaned_data.get('sort_by', 'newest')
        
        if q:
            prompts = prompts.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__name__icontains=q) |
                Q(author__username__icontains=q)
            ).distinct()
        
        if category:
            prompts = prompts.filter(category=category)
        
        if price_type:
            prompts = prompts.filter(price_type=price_type)
        
        # Apply sorting
        if sort_by == 'newest':
            prompts = prompts.order_by('-created_at')
        elif sort_by == 'oldest':
            prompts = prompts.order_by('created_at')
        elif sort_by == 'popular':
            prompts = prompts.order_by('-views', '-downloads', '-purchases')
        elif sort_by == 'rating':
            prompts = prompts.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
        elif sort_by == 'price_low':
            prompts = prompts.order_by('price')
        elif sort_by == 'price_high':
            prompts = prompts.order_by('-price')
    
    # Pagination
    paginator = Paginator(prompts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'prompts/search_results.html', {
        'form': form,
        'prompts': page_obj,
        'categories': Category.objects.all(),
    })


@login_required
def user_dashboard(request):
    """View for user dashboard showing their prompts and purchases."""
    user_prompts = Prompt.objects.filter(author=request.user).order_by('-created_at')
    user_purchases = PromptPurchase.objects.filter(buyer=request.user).select_related('prompt', 'seller').order_by('-purchased_at')
    user_downloads = PromptDownload.objects.filter(user=request.user).select_related('prompt', 'author').order_by('-downloaded_at')
    
    return render(request, 'prompts/user_dashboard.html', {
        'user_prompts': user_prompts,
        'user_purchases': user_purchases,
        'user_downloads': user_downloads,
    }) 