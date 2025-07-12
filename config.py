import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    # Internationalization
    LANGUAGES = {
        'en': 'English',
        'de': 'Deutsch',
        'ru': 'Русский'
    }
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    
    # API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Subscription Plans
    SUBSCRIPTION_PLANS = {
        'single-table': {
            'name': 'Single Table Plan',
            'price_id': os.environ.get('STRIPE_SINGLE_TABLE_PRICE_ID'),
            'max_files': 1,
            'features': ['Upload 1 Excel file', 'Chat assistant', 'Basic analysis']
        },
        'multi-table': {
            'name': 'Multi Table Plan',
            'price_id': os.environ.get('STRIPE_MULTI_TABLE_PRICE_ID'),
            'max_files': 10,
            'features': ['Upload up to 10 Excel files', 'Advanced chat assistant', 'Full analysis suite', 'Priority support']
        }
    }
    
    # Mail settings (for future notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@example.com']

class DevelopmentConfig(Config):
    DEBUG = True
    # Development mode flags
    BYPASS_STRIPE = os.environ.get('BYPASS_STRIPE', 'false').lower() in ['true', 'on', '1']
    BYPASS_OPENAI = os.environ.get('BYPASS_OPENAI', 'false').lower() in ['true', 'on', '1']

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
