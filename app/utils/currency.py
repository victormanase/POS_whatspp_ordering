"""
Currency utilities and management
"""
from flask import current_app
from app.models import SystemSettings, db

# Supported currencies with their symbols and formatting
SUPPORTED_CURRENCIES = {
    'TSH': {
        'name': 'Tanzanian Shilling',
        'symbol': 'TSh',
        'code': 'TSH',
        'decimal_places': 2,
        'symbol_position': 'before',  # before or after
        'thousand_separator': ',',
        'decimal_separator': '.',
        'country': 'Tanzania'
    },
    'USD': {
        'name': 'US Dollar',
        'symbol': '$',
        'code': 'USD',
        'decimal_places': 2,
        'symbol_position': 'before',
        'thousand_separator': ',',
        'decimal_separator': '.',
        'country': 'United States'
    },
    'KES': {
        'name': 'Kenyan Shilling',
        'symbol': 'KSh',
        'code': 'KES',
        'decimal_places': 2,
        'symbol_position': 'before',
        'thousand_separator': ',',
        'decimal_separator': '.',
        'country': 'Kenya'
    },
    'UGX': {
        'name': 'Ugandan Shilling',
        'symbol': 'USh',
        'code': 'UGX',
        'decimal_places': 0,  # UGX typically doesn't use decimal places
        'symbol_position': 'before',
        'thousand_separator': ',',
        'decimal_separator': '.',
        'country': 'Uganda'
    },
    'EUR': {
        'name': 'Euro',
        'symbol': '€',
        'code': 'EUR',
        'decimal_places': 2,
        'symbol_position': 'after',
        'thousand_separator': '.',
        'decimal_separator': ',',
        'country': 'European Union'
    },
    'GBP': {
        'name': 'British Pound',
        'symbol': '£',
        'code': 'GBP',
        'decimal_places': 2,
        'symbol_position': 'before',
        'thousand_separator': ',',
        'decimal_separator': '.',
        'country': 'United Kingdom'
    },
    'NGN': {
        'name': 'Nigerian Naira',
        'symbol': '₦',
        'code': 'NGN',
        'decimal_places': 2,
        'symbol_position': 'before',
        'thousand_separator': ',',
        'decimal_separator': '.',
        'country': 'Nigeria'
    },
    'ZAR': {
        'name': 'South African Rand',
        'symbol': 'R',
        'code': 'ZAR',
        'decimal_places': 2,
        'symbol_position': 'before',
        'thousand_separator': ',',
        'decimal_separator': '.',
        'country': 'South Africa'
    }
}

class CurrencyManager:
    """Manages currency settings and formatting"""
    
    @staticmethod
    def get_current_currency():
        """Get the current currency settings"""
        try:
            # Try to get from database settings first
            currency_setting = SystemSettings.query.filter_by(key='default_currency').first()
            if currency_setting and currency_setting.value in SUPPORTED_CURRENCIES:
                currency_code = currency_setting.value
            else:
                # Fallback to config
                currency_code = current_app.config.get('DEFAULT_CURRENCY', 'TSH')
            
            return SUPPORTED_CURRENCIES.get(currency_code, SUPPORTED_CURRENCIES['TSH'])
        except:
            # Fallback to TSH if database is not available
            return SUPPORTED_CURRENCIES['TSH']
    
    @staticmethod
    def set_currency(currency_code):
        """Set the system currency"""
        if currency_code not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency_code}")
        
        try:
            # Update or create currency setting in database
            currency_setting = SystemSettings.query.filter_by(key='default_currency').first()
            if currency_setting:
                currency_setting.value = currency_code
            else:
                currency_setting = SystemSettings(
                    key='default_currency',
                    value=currency_code,
                    description=f'Default system currency - {SUPPORTED_CURRENCIES[currency_code]["name"]}'
                )
                db.session.add(currency_setting)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def format_currency(amount, currency_code=None):
        """Format amount as currency string"""
        if amount is None:
            amount = 0
        
        # Get currency info
        if currency_code and currency_code in SUPPORTED_CURRENCIES:
            currency_info = SUPPORTED_CURRENCIES[currency_code]
        else:
            currency_info = CurrencyManager.get_current_currency()
        
        # Format the number
        decimal_places = currency_info['decimal_places']
        thousand_sep = currency_info['thousand_separator']
        decimal_sep = currency_info['decimal_separator']
        symbol = currency_info['symbol']
        symbol_position = currency_info['symbol_position']
        
        # Convert to float and format
        amount = float(amount)
        
        if decimal_places == 0:
            formatted_number = f"{int(amount):,}".replace(',', thousand_sep)
        else:
            formatted_number = f"{amount:,.{decimal_places}f}"
            if thousand_sep != ',' or decimal_sep != '.':
                # Replace default separators with custom ones
                parts = formatted_number.split('.')
                parts[0] = parts[0].replace(',', thousand_sep)
                formatted_number = decimal_sep.join(parts)
        
        # Add currency symbol
        if symbol_position == 'before':
            return f"{symbol} {formatted_number}"
        else:
            return f"{formatted_number} {symbol}"
    
    @staticmethod
    def get_currency_list():
        """Get list of all supported currencies"""
        return [
            {
                'code': code,
                'name': info['name'],
                'symbol': info['symbol'],
                'country': info['country']
            }
            for code, info in SUPPORTED_CURRENCIES.items()
        ]
    
    @staticmethod
    def parse_currency_input(input_string):
        """Parse currency input string to float"""
        if not input_string:
            return 0.0
        
        # Remove currency symbols and clean up
        cleaned = str(input_string).strip()
        
        # Remove common currency symbols
        for currency_info in SUPPORTED_CURRENCIES.values():
            cleaned = cleaned.replace(currency_info['symbol'], '')
        
        # Remove spaces and common separators, keep only numbers and decimal point
        cleaned = ''.join(c for c in cleaned if c.isdigit() or c in '.,')
        
        # Handle different decimal separators
        if ',' in cleaned and '.' in cleaned:
            # Both present, assume comma is thousands separator
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Only comma, could be decimal separator (European style)
            if len(cleaned.split(',')[-1]) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

# Global currency formatter function for templates
def format_currency(amount, currency_code=None):
    """Template-friendly currency formatter"""
    return CurrencyManager.format_currency(amount, currency_code)