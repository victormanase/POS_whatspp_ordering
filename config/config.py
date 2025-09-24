import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Load .env from the parent directory (project root)
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'app/static/uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))
    
    # WhatsApp Settings
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER')
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
    
    # Business Settings
    DEFAULT_TAX_RATE = float(os.environ.get('DEFAULT_TAX_RATE', 0.18))
    
    # Currency Settings
    DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'TSH')
    CURRENCY_SYMBOL = os.environ.get('CURRENCY_SYMBOL', 'TSh')
    CURRENCY_SYMBOL_POSITION = os.environ.get('CURRENCY_SYMBOL_POSITION', 'before')
    
    BUSINESS_NAME = os.environ.get('BUSINESS_NAME', 'POS System')
    BUSINESS_ADDRESS = os.environ.get('BUSINESS_ADDRESS', '')
    BUSINESS_PHONE = os.environ.get('BUSINESS_PHONE', '')
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'data-dev.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite://'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'data.db')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}