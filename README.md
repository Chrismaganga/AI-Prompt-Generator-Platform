# 🧠 AI Prompt Generator Platform

A comprehensive platform for creating, sharing, and monetizing AI prompts - like PromptBase but built with Django and modern web technologies.

## ✨ Features

### For Users

- **Browse & Search**: Discover prompts by category, tags, price, and popularity
- **Smart Filtering**: Filter by price (free/paid), category, ratings, and more
- **User Reviews**: Rate and review prompts with 5-star system
- **Secure Payments**: Stripe integration for purchasing paid prompts
- **User Dashboard**: Track downloads, purchases, and created prompts
- **Responsive Design**: Beautiful UI built with Tailwind CSS

### For Creators

- **Prompt Creation**: Rich text editor with preview functionality
- **Monetization**: Set prices and earn from your prompts
- **Analytics**: Track views, downloads, and earnings
- **Stripe Connect**: Direct payments to your Stripe account
- **Prompt Management**: Edit, update, and manage your prompts

### Platform Features

- **User Authentication**: Secure login/signup with email verification
- **Tagging System**: Organize prompts with flexible tagging
- **Categories**: Browse prompts by predefined categories
- **Search & Discovery**: Advanced search with multiple filters
- **Payment Processing**: Secure Stripe integration
- **Admin Panel**: Comprehensive Django admin interface

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/AI-Prompt-Generator-Platform.git
   cd AI-Prompt-Generator-Platform
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**

   ```bash
   python manage.py runserver
   ```

8. **Visit the application**
   - Main site: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Stripe Settings (Required for payments)
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Email Settings (Optional for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Stripe Dashboard
3. Set up webhooks for payment processing
4. Update your `.env` file with the keys

## 📁 Project Structure

```
AI-Prompt-Generator-Platform/
├── prompt_platform/          # Main Django project
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py              # WSGI configuration
├── prompts/                 # Prompts app
│   ├── models.py            # Prompt, Category, Review models
│   ├── views.py             # Prompt views and logic
│   ├── forms.py             # Prompt forms
│   └── urls.py              # Prompt URL patterns
├── users/                   # Custom user app
│   ├── models.py            # Custom user model
│   └── admin.py             # User admin configuration
├── payments/                # Payment processing app
│   ├── models.py            # Payment models
│   ├── views.py             # Stripe integration
│   └── urls.py              # Payment URL patterns
├── templates/               # HTML templates
│   ├── base.html            # Base template
│   ├── prompts/             # Prompt templates
│   └── payments/            # Payment templates
├── static/                  # Static files (CSS, JS, images)
├── media/                   # User uploaded files
├── requirements.txt         # Python dependencies
├── manage.py               # Django management script
└── README.md               # This file
```

## 🎯 Usage Guide

### For Users

1. **Browse Prompts**

   - Visit the homepage to see featured and latest prompts
   - Use the search bar to find specific prompts
   - Filter by category, price, or sort by popularity/rating

2. **Download Free Prompts**

   - Click on any free prompt
   - Click "Download Free" to get instant access
   - Copy the prompt content and use with your AI tool

3. **Purchase Paid Prompts**

   - Click on a paid prompt
   - Click "Purchase" to go to checkout
   - Complete payment with Stripe
   - Get instant access to the full prompt

4. **Leave Reviews**
   - After downloading/purchasing, leave a review
   - Rate the prompt from 1-5 stars
   - Share your experience with other users

### For Creators

1. **Create Your First Prompt**

   - Sign up and log in to your account
   - Click "Create Prompt" in the navigation
   - Fill in the prompt details (title, description, content)
   - Set pricing (free or paid)
   - Add tags and select category
   - Submit for review

2. **Monetize Your Prompts**

   - Set competitive prices for your prompts
   - Connect your Stripe account for payments
   - Track earnings in your dashboard
   - Get paid directly to your bank account

3. **Manage Your Prompts**
   - Edit existing prompts anytime
   - Update pricing and content
   - View analytics and performance
   - Respond to user reviews

## 🛠️ Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files

```bash
python manage.py collectstatic
```

### Creating Sample Data

```bash
python manage.py shell
```

```python
from prompts.models import Category, Prompt
from django.contrib.auth import get_user_model

User = get_user_model()

# Create sample categories
categories = [
    {'name': 'Writing', 'icon': 'fas fa-pen', 'color': '#3B82F6'},
    {'name': 'Marketing', 'icon': 'fas fa-bullhorn', 'color': '#10B981'},
    {'name': 'Programming', 'icon': 'fas fa-code', 'color': '#F59E0B'},
    {'name': 'Design', 'icon': 'fas fa-palette', 'color': '#EF4444'},
]

for cat_data in categories:
    Category.objects.get_or_create(
        name=cat_data['name'],
        defaults=cat_data
    )
```

## 🚀 Deployment

### Production Checklist

1. **Environment Variables**

   - Set `DEBUG=False`
   - Configure production database (PostgreSQL recommended)
   - Set up proper email backend
   - Configure Stripe production keys

2. **Security**

   - Use HTTPS in production
   - Set secure cookie settings
   - Configure CSRF trusted origins
   - Use environment variables for secrets

3. **Performance**

   - Use a production WSGI server (Gunicorn)
   - Set up static file serving (WhiteNoise or CDN)
   - Configure caching (Redis recommended)
   - Use a production database

4. **Monitoring**
   - Set up error tracking (Sentry)
   - Configure logging
   - Monitor performance metrics

### Deployment Options

- **Heroku**: Easy deployment with PostgreSQL add-on
- **DigitalOcean**: App Platform or Droplet with Docker
- **AWS**: Elastic Beanstalk or EC2 with RDS
- **Vercel**: Serverless deployment (with limitations)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [Stripe](https://stripe.com/) - Payment processing
- [Font Awesome](https://fontawesome.com/) - Icons
- [PromptBase](https://promptbase.com/) - Inspiration

## 📞 Support

- Create an issue for bugs or feature requests
- Email: support@prompthub.com
- Documentation: [docs.prompthub.com](https://docs.prompthub.com)

---

**Built with ❤️ for the AI community**
