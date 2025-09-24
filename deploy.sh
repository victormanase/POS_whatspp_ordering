#!/bin/bash

# POS System Docker Deployment Script
# This script helps deploy the POS system using Docker Compose

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Function to create environment file
create_env_file() {
    if [ ! -f ".env.local" ]; then
        print_status "Creating .env.local file..."
        cp .env.docker .env.local
        
        # Generate random passwords
        DB_ROOT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
        
        # Replace default passwords with generated ones
        sed -i "s/secure_root_password_123/${DB_ROOT_PASSWORD}/g" .env.local
        sed -i "s/secure_pos_password_123/${DB_PASSWORD}/g" .env.local
        sed -i "s/secure_redis_password_123/${REDIS_PASSWORD}/g" .env.local
        sed -i "s/your-very-long-and-secure-secret-key-for-production-change-this/${SECRET_KEY}/g" .env.local
        
        print_success "Environment file created with secure random passwords"
        print_warning "Please review and customize .env.local for your deployment"
    else
        print_status "Using existing .env.local file"
    fi
}

# Function to build and start services
deploy() {
    print_status "Starting POS System deployment..."
    
    # Create logs directory
    mkdir -p logs
    
    # Build and start services
    print_status "Building Docker images..."
    docker-compose --env-file .env.local build
    
    print_status "Starting services..."
    docker-compose --env-file .env.local up -d
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    print_status "Running database migrations..."
    docker-compose --env-file .env.local exec web flask db upgrade
    
    # Initialize system settings
    print_status "Initializing system settings..."
    docker-compose --env-file .env.local exec web python init_settings.py
    
    print_success "POS System deployed successfully!"
    print_status "Access your POS system at: http://localhost"
    print_status "Default admin credentials: admin / admin123"
    print_warning "Please change the default password after first login!"
}

# Function to show logs
show_logs() {
    print_status "Showing POS System logs..."
    docker-compose --env-file .env.local logs -f
}

# Function to stop services
stop() {
    print_status "Stopping POS System..."
    docker-compose --env-file .env.local down
    print_success "POS System stopped"
}

# Function to show status
status() {
    print_status "POS System status:"
    docker-compose --env-file .env.local ps
}

# Function to backup database
backup() {
    print_status "Creating database backup..."
    
    # Create backup directory
    mkdir -p backups
    
    # Generate backup filename with timestamp
    BACKUP_FILE="backups/pos_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Create backup
    docker-compose --env-file .env.local exec db mysqldump -u root -p"${DB_ROOT_PASSWORD}" pos_system > "$BACKUP_FILE"
    
    print_success "Database backup created: $BACKUP_FILE"
}

# Function to restore database
restore() {
    if [ -z "$1" ]; then
        print_error "Please provide backup file path"
        print_status "Usage: $0 restore /path/to/backup.sql"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    print_warning "This will overwrite the current database. Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
        print_status "Restoring database from: $1"
        docker-compose --env-file .env.local exec -T db mysql -u root -p"${DB_ROOT_PASSWORD}" pos_system < "$1"
        print_success "Database restored successfully"
    else
        print_status "Restore cancelled"
    fi
}

# Function to update system
update() {
    print_status "Updating POS System..."
    
    # Pull latest code (if using git)
    if [ -d ".git" ]; then
        print_status "Pulling latest code..."
        git pull
    fi
    
    # Rebuild and restart services
    print_status "Rebuilding services..."
    docker-compose --env-file .env.local build --no-cache
    docker-compose --env-file .env.local up -d
    
    # Run migrations
    print_status "Running database migrations..."
    docker-compose --env-file .env.local exec web flask db upgrade
    
    print_success "POS System updated successfully!"
}

# Main script logic
case "$1" in
    "deploy")
        check_docker
        create_env_file
        deploy
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        stop
        ;;
    "status")
        status
        ;;
    "backup")
        backup
        ;;
    "restore")
        restore "$2"
        ;;
    "update")
        update
        ;;
    *)
        echo "POS System Docker Deployment Script"
        echo "Usage: $0 {deploy|logs|stop|status|backup|restore|update}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy the POS system with Docker"
        echo "  logs    - Show system logs"
        echo "  stop    - Stop all services"
        echo "  status  - Show service status"
        echo "  backup  - Create database backup"
        echo "  restore - Restore database from backup"
        echo "  update  - Update system with latest code"
        echo ""
        echo "Examples:"
        echo "  $0 deploy                           # Deploy the system"
        echo "  $0 backup                          # Create backup"
        echo "  $0 restore backups/backup.sql      # Restore from backup"
        exit 1
        ;;
esac