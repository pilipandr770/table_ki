from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Initialize Babel
    babel.init_app(app)
    
    def get_locale():
        # 1. Check if user has a language preference in session
        if 'language' in session:
            return session['language']
        
        # 2. Check if user is logged in and has a preference
        from flask_login import current_user
        if current_user.is_authenticated and current_user.language_preference:
            return current_user.language_preference
        
        # 3. Check Accept-Language header
        return request.accept_languages.best_match(['en', 'de', 'ru']) or 'en'
    
    # Make get_locale available to templates
    app.jinja_env.globals.update(get_locale=get_locale)
    
    # Add nl2br filter for handling line breaks in chat messages
    def nl2br(value):
        if value:
            return value.replace('\n', '<br>')
        return ''
    
    app.jinja_env.filters['nl2br'] = nl2br
    
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['LANGUAGES'] = {
        'en': 'English',
        'de': 'Deutsch', 
        'ru': 'Русский'
    }
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.audio_test import bp as audio_test_bp
    app.register_blueprint(audio_test_bp, url_prefix='/audio-test')
    
    # Register CLI commands
    from app import cli
    cli.init_app(app)
    
    @app.route('/set-language/<language>')
    def set_language(language=None):
        """Set the user's language preference"""
        from flask import session, redirect, request
        session['language'] = language
        return redirect(request.referrer or url_for('main.index'))
    
    return app

from app import models
