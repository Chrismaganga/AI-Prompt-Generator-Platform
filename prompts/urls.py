from django.urls import path
from . import views

app_name = 'prompts'

urlpatterns = [
    # Main views
    path('', views.PromptListView.as_view(), name='prompt_list'),
    path('search/', views.search_prompts, name='search_prompts'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    
    # Prompt CRUD
    path('create/', views.PromptCreateView.as_view(), name='prompt_create'),
    path('<slug:slug>/', views.PromptDetailView.as_view(), name='prompt_detail'),
    path('<slug:slug>/edit/', views.PromptUpdateView.as_view(), name='prompt_update'),
    path('<slug:slug>/delete/', views.PromptDeleteView.as_view(), name='prompt_delete'),
    
    # Category views
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # User actions
    path('<slug:slug>/review/', views.add_review, name='add_review'),
    path('<slug:slug>/download/', views.download_prompt, name='download_prompt'),
    path('<slug:slug>/purchase/', views.purchase_prompt, name='purchase_prompt'),
] 