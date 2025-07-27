from django.urls import path
from . import views

app_name = 'prompts'

urlpatterns = [
    # Main views
    path('', views.PromptListView.as_view(), name='prompt_list'),
    path('create/', views.PromptCreateView.as_view(), name='prompt_create'),
    
    # Search - must come before slug patterns
    path('search/', views.search_prompts, name='search_prompts'),
    path('api/search/', views.api_search, name='api_search'),
    
    # User dashboard and analytics
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('export/', views.export_prompts, name='export_prompts'),
    
    # Browse by category and tags
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    
    # Prompt detail and actions - must come after specific patterns
    path('<slug:slug>/', views.PromptDetailView.as_view(), name='prompt_detail'),
    path('<slug:slug>/edit/', views.PromptUpdateView.as_view(), name='prompt_update'),
    path('<slug:slug>/delete/', views.PromptDeleteView.as_view(), name='prompt_delete'),
    
    # User actions
    path('<slug:slug>/download/', views.download_prompt, name='download_prompt'),
    path('<slug:slug>/purchase/', views.purchase_prompt, name='purchase_prompt'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),
    path('<slug:slug>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
] 