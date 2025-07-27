from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import random
from datetime import timedelta

from prompts.models import Category, Tag, Prompt, Review, PromptDownload, PromptPurchase, UserFavorite, PromptAnalytics

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample data for the AI Prompt Generator Platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create'
        )
        parser.add_argument(
            '--prompts',
            type=int,
            default=100,
            help='Number of prompts to create'
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=200,
            help='Number of reviews to create'
        )

    def handle(self, *args, **options):
        self.stdout.write('Generating sample data...')
        
        with transaction.atomic():
            self.create_categories()
            self.create_tags()
            users = self.create_users(options['users'])
            prompts = self.create_prompts(options['prompts'], users)
            self.create_reviews(options['reviews'], prompts, users)
            self.create_analytics(prompts, users)
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated sample data:\n'
                f'- {len(users)} users\n'
                f'- {len(prompts)} prompts\n'
                f'- {options["reviews"]} reviews\n'
                f'- Analytics data'
            )
        )

    def create_categories(self):
        """Create sample categories."""
        categories_data = [
            {
                'name': 'Writing & Content',
                'description': 'Prompts for writing articles, blog posts, and content creation',
                'color': '#3B82F6',
                'icon': 'fas fa-pen-fancy'
            },
            {
                'name': 'Marketing',
                'description': 'Prompts for marketing campaigns, ads, and social media',
                'color': '#10B981',
                'icon': 'fas fa-bullhorn'
            },
            {
                'name': 'Programming',
                'description': 'Prompts for code generation, debugging, and development',
                'color': '#F59E0B',
                'icon': 'fas fa-code'
            },
            {
                'name': 'Business',
                'description': 'Prompts for business plans, strategies, and analysis',
                'color': '#8B5CF6',
                'icon': 'fas fa-briefcase'
            },
            {
                'name': 'Education',
                'description': 'Prompts for learning, teaching, and educational content',
                'color': '#EF4444',
                'icon': 'fas fa-graduation-cap'
            },
            {
                'name': 'Creative',
                'description': 'Prompts for creative writing, storytelling, and art',
                'color': '#EC4899',
                'icon': 'fas fa-palette'
            },
            {
                'name': 'Productivity',
                'description': 'Prompts for productivity, organization, and efficiency',
                'color': '#06B6D4',
                'icon': 'fas fa-rocket'
            },
            {
                'name': 'Health & Wellness',
                'description': 'Prompts for health advice, fitness, and wellness',
                'color': '#84CC16',
                'icon': 'fas fa-heart'
            }
        ]
        
        for data in categories_data:
            Category.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
        
        self.stdout.write(f'Created {len(categories_data)} categories')

    def create_tags(self):
        """Create sample tags."""
        tags_data = [
            'AI', 'GPT', 'Claude', 'writing', 'marketing', 'programming', 'business',
            'productivity', 'creative', 'education', 'health', 'fitness', 'technology',
            'social media', 'email', 'copywriting', 'SEO', 'analytics', 'design',
            'development', 'python', 'javascript', 'react', 'nodejs', 'startup',
            'strategy', 'planning', 'research', 'analysis', 'content', 'blog',
            'article', 'story', 'poem', 'script', 'presentation', 'report',
            'proposal', 'resume', 'cover letter', 'email template', 'social post',
            'ad copy', 'landing page', 'product description', 'review', 'tutorial',
            'guide', 'manual', 'documentation', 'api', 'database', 'algorithm',
            'data analysis', 'machine learning', 'automation', 'workflow'
        ]
        
        for tag_name in tags_data:
            Tag.objects.get_or_create(name=tag_name)
        
        self.stdout.write(f'Created {len(tags_data)} tags')

    def create_users(self, num_users):
        """Create sample users."""
        users = []
        
        # Create some users with specific usernames
        special_users = [
            'alice_writer', 'bob_developer', 'charlie_marketer', 'diana_designer',
            'edward_analyst', 'fiona_creator', 'george_entrepreneur', 'helen_teacher'
        ]
        
        for i, username in enumerate(special_users):
            if i < num_users:
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='password123',
                    first_name=username.split('_')[0].title(),
                    last_name=username.split('_')[1].title()
                )
                users.append(user)
        
        # Create additional random users
        remaining_users = num_users - len(special_users)
        for i in range(remaining_users):
            username = f'user_{i + 1}'
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='password123',
                first_name=f'User{i + 1}',
                last_name='Test'
            )
            users.append(user)
        
        self.stdout.write(f'Created {len(users)} users')
        return users

    def create_prompts(self, num_prompts, users):
        """Create sample prompts."""
        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())
        prompts = []
        
        prompt_templates = [
            {
                'title': 'Professional Email Writer',
                'description': 'Generate professional, well-structured emails for business communication',
                'content': 'You are a professional email writer. Write a {tone} email about {topic}. Include a clear subject line, proper greeting, body with key points, and professional closing.',
                'preview_content': 'Subject: Follow-up on Project Discussion\n\nDear [Name],\n\nI hope this email finds you well. I wanted to follow up on our recent discussion regarding the project timeline...',
                'price_type': 'free',
                'difficulty_level': 'beginner'
            },
            {
                'title': 'SEO Content Optimizer',
                'description': 'Optimize your content for search engines with targeted keywords and structure',
                'content': 'You are an SEO expert. Analyze and optimize the following content for the keyword "{keyword}". Provide suggestions for title, meta description, headings, and content improvements.',
                'preview_content': 'Optimized Title: [Keyword-Rich Title]\nMeta Description: [Compelling 160-character description]\n\nH1: [Main Keyword]\nH2: [Related Keywords]\n\nContent optimization suggestions...',
                'price_type': 'paid',
                'difficulty_level': 'intermediate'
            },
            {
                'title': 'Code Review Assistant',
                'description': 'Get detailed code reviews and improvement suggestions for your programming projects',
                'content': 'You are a senior software engineer conducting a code review. Review the following {language} code for:\n1. Code quality and best practices\n2. Performance optimizations\n3. Security vulnerabilities\n4. Readability and maintainability\n\nProvide specific suggestions and examples.',
                'preview_content': 'Code Review Report:\n\n✅ Strengths:\n- Good variable naming\n- Proper error handling\n\n⚠️ Areas for Improvement:\n- Consider using async/await\n- Add input validation\n- Implement proper logging',
                'price_type': 'paid',
                'difficulty_level': 'advanced'
            },
            {
                'title': 'Social Media Content Creator',
                'description': 'Create engaging social media posts for various platforms and audiences',
                'content': 'You are a social media content creator. Create {platform} content about {topic} that is engaging, shareable, and optimized for the platform. Include hashtags and call-to-action.',
                'preview_content': '🚀 Exciting news! We just launched our new feature that will revolutionize how you work.\n\n✨ Key benefits:\n• 10x faster performance\n• Intuitive interface\n• 24/7 support\n\nTry it now: [link]\n\n#innovation #productivity #tech',
                'price_type': 'free',
                'difficulty_level': 'beginner'
            },
            {
                'title': 'Business Plan Generator',
                'description': 'Generate comprehensive business plans with market analysis and financial projections',
                'content': 'You are a business consultant. Create a detailed business plan for {business_type} including:\n1. Executive Summary\n2. Market Analysis\n3. Competitive Analysis\n4. Marketing Strategy\n5. Financial Projections\n6. Risk Assessment',
                'preview_content': 'Executive Summary:\n\n[Business Name] is a [business type] that will [value proposition]. We target [target market] and expect to generate $[revenue] in year one.\n\nMarket Analysis:\nThe [industry] market is valued at $[market_size]...',
                'price_type': 'paid',
                'difficulty_level': 'expert'
            }
        ]
        
        for i in range(num_prompts):
            template = random.choice(prompt_templates)
            author = random.choice(users)
            category = random.choice(categories)
            
            # Ensure unique title by adding a number
            base_title = template['title']
            title = f"{base_title} #{i + 1}"
            
            # Add variety to titles
            if random.random() < 0.3:
                title += f" - {random.choice(['Pro', 'Advanced', 'Ultimate', 'Master'])} Edition"
            
            prompt = Prompt.objects.create(
                title=title,
                description=template['description'],
                content=template['content'],
                preview_content=template['preview_content'],
                author=author,
                category=category,
                price_type=template['price_type'],
                price=Decimal(str(random.randint(0, 50))) if template['price_type'] == 'paid' else Decimal('0.00'),
                difficulty_level=template['difficulty_level'],
                status='published',
                is_active=True,
                estimated_tokens=random.randint(100, 2000),
                ai_model_compatibility=['GPT-4', 'Claude', 'Gemini'],
                use_cases=['Content creation', 'Business', 'Marketing'],
                views=random.randint(0, 1000),
                downloads=random.randint(0, 500),
                purchases=random.randint(0, 100),
                favorites=random.randint(0, 50),
                created_at=timezone.now() - timedelta(days=random.randint(0, 365)),
                published_at=timezone.now() - timedelta(days=random.randint(0, 365))
            )
            
            # Add random tags
            num_tags = random.randint(2, 6)
            selected_tags = random.sample(tags, min(num_tags, len(tags)))
            prompt.tags.set(selected_tags)
            
            prompts.append(prompt)
        
        self.stdout.write(f'Created {len(prompts)} prompts')
        return prompts

    def create_reviews(self, num_reviews, prompts, users):
        """Create sample reviews."""
        review_templates = [
            {
                'title': 'Excellent prompt!',
                'comment': 'This prompt exceeded my expectations. Very well structured and produces high-quality results.'
            },
            {
                'title': 'Great for beginners',
                'comment': 'Perfect for someone just starting out. Clear instructions and easy to follow.'
            },
            {
                'title': 'Highly recommended',
                'comment': 'I use this prompt regularly and it consistently delivers great results.'
            },
            {
                'title': 'Good value for money',
                'comment': 'Worth every penny. The quality of output is much better than free alternatives.'
            },
            {
                'title': 'Could be improved',
                'comment': 'Good concept but could use more specific examples and better formatting.'
            }
        ]
        
        for i in range(num_reviews):
            prompt = random.choice(prompts)
            user = random.choice(users)
            template = random.choice(review_templates)
            
            # Skip if user already reviewed this prompt
            if Review.objects.filter(prompt=prompt, user=user).exists():
                continue
            
            Review.objects.create(
                prompt=prompt,
                user=user,
                rating=random.randint(3, 5),
                title=template['title'],
                comment=template['comment'],
                is_verified_purchase=random.choice([True, False]),
                helpful_votes=random.randint(0, 10),
                created_at=timezone.now() - timedelta(days=random.randint(0, 30))
            )
        
        self.stdout.write(f'Created {num_reviews} reviews')

    def create_analytics(self, prompts, users):
        """Create sample analytics data."""
        for prompt in prompts:
            # Create analytics for the last 30 days
            for i in range(30):
                date = timezone.now().date() - timedelta(days=i)
                
                # Generate realistic daily stats
                views = random.randint(0, 50)
                downloads = random.randint(0, int(views * 0.3))
                purchases = random.randint(0, int(downloads * 0.2))
                revenue = purchases * float(prompt.price)
                
                PromptAnalytics.objects.create(
                    prompt=prompt,
                    date=date,
                    views=views,
                    downloads=downloads,
                    purchases=purchases,
                    revenue=Decimal(str(revenue))
                )
                
                # Create some download and purchase records
                if downloads > 0:
                    download_users = random.sample(users, min(downloads, len(users)))
                    for user in download_users:
                        PromptDownload.objects.get_or_create(
                            prompt=prompt,
                            user=user,
                            defaults={
                                'ip_address': f'192.168.1.{random.randint(1, 255)}',
                                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'created_at': timezone.now() - timedelta(days=i, hours=random.randint(0, 23))
                            }
                        )
                
                if purchases > 0 and prompt.price_type == 'paid':
                    purchase_users = random.sample(users, min(purchases, len(users)))
                    for user in purchase_users:
                        PromptPurchase.objects.get_or_create(
                            prompt=prompt,
                            user=user,
                            defaults={
                                'amount': prompt.price,
                                'payment_status': 'completed',
                                'stripe_payment_intent_id': f'pi_{random.randint(100000, 999999)}',
                                'ip_address': f'192.168.1.{random.randint(1, 255)}',
                                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'created_at': timezone.now() - timedelta(days=i, hours=random.randint(0, 23))
                            }
                        )
        
        self.stdout.write('Created analytics data') 