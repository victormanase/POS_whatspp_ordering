import os
import pymysql
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config.config import config
from app.models import db, User

# Install PyMySQL as MySQLdb
pymysql.install_as_MySQLdb()

login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.views.auth import auth_bp
    from app.views.main import main_bp
    from app.views.products import products_bp
    from app.views.pos import pos_bp
    from app.views.reports import reports_bp
    from app.views.whatsapp import whatsapp_bp
    from app.views.settings import settings_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(pos_bp, url_prefix='/pos')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(whatsapp_bp, url_prefix='/whatsapp')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(app.root_path, 'static', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Template filters and context processors
    from app.utils.currency import CurrencyManager, format_currency as currency_formatter
    
    @app.template_filter('currency')
    def format_currency(amount, currency_code=None):
        """Format amount as currency using currency manager"""
        return currency_formatter(amount, currency_code)
    
    @app.template_filter('number')
    def format_number(number):
        """Format number with commas"""
        if number is None:
            number = 0
        return f"{int(number):,}"
    
    @app.context_processor
    def utility_processor():
        """Make utility functions available in templates"""
        def formatCurrency(amount, currency_code=None):
            return currency_formatter(amount, currency_code)
        
        def formatNumber(number):
            if number is None:
                number = 0
            return f"{int(number):,}"
        
        def get_current_currency():
            return CurrencyManager.get_current_currency()
        
        def get_currency_list():
            return CurrencyManager.get_currency_list()
        
        from flask_wtf.csrf import generate_csrf
        
        def csrf_token():
            return generate_csrf()
        
        return dict(
            formatCurrency=formatCurrency, 
            formatNumber=formatNumber,
            get_current_currency=get_current_currency,
            get_currency_list=get_currency_list,
            csrf_token=csrf_token
        )
    
    return app
