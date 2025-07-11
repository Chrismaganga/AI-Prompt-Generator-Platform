from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from prompts.models import Category, Prompt
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial data for the AI Prompt Platform'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create categories
        categories_data = [
            {
                'name': 'Writing',
                'description': 'Prompts for creative writing, content creation, and copywriting',
                'icon': 'fas fa-pen',
                'color': '#3B82F6'
            },
            {
                'name': 'Marketing',
                'description': 'Prompts for marketing campaigns, social media, and advertising',
                'icon': 'fas fa-bullhorn',
                'color': '#10B981'
            },
            {
                'name': 'Programming',
                'description': 'Prompts for code generation, debugging, and software development',
                'icon': 'fas fa-code',
                'color': '#F59E0B'
            },
            {
                'name': 'Design',
                'description': 'Prompts for graphic design, UI/UX, and visual content',
                'icon': 'fas fa-palette',
                'color': '#EF4444'
            },
            {
                'name': 'Business',
                'description': 'Prompts for business strategy, analysis, and planning',
                'icon': 'fas fa-briefcase',
                'color': '#8B5CF6'
            },
            {
                'name': 'Education',
                'description': 'Prompts for learning, teaching, and educational content',
                'icon': 'fas fa-graduation-cap',
                'color': '#06B6D4'
            },
            {
                'name': 'Productivity',
                'description': 'Prompts for task management, organization, and efficiency',
                'icon': 'fas fa-tasks',
                'color': '#84CC16'
            },
            {
                'name': 'Entertainment',
                'description': 'Prompts for games, storytelling, and creative entertainment',
                'icon': 'fas fa-gamepad',
                'color': '#EC4899'
            }
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            created_categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')
        
        # Create a demo user if none exists
        if not User.objects.filter(username='demo_creator').exists():
            demo_user = User.objects.create_user(
                username='demo_creator',
                email='demo@prompthub.com',
                password='demo123456',
                first_name='Demo',
                last_name='Creator',
                bio='A demo creator showcasing the platform capabilities',
                is_creator=True
            )
            self.stdout.write(f'Created demo user: {demo_user.username}')
        else:
            demo_user = User.objects.get(username='demo_creator')
            self.stdout.write(f'Demo user already exists: {demo_user.username}')
        
        # Create sample prompts
        sample_prompts = [
            {
                'title': 'Professional Email Writer',
                'description': 'Generate professional, polite, and effective business emails for any situation.',
                'content': '''You are a professional email writer. Write a [TYPE] email that is:
- Professional and courteous
- Clear and concise
- Appropriate for the recipient
- Well-structured with proper greeting and closing

Context: [CONTEXT]
Recipient: [RECIPIENT]
Purpose: [PURPOSE]

Please write the email in a professional tone.''',
                'preview_content': 'Subject: Follow-up on Project Discussion\n\nDear [Name],\n\nThank you for taking the time to discuss the project yesterday. I appreciate your insights and look forward to our continued collaboration...',
                'category': 'Business',
                'price_type': 'free',
                'tags': 'email, business, professional, communication'
            },
            {
                'title': 'Creative Story Generator',
                'description': 'Create engaging stories with compelling characters and plot twists.',
                'content': '''You are a creative storyteller. Create a [GENRE] story with the following elements:

Genre: [GENRE]
Main Character: [CHARACTER_DESCRIPTION]
Setting: [SETTING]
Conflict: [CONFLICT]
Theme: [THEME]

Requirements:
- Engaging opening hook
- Well-developed characters
- Compelling plot with twists
- Satisfying conclusion
- Word count: [WORD_COUNT]

Please write the story with vivid descriptions and emotional depth.''',
                'preview_content': 'The old lighthouse stood sentinel on the rocky coast, its beam cutting through the fog like a sword of light. Sarah had always been drawn to its mysterious glow...',
                'category': 'Writing',
                'price_type': 'paid',
                'price': 2.99,
                'tags': 'story, creative, fiction, writing'
            },
            {
                'title': 'Code Review Assistant',
                'description': 'Get comprehensive code reviews with suggestions for improvement and best practices.',
                'content': '''You are an expert code reviewer. Please review the following [LANGUAGE] code and provide:

1. **Code Quality Assessment**
   - Readability and maintainability
   - Performance considerations
   - Security vulnerabilities

2. **Best Practices Check**
   - Coding standards compliance
   - Design patterns usage
   - Error handling

3. **Improvement Suggestions**
   - Specific refactoring recommendations
   - Alternative approaches
   - Optimization opportunities

Code to review:
```[LANGUAGE]
[CODE_HERE]
```

Please provide detailed feedback with examples.''',
                'preview_content': '## Code Quality Assessment\n\n✅ **Good**: Clear variable naming and consistent formatting\n⚠️ **Improve**: Consider adding input validation...',
                'category': 'Programming',
                'price_type': 'paid',
                'price': 4.99,
                'tags': 'code, review, programming, development'
            },
            {
                'title': 'Social Media Content Creator',
                'description': 'Generate engaging social media posts for any platform and industry.',
                'content': '''You are a social media content creator. Create [PLATFORM] content for [INDUSTRY] that is:

Platform: [PLATFORM] (Instagram, Twitter, LinkedIn, Facebook, TikTok)
Industry: [INDUSTRY]
Content Type: [CONTENT_TYPE] (post, story, video script, carousel)
Tone: [TONE] (professional, casual, humorous, inspirational)
Goal: [GOAL] (engagement, awareness, sales, education)

Requirements:
- Platform-optimized format
- Engaging hook
- Relevant hashtags
- Call-to-action
- Visual elements suggestions

Please create compelling content that resonates with the target audience.''',
                'preview_content': '🚀 Ready to transform your business?\n\nDiscover the 3 game-changing strategies that helped our clients increase revenue by 300% in just 6 months...',
                'category': 'Marketing',
                'price_type': 'free',
                'tags': 'social media, marketing, content, engagement'
            }
        ]
        
        for prompt_data in sample_prompts:
            category = Category.objects.get(name=prompt_data['category'])
            
            # Check if prompt already exists
            if not Prompt.objects.filter(title=prompt_data['title']).exists():
                prompt = Prompt.objects.create(
                    title=prompt_data['title'],
                    description=prompt_data['description'],
                    content=prompt_data['content'],
                    preview_content=prompt_data['preview_content'],
                    category=category,
                    author=demo_user,
                    price_type=prompt_data['price_type'],
                    price=prompt_data.get('price', 0.00),
                    status='published',
                    published_at=timezone.now()
                )
                
                # Add tags
                for tag_name in prompt_data['tags'].split(', '):
                    prompt.tags.add(tag_name.strip())
                
                self.stdout.write(f'Created sample prompt: {prompt.title}')
            else:
                self.stdout.write(f'Sample prompt already exists: {prompt_data["title"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                'Successfully set up initial data! '
                f'Created {len(created_categories)} categories and sample prompts.'
            )
        ) 