# Excel Chat Assistant

A comprehensive Flask-based web application for secure, multilingual analysis and interaction with Excel files via an AI-powered chat assistant.

## Features

- **User Authentication & Authorization**
  - Email/password registration and login
  - Admin approval required for system access
  - Role-based access control (User/Admin)

- **Subscription Management**
  - Integration with Stripe for payment processing
  - Two subscription tiers: Single Table and Multi Table
  - Automatic subscription status management

- **Multilingual Support**
  - Full support for German, Russian, and English
  - Dynamic language switching
  - Localized AI assistant responses

- **Excel File Management**
  - Secure file upload and storage per user
  - Permission-based access control (Read, Read/Write, Read/Write/Delete)
  - File analysis and metadata extraction

- **AI Chat Assistant**
  - Text and voice input support
  - Context-aware responses about Excel data
  - Powered by OpenAI GPT and Whisper APIs
  - Multilingual conversation support

- **Admin Panel**
  - User management and approval
  - Subscription administration
  - Analytics and reporting
  - System monitoring

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-Babel
- **Frontend**: Bootstrap 5, JavaScript, HTML5
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI Services**: OpenAI GPT-3.5-turbo, Whisper
- **Payments**: Stripe
- **File Processing**: Pandas, openpyxl
- **Internationalization**: Flask-Babel

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js (for frontend dependencies, optional)
- OpenAI API key
- Stripe account (for payments)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Table_flask
   ```

2. **Set up environment**
   ```bash
   python setup.py
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
   - Visit http://localhost:5000
   - Admin login: admin@example.com / admin123

### Manual Setup (Alternative)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

3. **Set up translations**
   ```bash
   pybabel extract -F babel.cfg -k _l -o messages.pot .
   pybabel init -i messages.pot -d app/translations -l de
   pybabel init -i messages.pot -d app/translations -l ru
   ```

4. **Create admin user**
   ```bash
   flask deploy
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db

# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_SINGLE_TABLE_PRICE_ID=price_your_single_table_price_id
STRIPE_MULTI_TABLE_PRICE_ID=price_your_multi_table_price_id
```

### Database Configuration

- **Development**: SQLite (default)
- **Production**: Set `DATABASE_URL` to your PostgreSQL connection string

### Stripe Setup

1. Create a Stripe account
2. Set up two subscription products (Single Table, Multi Table)
3. Configure webhook endpoint: `/api/stripe/webhook`
4. Add price IDs to environment variables

## Project Structure

```
Table_flask/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── auth/                # Authentication blueprint
│   ├── main/                # Main application blueprint
│   ├── admin/               # Admin panel blueprint
│   ├── api/                 # API routes blueprint
│   ├── static/              # Static files (CSS, JS)
│   ├── templates/           # Jinja2 templates
│   └── translations/        # i18n translations
├── migrations/              # Database migrations
├── uploads/                 # User-uploaded files
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── babel.cfg              # Babel configuration
└── run.py                 # Application entry point
```

## Usage

### For Users

1. **Registration**: Create account and select subscription plan
2. **Admin Approval**: Wait for admin approval
3. **File Upload**: Upload Excel files with permission settings
4. **Chat Interface**: Interact with files using text or voice
5. **Data Analysis**: Ask questions, get insights, analyze patterns

### For Admins

1. **User Management**: Approve users, manage roles
2. **Subscription Management**: Monitor and modify subscriptions
3. **Analytics**: View usage statistics and trends
4. **System Administration**: Monitor system health

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout
- `POST /auth/subscribe` - Subscription creation

### File Management
- `POST /upload` - File upload
- `GET /file/<id>` - View file
- `GET /file/<id>/download` - Download file
- `DELETE /file/<id>` - Delete file

### Chat API
- `POST /api/chat/send` - Send text message
- `POST /api/chat/voice` - Send voice message
- `GET /api/chat/sessions/<id>/messages` - Get chat history

### Admin API
- `GET /admin/users` - List users
- `POST /admin/user/<id>/approve` - Approve user
- `GET /admin/analytics` - System analytics

## Development

### Running Tests

```bash
pytest
```

### Updating Translations

```bash
# Extract new messages
pybabel extract -F babel.cfg -k _l -o messages.pot .

# Update existing translations
pybabel update -i messages.pot -d app/translations

# Compile translations
pybabel compile -d app/translations
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

## Deployment

### Production Setup

1. **Environment Configuration**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:password@host:port/database
   ```

2. **Database Setup**
   ```bash
   flask db upgrade
   flask deploy
   ```

3. **Web Server**
   - Use Gunicorn or uWSGI
   - Configure nginx as reverse proxy
   - Set up SSL/TLS certificates

4. **Security Considerations**
   - Change default admin password
   - Set strong SECRET_KEY
   - Configure firewall rules
   - Set up monitoring and logging

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

## Security Features

- **Data Encryption**: All data encrypted in transit and at rest
- **User Isolation**: Files and data isolated per user
- **Permission System**: Granular access control
- **Session Management**: Secure session handling
- **CSRF Protection**: Protection against cross-site request forgery
- **Input Validation**: Comprehensive input sanitization

## Compliance

- **GDPR Compliant**: Full support for EU data protection
- **Privacy Policy**: Comprehensive privacy documentation
- **Data Rights**: User data access, export, and deletion
- **Audit Logging**: Admin action tracking

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check DATABASE_URL configuration
   - Ensure database server is running

2. **OpenAI API Errors**
   - Verify API key is valid
   - Check API quota and billing

3. **Stripe Webhook Issues**
   - Verify webhook URL is accessible
   - Check webhook secret configuration

4. **File Upload Problems**
   - Check file size limits
   - Verify upload directory permissions

### Logging

Logs are available in:
- Console output (development)
- `logs/` directory (production)
- System logs for errors

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## Support

For technical support:
- Email: support@example.com
- Documentation: [Project Wiki]
- Issues: [GitHub Issues]

## License

[Your License Here]

## Changelog

### Version 1.0.0
- Initial release
- Complete feature implementation
- Full multilingual support
- Stripe integration
- Admin panel

---

**Note**: This is a production-ready application. Ensure all security configurations are properly set before deploying to production environments.
