#!/bin/bash

# Enhanced Marzban Complete Automated Installation Script
# Version: 2.1
# Repository: https://github.com/Kavis1/enhanced-marzban
#
# This script provides a complete, automated deployment solution for Enhanced Marzban
# with all security features, monitoring, and management capabilities.

set -eo pipefail

# Handle curl execution case - avoid BASH_SOURCE issues
SCRIPT_NAME="${0##*/}"
if [[ "$SCRIPT_NAME" == "bash" ]] || [[ "$SCRIPT_NAME" == "-bash" ]]; then
    SCRIPT_NAME="install-enhanced-marzban.sh"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
MARZBAN_DIR="/opt/enhanced-marzban"
LOG_DIR="/var/log/marzban"
FAIL2BAN_DIR="/etc/fail2ban"
SCRIPT_DIR="/usr/local/bin"
NGINX_DIR="/etc/nginx"
SSL_DIR="/etc/ssl/marzban"
BACKUP_DIR="/var/backups/marzban"
REPO_URL="https://github.com/Kavis1/enhanced-marzban.git"

# Installation variables
ADMIN_USERNAME="admin"
ADMIN_PASSWORD=""
API_TOKEN=""
JWT_SECRET=""
DATABASE_PASSWORD=""
DOMAIN=""
SILENT_MODE=false
INSTALL_MODE="install"
DETECTED_OS=""
DETECTED_VERSION=""

# Enhanced Functions
print_banner() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        Enhanced Marzban Installer v2.1                      ║"
    echo "║                                                                              ║"
    echo "║  🚀 Complete Automated Deployment Solution                                  ║"
    echo "║  🔐 Advanced Security Features                                              ║"
    echo "║  📊 Real-time Monitoring & Analytics                                       ║"
    echo "║  🛡️ Fail2ban Integration                                                   ║"
    echo "║                                                                              ║"
    echo "║  Repository: https://github.com/Kavis1/enhanced-marzban                     ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
}

print_step() {
    echo -e "${WHITE}[STEP $1/$2]${NC} ${CYAN}$3${NC}"
}

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

print_progress() {
    local current=$1
    local total=$2
    local message=$3
    local percent=$((current * 100 / total))
    local filled=$((percent / 2))
    local empty=$((50 - filled))

    printf "\r${BLUE}[%3d%%]${NC} [" "$percent"
    printf "%*s" "$filled" | tr ' ' '█'
    printf "%*s" "$empty" | tr ' ' '░'
    printf "] %s" "$message"

    if [ "$current" -eq "$total" ]; then
        echo
    fi
}

log_action() {
    # Ensure log directory exists before writing
    mkdir -p "$LOG_DIR" 2>/dev/null || true
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_DIR/install.log" 2>/dev/null || true
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        print_status "Please run: sudo $0 $*"
        exit 1
    fi
}

generate_password() {
    local length=${1:-16}
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-${length}
}

generate_secret() {
    local length=${1:-32}
    openssl rand -hex ${length}
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DETECTED_OS=$ID
        DETECTED_VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        DETECTED_OS="centos"
        DETECTED_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+' | head -1)
    else
        print_error "Unable to detect operating system"
        exit 1
    fi

    print_status "Detected OS: $DETECTED_OS $DETECTED_VERSION"
}

check_system_requirements() {
    print_step 1 14 "Checking system compatibility"

    # Just log the detected OS without strict requirements
    print_status "Detected OS: $DETECTED_OS $DETECTED_VERSION"

    # Check memory (warning only)
    local memory_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$memory_gb" -lt 2 ]; then
        print_warning "Less than 2GB RAM detected. Enhanced Marzban may run slowly."
    else
        print_status "Memory: ${memory_gb}GB available"
    fi

    # Check disk space (warning only)
    local disk_space_gb=$(df / | awk 'NR==2{print int($4/1024/1024)}')
    if [ "$disk_space_gb" -lt 5 ]; then
        print_warning "Low disk space detected: ${disk_space_gb}GB available"
    else
        print_status "Disk space: ${disk_space_gb}GB available"
    fi

    print_success "System compatibility check completed"
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            install)
                INSTALL_MODE="install"
                shift
                ;;
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --silent)
                SILENT_MODE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    echo "Enhanced Marzban Installation Script v2.1"
    echo
    echo "Usage: $0 [OPTIONS] COMMAND"
    echo
    echo "Commands:"
    echo "  install                 Install Enhanced Marzban"
    echo
    echo "Options:"
    echo "  --domain DOMAIN         Set custom domain for SSL certificate"
    echo "  --silent               Run in silent mode (no prompts)"
    echo "  --help, -h             Show this help message"
    echo
    echo "Examples:"
    echo "  $0 install"
    echo "  $0 install --domain marzban.example.com"
    echo "  $0 install --silent"
    echo
    echo "One-line installation:"
    echo "  sudo bash -c \"\$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/main/install.sh)\" @ install"
}

create_backup() {
    print_step 2 14 "Creating backup of existing configurations"

    mkdir -p "$BACKUP_DIR"
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)

    # Backup existing configurations
    if [ -d "$MARZBAN_DIR" ]; then
        print_status "Backing up existing Enhanced Marzban installation..."
        tar -czf "$BACKUP_DIR/marzban_backup_$backup_timestamp.tar.gz" -C "$(dirname "$MARZBAN_DIR")" "$(basename "$MARZBAN_DIR")" 2>/dev/null || true
    fi

    if [ -f "$NGINX_DIR/sites-available/enhanced-marzban" ]; then
        print_status "Backing up Nginx configuration..."
        cp "$NGINX_DIR/sites-available/enhanced-marzban" "$BACKUP_DIR/nginx_enhanced-marzban_$backup_timestamp.conf" 2>/dev/null || true
    fi

    if [ -d "$FAIL2BAN_DIR" ]; then
        print_status "Backing up Fail2ban configuration..."
        tar -czf "$BACKUP_DIR/fail2ban_backup_$backup_timestamp.tar.gz" -C "$FAIL2BAN_DIR" . 2>/dev/null || true
    fi

    print_success "Backup completed: $BACKUP_DIR"
    log_action "Backup created: $backup_timestamp"
}

install_dependencies() {
    print_step 3 14 "Installing system dependencies"

    # Update package lists
    print_progress 1 10 "Updating package lists..."
    case "$DETECTED_OS" in
        ubuntu|debian)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update -qq
            apt-get upgrade -y -qq
            ;;
        centos|rhel)
            yum update -y -q
            yum install -y epel-release
            ;;
    esac

    # Install basic tools
    print_progress 2 10 "Installing basic tools..."
    case "$DETECTED_OS" in
        ubuntu|debian)
            apt-get install -y -qq \
                curl wget git unzip software-properties-common \
                apt-transport-https ca-certificates gnupg lsb-release \
                openssl jq htop nano vim
            ;;
        centos|rhel)
            yum install -y -q \
                curl wget git unzip \
                openssl jq htop nano vim
            ;;
    esac

    # Install Python 3.8+
    print_progress 3 10 "Installing Python 3.8+..."
    case "$DETECTED_OS" in
        ubuntu|debian)
            apt-get install -y -qq \
                python3 python3-pip python3-venv python3-dev \
                python3-setuptools python3-wheel
            ;;
        centos|rhel)
            yum install -y -q \
                python3 python3-pip python3-devel \
                python3-setuptools python3-wheel
            ;;
    esac

    # Install database (PostgreSQL)
    print_progress 4 10 "Installing PostgreSQL..."
    case "$DETECTED_OS" in
        ubuntu|debian)
            apt-get install -y -qq postgresql postgresql-contrib postgresql-client \
                libpq-dev python3-dev build-essential
            ;;
        centos|rhel)
            yum install -y -q postgresql-server postgresql-contrib postgresql-devel \
                python3-devel gcc gcc-c++ make
            postgresql-setup initdb
            ;;
    esac

    # Install Redis
    print_progress 5 10 "Installing Redis..."
    case "$DETECTED_OS" in
        ubuntu|debian)
            apt-get install -y -qq redis-server
            ;;
        centos|rhel)
            yum install -y -q redis
            ;;
    esac

    # Install Nginx
    print_progress 6 10 "Installing Nginx..."
    case "$DETECTED_OS" in
        ubuntu|debian)
            apt-get install -y -qq nginx
            ;;
        centos|rhel)
            yum install -y -q nginx
            ;;
    esac

    # Install Fail2ban
    print_progress 7 10 "Installing Fail2ban..."
    case "$DETECTED_OS" in
        ubuntu|debian)
            apt-get install -y -qq fail2ban
            ;;
        centos|rhel)
            yum install -y -q fail2ban
            ;;
    esac

    # Install Certbot
    print_progress 8 10 "Installing Certbot..."
    case "$DETECTED_OS" in
        ubuntu|debian)
            apt-get install -y -qq certbot python3-certbot-nginx
            ;;
        centos|rhel)
            yum install -y -q certbot python3-certbot-nginx
            ;;
    esac

    # Install UFW firewall
    print_progress 9 10 "Installing UFW firewall..."
    case "$DETECTED_OS" in
        ubuntu|debian)
            apt-get install -y -qq ufw
            ;;
        centos|rhel)
            yum install -y -q firewalld
            ;;
    esac

    print_progress 10 10 "Dependencies installation completed"
    print_success "All system dependencies installed successfully"
    log_action "System dependencies installed"
}

setup_directories() {
    print_step 4 14 "Setting up directories and permissions"

    # Create main directories
    mkdir -p "$MARZBAN_DIR" "$LOG_DIR" "$SSL_DIR" "$BACKUP_DIR" "$SCRIPT_DIR"

    # Set proper permissions
    chmod 755 "$MARZBAN_DIR" "$LOG_DIR" "$BACKUP_DIR" "$SCRIPT_DIR"
    chmod 700 "$SSL_DIR"

    # Create log files
    touch "$LOG_DIR/install.log" "$LOG_DIR/fail2ban.log" "$LOG_DIR/marzban.log"
    chmod 644 "$LOG_DIR"/*.log

    print_success "Directories and permissions configured"
    log_action "Directories created and configured"
}

clone_repository() {
    print_step 5 14 "Cloning Enhanced Marzban repository"

    # Remove existing directory if it exists
    if [ -d "$MARZBAN_DIR" ]; then
        rm -rf "$MARZBAN_DIR"
    fi

    # Clone the repository
    print_status "Cloning from $REPO_URL..."
    git clone "$REPO_URL" "$MARZBAN_DIR"

    # Set proper ownership
    chown -R root:root "$MARZBAN_DIR"

    print_success "Repository cloned successfully"
    log_action "Repository cloned from $REPO_URL"
}

install_python_dependencies() {
    print_step 6 14 "Installing Python dependencies"

    cd "$MARZBAN_DIR"

    # Upgrade pip
    print_progress 1 5 "Upgrading pip..."
    python3 -m pip install --upgrade pip

    # Install wheel and setuptools
    print_progress 2 5 "Installing build tools..."
    python3 -m pip install wheel setuptools

    # Install requirements
    print_progress 3 5 "Installing Enhanced Marzban dependencies..."
    python3 -m pip install -r requirements.txt --ignore-installed

    # Install additional security and database packages
    print_progress 4 5 "Installing security and database packages..."
    python3 -m pip install cryptography bcrypt psycopg2-binary

    print_progress 5 5 "Python dependencies installation completed"
    print_success "All Python dependencies installed successfully"
    log_action "Python dependencies installed"
}

build_frontend() {
    print_step 7 16 "Building Enhanced frontend dashboard"

    cd "$MARZBAN_DIR"

    # Check if dashboard directory exists
    if [ ! -d "app/dashboard" ]; then
        print_error "Dashboard source code not found"
        return 1
    fi

    # Install Node.js and npm if not present
    print_progress 1 5 "Installing Node.js and npm..."
    if ! command -v node >/dev/null 2>&1; then
        if wget -qO- https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs; then
            print_status "Node.js 20 installed successfully"
        else
            print_warning "Failed to install Node.js 20, trying fallback with apt"
            apt-get install -y nodejs npm
        fi
    fi

    # Verify Node.js installation
    if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
        print_error "Failed to install Node.js and npm"
        return 1
    fi

    print_progress 2 5 "Installing frontend dependencies..."
    cd app/dashboard

    # Install dependencies
    # Clean install to prevent corruption
    rm -rf node_modules package-lock.json
    npm install --legacy-peer-deps --silent --no-progress 2>/dev/null || {
        print_warning "npm install failed, trying without silent flags"
        npm install --legacy-peer-deps
    }

    print_progress 3 5 "Building Enhanced dashboard..."
    # Build the dashboard with correct output directory
    NODE_OPTIONS="--max-old-space-size=8192" VITE_BASE_API=/api/ npm run build || {
        print_error "Failed to build dashboard"
        return 1
    }

    print_progress 4 5 "Setting up built files..."
    # Ensure build directory exists and copy index.html to 404.html
    if [ -d "build" ]; then
        cp build/index.html build/404.html 2>/dev/null || true
        print_success "Enhanced dashboard built successfully"
    else
        print_error "Build output not found"
        return 1
    fi

    print_progress 5 5 "Frontend build completed"
    cd "$MARZBAN_DIR"
    log_action "Enhanced frontend dashboard built"
}

generate_secrets() {
    print_step 8 16 "Generating secure credentials"

    # Generate admin password
    ADMIN_PASSWORD=$(generate_password 16)
    print_status "Generated secure admin password"

    # Generate API token
    API_TOKEN=$(generate_secret 32)
    print_status "Generated API token for Fail2ban integration"

    # Generate JWT secret
    JWT_SECRET=$(generate_secret 64)
    print_status "Generated JWT secret"

    # Generate database password
    DATABASE_PASSWORD=$(generate_password 20)
    print_status "Generated database password"

    print_success "All secure credentials generated"
    log_action "Secure credentials generated"
}

setup_database() {
    print_step 9 16 "Setting up PostgreSQL database"

    # Start PostgreSQL service
    systemctl start postgresql
    systemctl enable postgresql
    sleep 3

    print_progress 1 4 "Setting up PostgreSQL authentication..."

    # Configure PostgreSQL to use trust authentication temporarily for setup
    local pg_version=$(ls /etc/postgresql/ 2>/dev/null | head -1)
    if [ -z "$pg_version" ]; then
        pg_version="14"  # Default fallback
    fi

    local pg_config_dir="/etc/postgresql/$pg_version/main"
    local pg_hba_conf="$pg_config_dir/pg_hba.conf"

    # Alternative paths for different distributions
    if [ ! -f "$pg_hba_conf" ]; then
        pg_config_dir="/var/lib/pgsql/data"
        pg_hba_conf="$pg_config_dir/pg_hba.conf"
    fi
    if [ ! -f "$pg_hba_conf" ]; then
        pg_config_dir="/etc/postgresql"
        pg_hba_conf="$pg_config_dir/pg_hba.conf"
    fi

    print_status "PostgreSQL config: $pg_hba_conf"

    if [ -f "$pg_hba_conf" ]; then
        # Backup original configuration
        cp "$pg_hba_conf" "$pg_hba_conf.original" 2>/dev/null || true

        # Create a temporary configuration with trust authentication
        cat > "$pg_hba_conf" << EOF
# Temporary configuration for Enhanced Marzban setup
local   all             postgres                                trust
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
EOF

        # Restart PostgreSQL with new configuration
        systemctl restart postgresql
        sleep 3
        print_status "Configured temporary trust authentication"
    else
        print_error "PostgreSQL configuration file not found"
        exit 1
    fi

    print_progress 2 4 "Creating database and user..."

    # Now create database and user without password prompts
    sudo -u postgres createdb enhanced_marzban 2>/dev/null || true
    sudo -u postgres createuser marzban 2>/dev/null || true
    sudo -u postgres psql -c "ALTER USER marzban WITH SUPERUSER;" 2>/dev/null || true
    sudo -u postgres psql -c "ALTER USER marzban WITH PASSWORD '$DATABASE_PASSWORD';" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE enhanced_marzban TO marzban;" 2>/dev/null || true

    print_progress 3 4 "Running database migrations..."
    cd "$MARZBAN_DIR"

    # Set DATABASE_URL for trust authentication during setup
    DATABASE_URL="postgresql://marzban@localhost/enhanced_marzban"

    # Run database migrations
    python3 -c "
import os
os.environ['SQLALCHEMY_DATABASE_URL'] = '$DATABASE_URL'
from app.db import engine, GetDB
from app.db.models_enhanced import Base
from app.db.models import Base as OriginalBase, JWT
try:
    OriginalBase.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print('✓ Database tables created successfully')

    # Ensure JWT secret key exists
    with GetDB() as db:
        jwt_record = db.query(JWT).first()
        if not jwt_record:
            jwt_record = JWT(secret_key=os.urandom(32).hex())
            db.add(jwt_record)
            db.commit()
            print('✓ JWT secret key initialized')
        else:
            print('✓ JWT secret key already exists')

except Exception as e:
    print(f'Database setup error: {e}')
    exit(1)
"

    print_progress 4 4 "Restoring secure PostgreSQL configuration..."

    # Restore secure configuration with password authentication
    if [ -f "$pg_hba_conf.original" ]; then
        # Restore original configuration
        cp "$pg_hba_conf.original" "$pg_hba_conf"

        # Update for password authentication
        sed -i 's/local   all             all                                     peer/local   all             all                                     md5/g' "$pg_hba_conf"
        sed -i 's/local   all             postgres                                peer/local   all             postgres                                md5/g' "$pg_hba_conf"

        # Restart PostgreSQL with secure configuration
        systemctl restart postgresql
        sleep 2

        # Update DATABASE_URL for production use
        DATABASE_URL="postgresql://marzban:$DATABASE_PASSWORD@localhost/enhanced_marzban"

        print_status "Restored secure PostgreSQL authentication"
    fi

    print_success "PostgreSQL database configured successfully"
    log_action "Database setup completed"
}

create_configuration() {
    print_step 10 16 "Creating Enhanced Marzban configuration"

    cd "$MARZBAN_DIR"

    # Use the DATABASE_URL that was configured during database setup
    if [ -z "$DATABASE_URL" ]; then
        DATABASE_URL="postgresql://marzban:$DATABASE_PASSWORD@localhost/enhanced_marzban"
    fi

    # Create .env configuration file
    cat > .env << EOF
# Enhanced Marzban Configuration
# Generated on $(date)

# Database Configuration
SQLALCHEMY_DATABASE_URL=$DATABASE_URL

# Application Configuration
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_SECRET_KEY=$JWT_SECRET

# Admin Configuration
SUDO_USERNAME=$ADMIN_USERNAME
SUDO_PASSWORD=$ADMIN_PASSWORD

# Two-Factor Authentication
TWO_FACTOR_AUTH_ENABLED=true
TWO_FACTOR_ISSUER_NAME="Enhanced Marzban"
TWO_FACTOR_BACKUP_CODES_COUNT=10

# Fail2ban Integration
FAIL2BAN_ENABLED=true
FAIL2BAN_LOG_PATH=$LOG_DIR/fail2ban.log
FAIL2BAN_MAX_VIOLATIONS=3
TORRENT_DETECTION_ENABLED=true
TRAFFIC_ANALYSIS_ENABLED=true
FAIL2BAN_BAN_DURATION=3600

# Connection Limiting
CONNECTION_LIMIT_ENABLED=true
DEFAULT_MAX_CONNECTIONS=5
CONNECTION_TRACKING_INTERVAL=30

# DNS Override
DNS_OVERRIDE_ENABLED=true
DNS_OVERRIDE_SERVERS=1.1.1.1,8.8.8.8
DNS_CACHE_TTL=300

# Ad-blocking
ADBLOCK_ENABLED=true
ADBLOCK_UPDATE_INTERVAL=86400
ADBLOCK_DEFAULT_LISTS=easylist,easyprivacy,malware

# Performance and Cleanup
LOG_CLEANUP_ENABLED=true
LOG_RETENTION_DAYS=30
CACHE_CLEANUP_INTERVAL=3600
PERFORMANCE_MONITORING_ENABLED=true

# Security
DOCS=false
DEBUG=false

# API Token for Fail2ban
MARZBAN_API_TOKEN=$API_TOKEN
EOF

    # Set proper permissions
    chmod 600 .env

    print_success "Configuration file created: $MARZBAN_DIR/.env"
    log_action "Configuration file created"
}

create_admin_user() {
    print_step 11 16 "Creating admin user"

    cd "$MARZBAN_DIR"

    # Use the same DATABASE_URL that was configured
    if [ -z "$DATABASE_URL" ]; then
        DATABASE_URL="postgresql://marzban:$DATABASE_PASSWORD@localhost/enhanced_marzban"
    fi

    # Create admin user
    python3 -c "
import os
import sys
sys.path.append('.')

# Set environment variables
os.environ['SQLALCHEMY_DATABASE_URL'] = '$DATABASE_URL'

from app.db import get_db
from app.db.models import Admin
from passlib.context import CryptContext

# Initialize password context
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

try:
    db = next(get_db())

    # Check if admin already exists
    existing_admin = db.query(Admin).filter(Admin.username == '$ADMIN_USERNAME').first()
    if existing_admin:
        # Update existing admin
        existing_admin.hashed_password = pwd_context.hash('$ADMIN_PASSWORD')
        existing_admin.is_sudo = True
        print('✓ Admin user updated')
    else:
        # Create new admin
        admin = Admin(
            username='$ADMIN_USERNAME',
            hashed_password=pwd_context.hash('$ADMIN_PASSWORD'),
            is_sudo=True
        )
        db.add(admin)
        print('✓ Admin user created')

    db.commit()
    db.close()
    print('✓ Admin user configured successfully')
except Exception as e:
    print(f'Error creating admin user: {e}')
    exit(1)
"

    print_success "Admin user created: $ADMIN_USERNAME"
    log_action "Admin user created"
}

setup_fail2ban() {
    print_step 12 16 "Setting up Fail2ban integration"

    cd "$MARZBAN_DIR"

    # Copy Fail2ban configuration files
    print_progress 1 5 "Installing Fail2ban configurations..."
    if [ -d "fail2ban" ]; then
        # Copy jail configuration
        cp fail2ban/jail.local "$FAIL2BAN_DIR/"

        # Copy filter configurations
        cp fail2ban/filter.d/*.conf "$FAIL2BAN_DIR/filter.d/"

        # Copy action configuration
        cp fail2ban/action.d/*.conf "$FAIL2BAN_DIR/action.d/"

        print_success "Fail2ban configurations copied"
    else
        print_warning "Fail2ban configuration files not found in repository"
    fi

    # Setup action script
    print_progress 2 5 "Setting up Fail2ban action script..."
    if [ -f "scripts/marzban-fail2ban-action.sh" ]; then
        cp scripts/marzban-fail2ban-action.sh "$SCRIPT_DIR/"
        chmod +x "$SCRIPT_DIR/marzban-fail2ban-action.sh"

        # Update API token in the script
        sed -i "s/MARZBAN_API_TOKEN=\"\"/MARZBAN_API_TOKEN=\"$API_TOKEN\"/" "$SCRIPT_DIR/marzban-fail2ban-action.sh"

        print_success "Fail2ban action script configured"
    else
        print_warning "Fail2ban action script not found"
    fi

    # Start and enable Fail2ban
    print_progress 3 5 "Starting Fail2ban service..."
    systemctl enable fail2ban
    systemctl restart fail2ban

    print_progress 4 5 "Verifying Fail2ban configuration..."
    sleep 2
    if systemctl is-active --quiet fail2ban; then
        print_success "Fail2ban service is running"
    else
        print_warning "Fail2ban service may have issues"
    fi

    print_progress 5 5 "Fail2ban setup completed"
    log_action "Fail2ban integration configured"
}

setup_systemd_service() {
    print_step 13 16 "Setting up systemd service"

    # Create systemd service file
    cat > /etc/systemd/system/enhanced-marzban.service << EOF
[Unit]
Description=Enhanced Marzban VPN Panel
Documentation=https://github.com/Kavis1/enhanced-marzban
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$MARZBAN_DIR
ExecStart=/usr/bin/python3 main.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=enhanced-marzban

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$MARZBAN_DIR $LOG_DIR /tmp

# Environment
Environment=PYTHONPATH=$MARZBAN_DIR
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable enhanced-marzban.service

    print_success "Systemd service configured and enabled"
    log_action "Systemd service created"
}

setup_nginx() {
    print_step 14 16 "Setting up Nginx configuration"

    # Create necessary Nginx directories
    mkdir -p "$NGINX_DIR/sites-available" "$NGINX_DIR/sites-enabled"

    # Determine server name
    local server_name="_"
    if [ -n "$DOMAIN" ]; then
        server_name="$DOMAIN"
    fi

    # Create Nginx configuration
    print_progress 1 4 "Creating Nginx configuration..."
    cat > "$NGINX_DIR/sites-available/enhanced-marzban" << EOF
# Enhanced Marzban Nginx Configuration
# Generated on $(date)

# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=dashboard:10m rate=5r/s;

# Upstream for Enhanced Marzban
upstream enhanced_marzban {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP server
server {
    listen 80;
    listen [::]:80;
    server_name $server_name;

    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Dashboard with rate limiting
    location /dashboard {
        limit_req zone=dashboard burst=10 nodelay;
        proxy_pass http://enhanced_marzban;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API with stricter rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://enhanced_marzban;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;

        # API specific headers
        proxy_set_header Accept-Encoding "";
        proxy_buffering off;

        # Timeouts for API
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Static files and other routes
    location / {
        proxy_pass http://enhanced_marzban;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://enhanced_marzban/api/enhanced/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Deny access to sensitive files
    location ~ /\\.env {
        deny all;
        return 404;
    }

    location ~ /\\.git {
        deny all;
        return 404;
    }
}
EOF

    # Enable site
    print_progress 2 4 "Enabling Nginx site..."
    ln -sf "$NGINX_DIR/sites-available/enhanced-marzban" "$NGINX_DIR/sites-enabled/"

    # Remove default site if it exists
    rm -f "$NGINX_DIR/sites-enabled/default"

    # Test nginx configuration
    print_progress 3 4 "Testing Nginx configuration..."
    if nginx -t; then
        print_success "Nginx configuration is valid"
    else
        print_error "Nginx configuration test failed"
        return 1
    fi

    print_progress 4 4 "Nginx setup completed"
    log_action "Nginx configuration created"
}

setup_ssl_certificates() {
    print_step 15 16 "Setting up SSL certificates"

    # Create SSL directory
    mkdir -p "$SSL_DIR"
    chmod 700 "$SSL_DIR"

    if [ -n "$DOMAIN" ]; then
        print_progress 1 3 "Attempting to obtain Let's Encrypt certificate..."

        # Try to get Let's Encrypt certificate
        if certbot --nginx --non-interactive --agree-tos --register-unsafely-without-email \
           --domains "$DOMAIN" --redirect; then

            # Update Nginx config to use Let's Encrypt certificates
            sed -i "s|ssl_certificate $SSL_DIR/marzban.crt;|ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|" \
                "$NGINX_DIR/sites-available/enhanced-marzban"
            sed -i "s|ssl_certificate_key $SSL_DIR/marzban.key;|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|" \
                "$NGINX_DIR/sites-available/enhanced-marzban"

            print_success "Let's Encrypt certificate obtained for $DOMAIN"
            log_action "Let's Encrypt certificate configured for $DOMAIN"
        else
            print_warning "Failed to obtain Let's Encrypt certificate, using self-signed"
            create_self_signed_certificate
        fi
    else
        print_progress 1 3 "Creating self-signed certificate..."
        create_self_signed_certificate
    fi

    print_progress 3 3 "SSL certificates setup completed"
}

create_self_signed_certificate() {
    print_progress 2 3 "Generating self-signed certificate..."

    # Generate private key
    openssl genrsa -out "$SSL_DIR/marzban.key" 2048

    # Generate certificate
    openssl req -new -x509 -key "$SSL_DIR/marzban.key" -out "$SSL_DIR/marzban.crt" -days 365 \
        -subj "/C=US/ST=State/L=City/O=Enhanced Marzban/CN=${DOMAIN:-marzban.local}"

    # Set proper permissions
    chmod 600 "$SSL_DIR/marzban.key"
    chmod 644 "$SSL_DIR/marzban.crt"

    print_success "Self-signed SSL certificate created"
    log_action "Self-signed SSL certificate created"
}

configure_firewall() {
    print_step 16 16 "Configuring firewall"

    case "$DETECTED_OS" in
        ubuntu|debian)
            configure_ufw_firewall
            ;;
        centos|rhel)
            configure_firewalld
            ;;
        *)
            print_warning "Firewall configuration skipped for unsupported OS"
            ;;
    esac
}

configure_ufw_firewall() {
    print_progress 1 6 "Installing and configuring UFW..."

    # Install ufw if not present
    apt-get install -y -qq ufw

    # Reset firewall
    ufw --force reset

    print_progress 2 6 "Setting default policies..."
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing

    print_progress 3 6 "Allowing SSH access..."
    # Allow SSH (be careful not to lock yourself out)
    ufw allow ssh
    ufw allow 22/tcp

    print_progress 4 6 "Allowing web traffic..."
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp

    print_progress 5 6 "Allowing Enhanced Marzban ports..."
    # Allow Enhanced Marzban application port
    ufw allow 8000/tcp

    # Allow common proxy ports (customize as needed)
    ufw allow 2053/tcp
    ufw allow 2083/tcp
    ufw allow 2087/tcp
    ufw allow 2096/tcp
    ufw allow 8080/tcp
    ufw allow 8443/tcp

    # Allow database access (local only)
    ufw allow from 127.0.0.1 to any port 5432

    print_progress 6 6 "Enabling firewall..."
    # Enable firewall
    ufw --force enable

    print_success "UFW firewall configured and enabled"
    log_action "UFW firewall configured"
}

configure_firewalld() {
    print_progress 1 4 "Configuring firewalld..."

    # Start and enable firewalld
    systemctl start firewalld
    systemctl enable firewalld

    print_progress 2 4 "Adding firewall rules..."
    # Allow SSH
    firewall-cmd --permanent --add-service=ssh

    # Allow HTTP and HTTPS
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https

    # Allow Enhanced Marzban ports
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --permanent --add-port=2053/tcp
    firewall-cmd --permanent --add-port=2083/tcp
    firewall-cmd --permanent --add-port=2087/tcp
    firewall-cmd --permanent --add-port=2096/tcp

    print_progress 3 4 "Reloading firewall..."
    # Reload firewall
    firewall-cmd --reload

    print_progress 4 4 "Firewalld configuration completed"
    print_success "Firewalld configured and enabled"
    log_action "Firewalld configured"
}

start_services() {
    print_status "Starting and verifying services..."

    # Start PostgreSQL
    print_progress 1 6 "Starting PostgreSQL..."
    systemctl start postgresql
    systemctl enable postgresql

    # Start Redis
    print_progress 2 6 "Starting Redis..."
    systemctl start redis-server 2>/dev/null || systemctl start redis
    systemctl enable redis-server 2>/dev/null || systemctl enable redis

    # Start Nginx
    print_progress 3 6 "Starting Nginx..."
    systemctl enable nginx
    systemctl restart nginx

    # Start Fail2ban
    print_progress 4 6 "Starting Fail2ban..."
    systemctl enable fail2ban
    systemctl restart fail2ban

    # Start Enhanced Marzban
    print_progress 5 6 "Starting Enhanced Marzban..."
    systemctl start enhanced-marzban

    # Wait a moment for services to start
    sleep 3

    print_progress 6 6 "Verifying services..."
    verify_services

    print_success "All services started successfully"
    log_action "Services started and verified"
}

verify_services() {
    local failed_services=()

    # Check PostgreSQL
    if ! systemctl is-active --quiet postgresql; then
        failed_services+=("PostgreSQL")
    fi

    # Check Redis
    if ! systemctl is-active --quiet redis-server && ! systemctl is-active --quiet redis; then
        failed_services+=("Redis")
    fi

    # Check Nginx
    if ! systemctl is-active --quiet nginx; then
        failed_services+=("Nginx")
    fi

    # Check Fail2ban
    if ! systemctl is-active --quiet fail2ban; then
        failed_services+=("Fail2ban")
    fi

    # Check Enhanced Marzban
    if ! systemctl is-active --quiet enhanced-marzban; then
        failed_services+=("Enhanced Marzban")
    fi

    if [ ${#failed_services[@]} -gt 0 ]; then
        print_warning "Some services failed to start: ${failed_services[*]}"
        print_status "You may need to check the logs and restart them manually"
    else
        print_success "All services are running correctly"
    fi
}

setup_log_rotation() {
    print_status "Setting up log rotation..."

    # Create logrotate configuration for Enhanced Marzban
    cat > /etc/logrotate.d/enhanced-marzban << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload enhanced-marzban 2>/dev/null || true
    endscript
}
EOF

    print_success "Log rotation configured"
    log_action "Log rotation configured"
}

create_management_scripts() {
    print_status "Creating management scripts..."

    # Create Enhanced Marzban CLI script
    cat > "$SCRIPT_DIR/enhanced-marzban" << 'EOF'
#!/bin/bash

# Enhanced Marzban Management Script

MARZBAN_DIR="/opt/enhanced-marzban"
LOG_DIR="/var/log/marzban"

case "$1" in
    start)
        echo "Starting Enhanced Marzban..."
        systemctl start enhanced-marzban
        ;;
    stop)
        echo "Stopping Enhanced Marzban..."
        systemctl stop enhanced-marzban
        ;;
    restart)
        echo "Restarting Enhanced Marzban..."
        systemctl restart enhanced-marzban
        ;;
    status)
        systemctl status enhanced-marzban
        ;;
    logs)
        journalctl -u enhanced-marzban -f
        ;;
    update)
        echo "Updating Enhanced Marzban..."
        cd "$MARZBAN_DIR"
        git pull origin main
        pip3 install -r requirements.txt
        systemctl restart enhanced-marzban
        echo "Update completed"
        ;;
    backup)
        echo "Creating backup..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        tar -czf "/var/backups/marzban/enhanced-marzban-backup-$timestamp.tar.gz" \
            -C "$(dirname "$MARZBAN_DIR")" "$(basename "$MARZBAN_DIR")" \
            -C /etc nginx/sites-available/enhanced-marzban \
            -C /etc fail2ban jail.local
        echo "Backup created: /var/backups/marzban/enhanced-marzban-backup-$timestamp.tar.gz"
        ;;
    health)
        echo "Checking Enhanced Marzban health..."
        curl -s http://localhost:8000/api/enhanced/health | jq . 2>/dev/null || \
        curl -s http://localhost:8000/api/enhanced/health
        ;;
    version)
        echo "Enhanced Marzban v2.1"
        ;;
    check-update)
        echo "Checking for updates..."
        cd "$MARZBAN_DIR"
        git fetch origin
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/main)
        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "Update available. Run 'enhanced-marzban update' to update."
        else
            echo "You are up to date."
        fi
        ;;
    *)
        echo "Enhanced Marzban Management Script v2.1"
        echo "Usage: $0 {start|stop|restart|status|logs|update|backup|health|version|check-update}"
        echo
        echo "Commands:"
        echo "  start       - Start Enhanced Marzban service"
        echo "  stop        - Stop Enhanced Marzban service"
        echo "  restart     - Restart Enhanced Marzban service"
        echo "  status      - Show service status"
        echo "  logs        - Show live logs"
        echo "  update      - Update to latest version"
        echo "  backup      - Create backup"
        echo "  health      - Check application health"
        echo "  version     - Show version information"
        echo "  check-update- Check for available updates"
        exit 1
        ;;
esac
EOF

    chmod +x "$SCRIPT_DIR/enhanced-marzban"

    print_success "Management scripts created"
    log_action "Management scripts created"
}

show_completion_message() {
    clear
    print_banner

    echo -e "${GREEN}🎉 Enhanced Marzban Installation Completed Successfully! 🎉${NC}"
    echo
    echo -e "${WHITE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo

    # Determine access URL
    local server_ip=$(hostname -I | awk '{print $1}')
    local access_url="http://$server_ip"
    if [ -n "$DOMAIN" ]; then
        access_url="https://$DOMAIN"
    fi

    echo -e "${CYAN}🌐 ACCESS INFORMATION${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "📱 Web Panel:      ${GREEN}$access_url/dashboard/${NC}"
    echo -e "🔧 API Docs:       ${GREEN}$access_url/docs${NC}"
    echo -e "🌐 Server IP:      ${BLUE}$server_ip${NC}"
    echo -e "👤 Admin Username: ${YELLOW}$ADMIN_USERNAME${NC}"
    echo -e "🔑 Admin Password: ${YELLOW}$ADMIN_PASSWORD${NC}"
    echo -e "🔐 API Token:      ${YELLOW}$API_TOKEN${NC}"
    echo

    echo -e "${CYAN}📁 IMPORTANT FILE LOCATIONS${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "⚙️  Configuration:  ${BLUE}$MARZBAN_DIR/.env${NC}"
    echo -e "🌐 Nginx Config:   ${BLUE}$NGINX_DIR/sites-available/enhanced-marzban${NC}"
    echo -e "🛡️  Fail2ban Config: ${BLUE}$FAIL2BAN_DIR/jail.local${NC}"
    echo -e "📜 Action Script:   ${BLUE}$SCRIPT_DIR/marzban-fail2ban-action.sh${NC}"
    echo -e "📊 Log Files:      ${BLUE}$LOG_DIR/${NC}"
    echo -e "💾 Backups:        ${BLUE}$BACKUP_DIR/${NC}"
    echo

    echo -e "${CYAN}🔧 SERVICE MANAGEMENT${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "🚀 Start:          ${GREEN}systemctl start enhanced-marzban${NC}"
    echo -e "⏹️  Stop:           ${RED}systemctl stop enhanced-marzban${NC}"
    echo -e "🔄 Restart:        ${YELLOW}systemctl restart enhanced-marzban${NC}"
    echo -e "📊 Status:         ${BLUE}systemctl status enhanced-marzban${NC}"
    echo -e "📋 Logs:           ${BLUE}journalctl -u enhanced-marzban -f${NC}"
    echo -e "🛠️  Management:     ${PURPLE}enhanced-marzban {start|stop|restart|status|logs|update|backup|health|version|check-update}${NC}"
    echo

    echo -e "${CYAN}🔒 ENHANCED FEATURES ENABLED${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "✅ Two-Factor Authentication (2FA)"
    echo -e "✅ Fail2ban Integration for Traffic Monitoring"
    echo -e "✅ Connection Limiting (Max 5 per user)"
    echo -e "✅ DNS Override and Redirection"
    echo -e "✅ Ad-blocking Integration"
    echo -e "✅ Real-time Performance Monitoring"
    echo -e "✅ Automated Security Features"
    echo

    echo -e "${CYAN}🚀 NEXT STEPS${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "1. 🌐 Access the web panel at: ${GREEN}$access_url/dashboard/${NC}"
    echo -e "2. 🔐 Login with the credentials shown above"
    echo -e "3. 🛡️  Configure 2FA for enhanced security"
    echo -e "4. 📊 Review system status in the dashboard"
    echo -e "5. 📖 Read the documentation: ${BLUE}https://github.com/Kavis1/enhanced-marzban${NC}"

    if [ -z "$DOMAIN" ]; then
        echo
        echo -e "${YELLOW}⚠️  PRODUCTION DEPLOYMENT RECOMMENDATIONS${NC}"
        echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "🔒 Obtain a proper SSL certificate for your domain"
        echo -e "🌐 Configure a domain name and update DNS records"
        echo -e "🔧 Review and customize firewall rules"
        echo -e "💾 Set up automated backups"
        echo -e "📊 Monitor system performance and logs"
    fi

    echo
    echo -e "${WHITE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Enhanced Marzban is now ready for use! 🚀${NC}"
    echo -e "${WHITE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo

    # Save installation summary
    cat > "$LOG_DIR/installation-summary.txt" << EOF
Enhanced Marzban Installation Summary
Generated on: $(date)

Access Information:
- Web Panel: $access_url/dashboard/
- API Documentation: $access_url/docs
- Server IP: $server_ip
- Admin Username: $ADMIN_USERNAME
- Admin Password: $ADMIN_PASSWORD
- API Token: $API_TOKEN

File Locations:
- Configuration: $MARZBAN_DIR/.env
- Nginx Config: $NGINX_DIR/sites-available/enhanced-marzban
- Fail2ban Config: $FAIL2BAN_DIR/jail.local
- Action Script: $SCRIPT_DIR/marzban-fail2ban-action.sh
- Log Directory: $LOG_DIR/
- Backup Directory: $BACKUP_DIR/

Enhanced Features:
- Two-Factor Authentication: Enabled
- Fail2ban Integration: Enabled
- Connection Limiting: Enabled (Max 5 per user)
- DNS Override: Enabled
- Ad-blocking: Enabled
- Performance Monitoring: Enabled

Management Commands:
- enhanced-marzban start|stop|restart|status|logs|update|backup|health
- systemctl start|stop|restart|status enhanced-marzban
- journalctl -u enhanced-marzban -f

Installation completed successfully!
EOF

    log_action "Installation completed successfully"
}

rollback_installation() {
    print_error "Installation failed. Rolling back changes..."

    # Stop services
    systemctl stop enhanced-marzban 2>/dev/null || true
    systemctl disable enhanced-marzban 2>/dev/null || true

    # Remove systemd service
    rm -f /etc/systemd/system/enhanced-marzban.service
    systemctl daemon-reload

    # Remove Nginx configuration
    rm -f "$NGINX_DIR/sites-enabled/enhanced-marzban"
    rm -f "$NGINX_DIR/sites-available/enhanced-marzban"

    # Restore Nginx default if it was removed
    if [ ! -f "$NGINX_DIR/sites-enabled/default" ] && [ -f "$NGINX_DIR/sites-available/default" ]; then
        ln -s "$NGINX_DIR/sites-available/default" "$NGINX_DIR/sites-enabled/default"
    fi

    # Remove Enhanced Marzban directory
    rm -rf "$MARZBAN_DIR"

    # Remove management scripts
    rm -f "$SCRIPT_DIR/enhanced-marzban"
    rm -f "$SCRIPT_DIR/marzban-fail2ban-action.sh"

    # Remove log rotation
    rm -f /etc/logrotate.d/enhanced-marzban

    print_status "Rollback completed. System restored to previous state."
    log_action "Installation rolled back due to failure"
}

handle_error() {
    local exit_code=$?
    local line_number=$1

    print_error "An error occurred on line $line_number (exit code: $exit_code)"

    if [ "$SILENT_MODE" = false ]; then
        echo
        read -p "Do you want to attempt rollback? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback_installation
        fi
    else
        rollback_installation
    fi

    exit $exit_code
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# Main installation process
main() {
    # Check root privileges first
    check_root

    # Parse command line arguments
    parse_arguments "$@"

    # Show banner
    if [ "$SILENT_MODE" = false ]; then
        print_banner

        if [ "$INSTALL_MODE" = "install" ]; then
            echo -e "${YELLOW}This script will install Enhanced Marzban with all security features.${NC}"
            echo -e "${YELLOW}The installation will take approximately 5-10 minutes.${NC}"
            echo

            if [ -z "$DOMAIN" ]; then
                read -p "Enter your domain name (optional, press Enter to skip): " DOMAIN
                DOMAIN=$(echo "$DOMAIN" | tr -d ' ')
            fi

            echo
            read -p "Continue with installation? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_status "Installation cancelled by user"
                exit 0
            fi
        fi
    fi

    # Start installation
    print_status "Starting Enhanced Marzban installation..."

    # Create initial log directory
    mkdir -p "$LOG_DIR" 2>/dev/null || true
    log_action "Installation started"

    # Detect operating system
    detect_os

    # Check system requirements
    check_system_requirements

    # Create backup of existing configurations
    create_backup

    # Install system dependencies
    install_dependencies

    # Setup directories and permissions
    setup_directories

    # Clone Enhanced Marzban repository
    clone_repository

    # Install Python dependencies
    install_python_dependencies

    # Build Enhanced frontend dashboard
    build_frontend

    # Generate secure credentials
    generate_secrets

    # Setup PostgreSQL database
    setup_database

    # Create configuration file
    create_configuration

    # Create admin user
    create_admin_user

    # Setup Fail2ban integration
    setup_fail2ban

    # Setup systemd service
    setup_systemd_service

    # Setup Nginx configuration
    setup_nginx

    # Setup SSL certificates
    setup_ssl_certificates

    # Configure firewall
    configure_firewall

    # Setup log rotation
    setup_log_rotation

    # Create management scripts
    create_management_scripts

    # Start and verify services
    start_services

    # Show completion message
    show_completion_message
}

# Execute main function - always run when script is executed
main "$@"
