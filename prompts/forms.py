from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.db.models import Q
import re

from .models import Prompt, Category, Tag, Review

User = get_user_model()

class PromptForm(forms.ModelForm):
    """Enhanced form for creating and editing prompts."""
    
    # Custom fields for better UX
    tags_input = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas (e.g., writing, marketing, AI)',
            'data-role': 'tagsinput'
        }),
        help_text="Enter tags separated by commas"
    )
    
    ai_models = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., GPT-4, Claude, Gemini, Llama'
        }),
        help_text="Compatible AI models (comma-separated)"
    )
    
    use_cases_input = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'e.g., Content writing, Email marketing, Code generation'
        }),
        help_text="Use cases for this prompt (one per line)"
    )
    
    keywords_input = forms.CharField(
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'SEO keywords separated by commas'
        }),
        help_text="Keywords for better discoverability"
    )

    class Meta:
        model = Prompt
        fields = [
            'title', 'description', 'content', 'preview_content',
            'category', 'price_type', 'price', 'difficulty_level',
            'estimated_tokens', 'meta_title', 'meta_description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a descriptive title for your prompt'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what this prompt does and its benefits'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Write your complete AI prompt here...'
            }),
            'preview_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Show users what your prompt can generate'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'price_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'estimated_tokens': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Estimated token count'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '60',
                'placeholder': 'SEO title (max 60 characters)'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': '160',
                'placeholder': 'SEO description (max 160 characters)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values for custom fields
        if self.instance.pk:
            # Tags
            if self.instance.tags.exists():
                self.fields['tags_input'].initial = ', '.join(
                    self.instance.tags.values_list('name', flat=True)
                )
            
            # AI models
            if self.instance.ai_model_compatibility:
                self.fields['ai_models'].initial = ', '.join(self.instance.ai_model_compatibility)
            
            # Use cases
            if self.instance.use_cases:
                self.fields['use_cases_input'].initial = '\n'.join(self.instance.use_cases)
            
            # Keywords
            if self.instance.keywords:
                self.fields['keywords_input'].initial = self.instance.keywords

    def clean_title(self):
        """Validate title and ensure uniqueness."""
        title = self.cleaned_data['title']
        
        # Check for minimum length
        if len(title) < 10:
            raise forms.ValidationError("Title must be at least 10 characters long.")
        
        # Check for maximum length
        if len(title) > 200:
            raise forms.ValidationError("Title must be no more than 200 characters.")
        
        # Check for inappropriate content
        inappropriate_words = ['spam', 'scam', 'fake', 'test']
        if any(word in title.lower() for word in inappropriate_words):
            raise forms.ValidationError("Title contains inappropriate content.")
        
        # Check for uniqueness (excluding current instance)
        slug = slugify(title)
        existing_prompt = Prompt.objects.filter(slug=slug)
        if self.instance.pk:
            existing_prompt = existing_prompt.exclude(pk=self.instance.pk)
        
        if existing_prompt.exists():
            raise forms.ValidationError("A prompt with this title already exists.")
        
        return title

    def clean_description(self):
        """Validate description."""
        description = self.cleaned_data['description']
        
        if len(description) < 50:
            raise forms.ValidationError("Description must be at least 50 characters long.")
        
        if len(description) > 1000:
            raise forms.ValidationError("Description must be no more than 1000 characters.")
        
        return description

    def clean_content(self):
        """Validate prompt content."""
        content = self.cleaned_data['content']
        
        if len(content) < 20:
            raise forms.ValidationError("Prompt content must be at least 20 characters long.")
        
        if len(content) > 10000:
            raise forms.ValidationError("Prompt content must be no more than 10,000 characters.")
        
        # Check for common prompt patterns
        if not any(keyword in content.lower() for keyword in ['you are', 'act as', 'role', 'task', 'generate', 'create']):
            raise forms.ValidationError("Prompt content should include clear instructions or role definitions.")
        
        return content

    def clean_price(self):
        """Validate price based on price type."""
        price = self.cleaned_data['price']
        price_type = self.cleaned_data.get('price_type')
        
        if price_type == 'paid':
            if price <= 0:
                raise forms.ValidationError("Paid prompts must have a price greater than 0.")
            if price > 1000:
                raise forms.ValidationError("Price cannot exceed $1,000.")
        else:
            if price != 0:
                raise forms.ValidationError("Free prompts must have a price of 0.")
        
        return price

    def clean_meta_title(self):
        """Validate meta title length."""
        meta_title = self.cleaned_data['meta_title']
        if meta_title and len(meta_title) > 60:
            raise forms.ValidationError("Meta title must be no more than 60 characters.")
        return meta_title

    def clean_meta_description(self):
        """Validate meta description length."""
        meta_description = self.cleaned_data['meta_description']
        if meta_description and len(meta_description) > 160:
            raise forms.ValidationError("Meta description must be no more than 160 characters.")
        return meta_description

    def clean_tags_input(self):
        """Process and validate tags input."""
        tags_input = self.cleaned_data['tags_input']
        if not tags_input:
            return []
        
        # Split by comma and clean
        tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        
        # Validate each tag
        cleaned_tags = []
        for tag_name in tag_names:
            if len(tag_name) < 2:
                raise forms.ValidationError(f"Tag '{tag_name}' is too short (minimum 2 characters).")
            if len(tag_name) > 30:
                raise forms.ValidationError(f"Tag '{tag_name}' is too long (maximum 30 characters).")
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', tag_name):
                raise forms.ValidationError(f"Tag '{tag_name}' contains invalid characters.")
            cleaned_tags.append(tag_name)
        
        # Limit number of tags
        if len(cleaned_tags) > 10:
            raise forms.ValidationError("You can add a maximum of 10 tags.")
        
        return cleaned_tags

    def clean_ai_models(self):
        """Process AI models input."""
        ai_models = self.cleaned_data['ai_models']
        if not ai_models:
            return []
        
        models = [model.strip() for model in ai_models.split(',') if model.strip()]
        return models[:10]  # Limit to 10 models

    def clean_use_cases_input(self):
        """Process use cases input."""
        use_cases_input = self.cleaned_data['use_cases_input']
        if not use_cases_input:
            return []
        
        use_cases = [case.strip() for case in use_cases_input.split('\n') if case.strip()]
        return use_cases[:10]  # Limit to 10 use cases

    def save(self, commit=True):
        """Save the prompt with processed custom fields."""
        prompt = super().save(commit=False)
        
        # Process tags
        tag_names = self.cleaned_data.get('tags_input', [])
        if commit:
            prompt.save()
            
            # Clear existing tags and add new ones
            prompt.tags.clear()
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': slugify(tag_name)}
                )
                prompt.tags.add(tag)
        
        # Process other custom fields
        prompt.ai_model_compatibility = self.cleaned_data.get('ai_models', [])
        prompt.use_cases = self.cleaned_data.get('use_cases_input', [])
        prompt.keywords = self.cleaned_data.get('keywords_input', '')
        
        if commit:
            prompt.save()
        
        return prompt

class ReviewForm(forms.ModelForm):
    """Form for adding reviews to prompts."""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-control'}
            ),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of your experience',
                'maxlength': '200'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your detailed experience with this prompt...',
                'maxlength': '1000'
            }),
        }

    def clean_title(self):
        """Validate review title."""
        title = self.cleaned_data['title']
        
        if len(title) < 5:
            raise forms.ValidationError("Review title must be at least 5 characters long.")
        
        if len(title) > 200:
            raise forms.ValidationError("Review title must be no more than 200 characters.")
        
        return title

    def clean_comment(self):
        """Validate review comment."""
        comment = self.cleaned_data['comment']
        
        if len(comment) < 10:
            raise forms.ValidationError("Review comment must be at least 10 characters long.")
        
        if len(comment) > 1000:
            raise forms.ValidationError("Review comment must be no more than 1000 characters.")
        
        # Check for inappropriate content
        inappropriate_words = ['spam', 'scam', 'fake', 'test', 'advertisement']
        if any(word in comment.lower() for word in inappropriate_words):
            raise forms.ValidationError("Review contains inappropriate content.")
        
        return comment

class SearchForm(forms.Form):
    """Enhanced search form with advanced filtering options."""
    
    SORT_CHOICES = [
        ('newest', 'Newest First'),
        ('oldest', 'Oldest First'),
        ('popular', 'Most Popular'),
        ('rating', 'Highest Rated'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
    ]
    
    PRICE_CHOICES = [
        ('', 'All Prices'),
        ('free', 'Free Only'),
        ('paid', 'Paid Only'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('', 'All Levels'),
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    q = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search prompts, tags, or categories...',
            'autocomplete': 'off'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    price_type = forms.ChoiceField(
        choices=PRICE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    difficulty_level = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='newest',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    min_rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min rating',
            'min': '1',
            'max': '5'
        })
    )
    
    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max price',
            'min': '0',
            'step': '0.01'
        })
    )
    
    tags = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by tags (comma-separated)'
        })
    )

    def clean_q(self):
        """Clean search query."""
        q = self.cleaned_data['q']
        if q and len(q.strip()) < 2:
            raise forms.ValidationError("Search query must be at least 2 characters long.")
        return q.strip() if q else ''

    def clean_max_price(self):
        """Validate maximum price."""
        max_price = self.cleaned_data['max_price']
        if max_price is not None and max_price < 0:
            raise forms.ValidationError("Maximum price cannot be negative.")
        return max_price

    def clean_min_rating(self):
        """Validate minimum rating."""
        min_rating = self.cleaned_data['min_rating']
        if min_rating is not None and (min_rating < 1 or min_rating > 5):
            raise forms.ValidationError("Minimum rating must be between 1 and 5.")
        return min_rating

    def clean_tags(self):
        """Process tags input."""
        tags = self.cleaned_data['tags']
        if not tags:
            return []
        
        tag_names = [tag.strip() for tag in tags.split(',') if tag.strip()]
        return tag_names[:5]  # Limit to 5 tags for search
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the category queryset dynamically
        self.fields['category'].queryset = Category.objects.filter(is_active=True)

class BulkPromptForm(forms.Form):
    """Form for bulk operations on prompts."""
    
    ACTION_CHOICES = [
        ('publish', 'Publish Selected'),
        ('unpublish', 'Unpublish Selected'),
        ('delete', 'Delete Selected'),
        ('change_category', 'Change Category'),
        ('change_price', 'Change Price'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    prompt_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    new_category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="Select Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    new_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'New price',
            'step': '0.01'
        })
    )

    def clean_prompt_ids(self):
        """Validate prompt IDs."""
        prompt_ids = self.cleaned_data['prompt_ids']
        if not prompt_ids:
            raise forms.ValidationError("No prompts selected.")
        
        try:
            ids = [int(id.strip()) for id in prompt_ids.split(',') if id.strip()]
            if not ids:
                raise forms.ValidationError("No valid prompt IDs provided.")
            return ids
        except ValueError:
            raise forms.ValidationError("Invalid prompt IDs provided.")

    def clean(self):
        """Validate form based on selected action."""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        if action == 'change_category' and not cleaned_data.get('new_category'):
            raise forms.ValidationError("Please select a new category.")
        
        if action == 'change_price' and cleaned_data.get('new_price') is None:
            raise forms.ValidationError("Please enter a new price.")
        
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the category queryset dynamically
        self.fields['new_category'].queryset = Category.objects.filter(is_active=True)

class PromptImportForm(forms.Form):
    """Form for importing prompts from JSON."""
    
    json_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json'
        }),
        help_text="Upload a JSON file containing prompts to import"
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Overwrite existing prompts with the same title"
    )
    
    def clean_json_file(self):
        """Validate JSON file."""
        json_file = self.cleaned_data['json_file']
        
        if not json_file.name.endswith('.json'):
            raise forms.ValidationError("Please upload a JSON file.")
        
        if json_file.size > 5 * 1024 * 1024:  # 5MB limit
            raise forms.ValidationError("File size must be less than 5MB.")
        
        try:
            import json
            json.load(json_file)
            json_file.seek(0)  # Reset file pointer
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON file.")
        
        return json_file 