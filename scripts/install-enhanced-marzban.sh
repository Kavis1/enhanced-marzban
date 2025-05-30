#!/bin/bash

# Enhanced Marzban Installation Script
# This script installs and configures all enhanced features

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MARZBAN_DIR="/opt/marzban"
LOG_DIR="/var/log/marzban"
FAIL2BAN_DIR="/etc/fail2ban"
SCRIPT_DIR="/usr/local/bin"

# Functions
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

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

install_dependencies() {
    print_status "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3-pip \
        python3-venv \
        fail2ban \
        curl \
        wget \
        git \
        nginx \
        certbot \
        python3-certbot-nginx
    
    print_success "System dependencies installed"
}

install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Navigate to Marzban directory
    cd "$MARZBAN_DIR"
    
    # Install enhanced dependencies
    pip3 install -r requirements.txt
    
    print_success "Python dependencies installed"
}

setup_directories() {
    print_status "Setting up directories..."
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    chmod 755 "$LOG_DIR"
    
    # Create fail2ban log file
    touch "$LOG_DIR/fail2ban.log"
    chmod 644 "$LOG_DIR/fail2ban.log"
    
    # Create script directory if it doesn't exist
    mkdir -p "$SCRIPT_DIR"
    
    print_success "Directories created"
}

setup_fail2ban() {
    print_status "Setting up Fail2ban integration..."
    
    # Copy Fail2ban configuration files
    if [ -d "fail2ban" ]; then
        # Copy jail configuration
        cp fail2ban/jail.local "$FAIL2BAN_DIR/"
        
        # Copy filter configurations
        cp fail2ban/filter.d/*.conf "$FAIL2BAN_DIR/filter.d/"
        
        # Copy action configuration
        cp fail2ban/action.d/*.conf "$FAIL2BAN_DIR/action.d/"
        
        # Copy and setup action script
        cp scripts/marzban-fail2ban-action.sh "$SCRIPT_DIR/"
        chmod +x "$SCRIPT_DIR/marzban-fail2ban-action.sh"
        
        print_success "Fail2ban configuration installed"
    else
        print_warning "Fail2ban configuration files not found"
    fi
}

setup_database() {
    print_status "Setting up database migrations..."
    
    cd "$MARZBAN_DIR"
    
    # Run database migrations
    python3 -c "
from app.db import engine
from app.db.models_enhanced import Base
Base.metadata.create_all(bind=engine)
print('Enhanced database tables created')
"
    
    print_success "Database migrations completed"
}

setup_systemd_service() {
    print_status "Setting up systemd service..."
    
    cat > /etc/systemd/system/enhanced-marzban.service << EOF
[Unit]
Description=Enhanced Marzban VPN Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$MARZBAN_DIR
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=3
Environment=PYTHONPATH=$MARZBAN_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable enhanced-marzban.service
    
    print_success "Systemd service configured"
}

setup_nginx() {
    print_status "Setting up Nginx configuration..."
    
    cat > /etc/nginx/sites-available/enhanced-marzban << EOF
server {
    listen 80;
    server_name _;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;
    
    # SSL configuration (update with your certificates)
    ssl_certificate /etc/ssl/certs/marzban.crt;
    ssl_certificate_key /etc/ssl/private/marzban.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Proxy to Marzban
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # API rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Rate limiting zone
http {
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/enhanced-marzban /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    nginx -t
    
    print_success "Nginx configuration created"
}

setup_ssl_certificates() {
    print_status "Setting up SSL certificates..."
    
    # Create self-signed certificates for initial setup
    mkdir -p /etc/ssl/private
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/marzban.key \
        -out /etc/ssl/certs/marzban.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=marzban.local"
    
    chmod 600 /etc/ssl/private/marzban.key
    chmod 644 /etc/ssl/certs/marzban.crt
    
    print_success "Self-signed SSL certificates created"
    print_warning "Replace with proper SSL certificates in production"
}

configure_firewall() {
    print_status "Configuring firewall..."
    
    # Install ufw if not present
    apt-get install -y ufw
    
    # Reset firewall
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow Marzban ports (customize as needed)
    ufw allow 8000/tcp
    ufw allow 2053/tcp
    ufw allow 2083/tcp
    ufw allow 2087/tcp
    ufw allow 2096/tcp
    
    # Enable firewall
    ufw --force enable
    
    print_success "Firewall configured"
}

start_services() {
    print_status "Starting services..."
    
    # Start and enable Fail2ban
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    # Start and enable Nginx
    systemctl enable nginx
    systemctl restart nginx
    
    # Start Enhanced Marzban
    systemctl start enhanced-marzban
    
    print_success "Services started"
}

show_completion_message() {
    print_success "Enhanced Marzban installation completed!"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Update the configuration in config.py"
    echo "2. Set up your admin account"
    echo "3. Configure SSL certificates for production"
    echo "4. Update Fail2ban action script with API token"
    echo "5. Test all enhanced features"
    echo
    echo -e "${BLUE}Service management:${NC}"
    echo "- Start: systemctl start enhanced-marzban"
    echo "- Stop: systemctl stop enhanced-marzban"
    echo "- Status: systemctl status enhanced-marzban"
    echo "- Logs: journalctl -u enhanced-marzban -f"
    echo
    echo -e "${BLUE}Access:${NC}"
    echo "- Web Panel: https://your-domain/"
    echo "- API: https://your-domain/api/"
    echo
    echo -e "${YELLOW}Important:${NC}"
    echo "- Update MARZBAN_API_TOKEN in $SCRIPT_DIR/marzban-fail2ban-action.sh"
    echo "- Configure proper SSL certificates"
    echo "- Review and customize firewall rules"
}

# Main installation process
main() {
    print_status "Starting Enhanced Marzban installation..."
    
    check_root
    install_dependencies
    setup_directories
    install_python_dependencies
    setup_database
    setup_fail2ban
    setup_systemd_service
    setup_nginx
    setup_ssl_certificates
    configure_firewall
    start_services
    show_completion_message
}

# Run main function
main "$@"
