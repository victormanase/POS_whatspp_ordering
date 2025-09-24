# 🏪 Advanced POS System with WhatsApp Integration

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.0+-purple.svg)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Business-25D366.svg)

A comprehensive, modern Point of Sale (POS) system with WhatsApp Business integration built with Flask, MySQL, and Bootstrap 5. Designed for small to medium businesses to efficiently manage inventory, sales, customers, and WhatsApp orders in one unified platform.

## ✨ Features

### 🎯 Core POS Features
- **🛒 Advanced Point of Sale**: Intuitive sales interface with barcode scanning, cart management, and quick checkout
- **📦 Comprehensive Product Management**: Products with categories, images, barcodes, pricing tiers, and stock tracking
- **📊 Inventory Management**: Real-time stock tracking, low-stock alerts, purchase recording, and supplier management
- **🧾 Receipt & Invoice System**: Digital and printable receipts with customizable branding
- **👥 Multi-User Support**: Role-based access (Admin/Cashier) with secure authentication
- **📈 Advanced Analytics**: Sales reports, profit analysis, inventory reports, and business insights

### 💰 Financial Management
- **💱 Multi-Currency Support**: Support for multiple currencies with real-time formatting (TSH, USD, EUR, etc.)
- **💳 Multiple Payment Methods**: Cash, Card, Mobile Money (M-Pesa, Airtel Money, etc.)
- **🧮 Tax Calculation**: Configurable tax rates with automatic calculations
- **💸 Refund Management**: Complete refund processing with reason tracking

### 📱 WhatsApp Business Integration
- **🤖 Smart Order Processing**: Customers can browse products and place orders via WhatsApp
- **📋 Order Management**: WhatsApp orders integrate seamlessly into the POS system
- **💬 Customer Communication**: Direct WhatsApp messaging from the admin panel
- **🔔 Automated Notifications**: Order confirmations, status updates, and delivery notifications
- **📊 WhatsApp Analytics**: Track WhatsApp order performance and customer engagement

### 🏢 Business Management
- **🏪 Supplier Management**: Complete supplier database with purchase history and contact management
- **📋 Purchase Management**: Record purchases, track supplier performance, and manage procurement
- **👤 Customer Management**: Customer profiles, purchase history, and loyalty tracking
- **⚙️ System Settings**: Configurable business settings, user management, and system preferences

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **MySQL 8.0+** database server
- **Node.js** (optional, for advanced frontend features)
- **WhatsApp Business Account** (for WhatsApp integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd pos-system
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup MySQL database**
   ```bash
   # Create database
   mysql -u root -p
   CREATE DATABASE pos_system;
   CREATE USER 'pos_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON pos_system.* TO 'pos_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

5. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Flask Configuration
   SECRET_KEY=your-very-secret-key-here
   FLASK_ENV=development
   
   # Database Configuration
   DATABASE_URL=mysql+pymysql://pos_user:your_password@localhost/pos_system
   
   # Business Settings
   DEFAULT_CURRENCY=TSH
   DEFAULT_TAX_RATE=0.18
   BUSINESS_NAME=Your Business Name
   BUSINESS_ADDRESS=Your Business Address
   BUSINESS_PHONE=+255123456789
   BUSINESS_EMAIL=info@yourbusiness.com
   
   # WhatsApp Integration (Optional)
   WHATSAPP_TOKEN=your_whatsapp_business_token
   WHATSAPP_PHONE_ID=your_phone_number_id
   WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
   ```

6. **Initialize database**
   ```bash
   export FLASK_APP=run.py
   flask db upgrade
   python init_settings.py  # Initialize system settings
   ```

7. **Create admin user**
   ```bash
   python create_admin.py
   ```
   Default credentials:
   - **Username**: admin
   - **Password**: admin123

8. **Run the application**
   ```bash
   python run.py
   ```
   
   🌐 Application will be available at `http://localhost:5000`

## 📖 Usage Guide

### 🎛️ Dashboard
- **Sales Overview**: Today's sales, monthly revenue, and key metrics
- **Inventory Alerts**: Low stock notifications and out-of-stock items
- **Recent Activities**: Latest transactions and system updates
- **Quick Actions**: Fast access to common tasks

### 🛒 Point of Sale
1. **Add Products**: Search by name, scan barcode, or browse categories
2. **Manage Cart**: Adjust quantities, apply discounts, remove items
3. **Customer Info**: Add customer details for receipt and tracking
4. **Payment**: Select payment method (Cash, Card, Mobile Money)
5. **Complete Sale**: Generate receipt and update inventory

### 📦 Product Management
- **Add Products**: Name, description, barcode, category, pricing, images
- **Stock Tracking**: Current stock, reorder levels, purchase history
- **Categories**: Organize products into logical categories
- **Bulk Import**: Import products via CSV files

### 📊 Inventory Management
- **Stock Overview**: Real-time inventory levels across all products
- **Low Stock Alerts**: Automatic notifications for items below reorder level
- **Purchase Recording**: Track incoming stock and supplier information
- **Stock Movements**: Complete audit trail of inventory changes

### 🏪 Supplier Management
- **Supplier Database**: Contact information, payment terms, performance metrics
- **Purchase History**: Complete record of all purchases from each supplier
- **Performance Tracking**: Delivery times, quality ratings, and reliability scores

### 📱 WhatsApp Integration
- **Order Reception**: Customers place orders directly via WhatsApp
- **Order Processing**: Review, confirm, and fulfill WhatsApp orders
- **Customer Communication**: Direct messaging with order updates
- **Automated Responses**: Smart replies for common inquiries

### 📈 Reports & Analytics
- **Sales Reports**: Daily, weekly, monthly, and custom date ranges
- **Product Performance**: Best sellers, slow movers, and profit analysis
- **Inventory Reports**: Stock levels, valuation, and movement history
- **Financial Reports**: Revenue, profit margins, and tax summaries

## 🔌 WhatsApp Commands

Customers can interact with your business using these WhatsApp commands:

| Command | Description | Example |
|---------|-------------|----------|
| `help` | Show available commands | `help` |
| `catalog` | View product catalog | `catalog` |
| `search [product]` | Search for products | `search phone` |
| `price [product]` | Get product price | `price samsung galaxy` |
| `order [product] [qty]` | Place an order | `order iphone 12 1` |
| `status [order_id]` | Check order status | `status WA123` |
| `location` | Get business address | `location` |

## 📡 API Documentation

### WhatsApp Webhook Endpoints
```bash
# Receive WhatsApp messages
POST /api/whatsapp/webhook

# Verify webhook (Meta requirement)
GET /api/whatsapp/webhook?hub.verify_token=TOKEN

# Send WhatsApp message
POST /api/whatsapp/send
```

### POS API Endpoints
```bash
# Product search for POS
GET /api/products/search?q=product_name

# Get product details
GET /api/products/{product_id}

# Complete sale transaction
POST /api/pos/complete_sale

# Get sales data
GET /api/sales?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
```

### Authentication
Most API endpoints require authentication:
```bash
# Login to get session
POST /auth/login
{
  "username": "admin",
  "password": "admin123"
}
```

## 📱 File Structure

```
pos-system/
├── app/
│   ├── models/
│   │   ├── __init__.py        # Database models
│   │   ├── product.py        # Product, Category models
│   │   ├── sale.py           # Sales, SaleItem models
│   │   ├── user.py           # User, Role models
│   │   └── supplier.py       # Supplier, Purchase models
│   ├── views/
│   │   ├── auth.py           # Authentication routes
│   │   ├── main.py           # Dashboard routes
│   │   ├── products.py       # Product management
│   │   ├── pos.py            # POS and sales
│   │   ├── settings.py       # System settings
│   │   └── whatsapp.py       # WhatsApp integration
│   ├── templates/
│   │   ├── auth/             # Login templates
│   │   ├── dashboard/        # Dashboard templates
│   │   ├── products/         # Product management
│   │   ├── pos/              # POS and sales
│   │   ├── settings/         # System settings
│   │   └── base.html         # Base template
│   ├── static/
│   │   ├── css/              # Custom stylesheets
│   │   ├── js/               # JavaScript files
│   │   ├── img/              # Images and icons
│   │   └── uploads/          # Uploaded product images
│   └── utils/
│       ├── currency.py       # Currency management
│       └── whatsapp.py       # WhatsApp utilities
├── config/
│   └── config.py          # Flask configuration
├── migrations/             # Database migrations
├── tests/                  # Unit tests
├── .env                    # Environment variables
├── .gitignore             # Git ignore file
├── requirements.txt        # Python dependencies
├── run.py                 # Application entry point
├── init_settings.py       # Initialize system settings
├── create_admin.py        # Create admin user script
└── README.md              # This file
```

## 🚀 Production Deployment

### 🐳 Docker Deployment (Recommended)

1. **Build and run with Docker Compose**
   ```bash
   # Create docker-compose.yml
   docker-compose up -d
   ```

2. **Docker Compose Configuration**
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "80:5000"
       environment:
         - FLASK_ENV=production
       depends_on:
         - db
     
     db:
       image: mysql:8.0
       environment:
         MYSQL_ROOT_PASSWORD: root_password
         MYSQL_DATABASE: pos_system
         MYSQL_USER: pos_user
         MYSQL_PASSWORD: pos_password
       volumes:
         - mysql_data:/var/lib/mysql
   
   volumes:
     mysql_data:
   ```

### 🔧 Manual Deployment

1. **Install production server**
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 run:app
   ```

3. **Configure Nginx (reverse proxy)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static {
           alias /path/to/pos-system/app/static;
       }
   }
   ```

4. **SSL/HTTPS Setup**
   ```bash
   # Using Certbot for Let's Encrypt
   sudo certbot --nginx -d your-domain.com
   ```

## 🔒 Security Considerations

- ✅ **Change default passwords** before production
- ✅ **Use strong SECRET_KEY** in production
- ✅ **Enable HTTPS** with valid SSL certificates
- ✅ **Regular database backups** 
- ✅ **Monitor access logs** for suspicious activity
- ✅ **Keep dependencies updated** with `pip-audit`
- ✅ **Configure firewall** to restrict access
- ✅ **Use environment variables** for sensitive data

## 🛠️ Maintenance

### Daily Tasks
- ✅ Check system logs for errors
- ✅ Verify backup completion
- ✅ Monitor disk space usage

### Weekly Tasks
- ✅ Review sales reports and analytics
- ✅ Update product inventory
- ✅ Check for software updates

### Monthly Tasks
- ✅ Full system backup
- ✅ Security audit
- ✅ Performance optimization

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check MySQL service status
sudo systemctl status mysql

# Restart MySQL if needed
sudo systemctl restart mysql
```

**WhatsApp Integration Not Working**
- Verify webhook URL is accessible
- Check WhatsApp Business API credentials
- Review webhook logs in Meta Developer Console

**Performance Issues**
- Enable database query optimization
- Configure Redis for session storage
- Implement CDN for static files

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Code formatting
black app/

# Linting
flake8 app/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚑 Support & Contact

- 📞 **Phone**: +255 123 456 789
- 📧 **Email**: support@yourpos.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/pos-system/issues)
- 📚 **Documentation**: [Wiki](https://github.com/yourusername/pos-system/wiki)

## 🚀 Roadmap

- [ ] **Mobile App**: Native iOS/Android applications
- [ ] **Multi-location Support**: Manage multiple store locations
- [ ] **Advanced Analytics**: AI-powered insights and predictions
- [ ] **Integration APIs**: Third-party accounting software integration
- [ ] **Loyalty Program**: Customer rewards and points system
- [ ] **E-commerce Integration**: Online store synchronization

---

**✨ Built with ❤️ for small and medium businesses**

*This POS system is designed to grow with your business. From a single store to multiple locations, from basic sales to advanced analytics, we've got you covered.*
