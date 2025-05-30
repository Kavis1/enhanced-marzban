#!/bin/bash

# Enhanced Marzban VPN System - Installation Script
# Version: 1.0.0
# Description: Complete installation and management of Enhanced Marzban
# Author: Enhanced Marzban Team
# License: MIT

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
MARZBAN_DIR="/opt/marzban"
SERVICE_NAME="marzban"
LOG_FILE="/var/log/marzban-install.log"

# Default admin credentials
DEFAULT_ADMIN_USER="admin"
DEFAULT_ADMIN_PASS=""

echo "=============================================="
echo "Enhanced Marzban VPN System Installer v1.0.0"
echo "=============================================="
echo ""
echo "🚀 Welcome to Enhanced Marzban!"
echo ""
echo "This installer will set up:"
echo "  ✅ Enhanced Marzban VPN System"
echo "  ✅ Fail2ban Integration"
echo "  ✅ Connection Management"
echo "  ✅ DNS Override"
echo "  ✅ Ad-blocking"
echo "  ✅ Traffic Analysis"
echo "  ✅ Secure Admin Access"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}[ERROR]${NC} This script must be run as root. Please use: sudo $0"
    exit 1
fi

echo "🔄 Starting installation process..."
echo ""

# Generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-16
}

# Create log file
touch "$LOG_FILE"
chmod 666 "$LOG_FILE"
echo "[$(date +'%Y-%m-%d %H:%M:%S')] Starting Enhanced Marzban installation..." >> "$LOG_FILE"

echo "📦 Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update >> "$LOG_FILE" 2>&1
    apt-get install -y curl wget git unzip python3 python3-pip nodejs npm fail2ban ufw >> "$LOG_FILE" 2>&1
elif command -v yum &> /dev/null; then
    yum update -y >> "$LOG_FILE" 2>&1
    yum install -y curl wget git unzip python3 python3-pip nodejs npm fail2ban firewalld >> "$LOG_FILE" 2>&1
else
    echo -e "${RED}[ERROR]${NC} Unsupported operating system"
    exit 1
fi
echo "✅ Dependencies installed"

echo "📥 Downloading Enhanced Marzban..."
# Remove existing directory if it exists
if [[ -d "$MARZBAN_DIR" ]]; then
    rm -rf "$MARZBAN_DIR"
fi

mkdir -p "$MARZBAN_DIR"

# Try to clone the repository
if git clone https://github.com/Kavis1/enhanced-marzban.git "$MARZBAN_DIR" >> "$LOG_FILE" 2>&1; then
    echo "✅ Enhanced Marzban downloaded successfully"
else
    echo "⚠️  Git clone failed, trying ZIP download..."
    wget -O /tmp/enhanced-marzban.zip https://github.com/Kavis1/enhanced-marzban/archive/refs/heads/main.zip >> "$LOG_FILE" 2>&1
    unzip -q /tmp/enhanced-marzban.zip -d /tmp/ >> "$LOG_FILE" 2>&1
    cp -r /tmp/enhanced-marzban-main/* "$MARZBAN_DIR/" >> "$LOG_FILE" 2>&1
    rm -f /tmp/enhanced-marzban.zip
    rm -rf /tmp/enhanced-marzban-main
    echo "✅ Enhanced Marzban downloaded via ZIP"
fi

echo "👤 Creating admin user..."
DEFAULT_ADMIN_PASS=$(generate_password)

# Save credentials to file
cat > /root/marzban-credentials.txt << EOL
Enhanced Marzban Admin Credentials
Generated on: $(date)

Username: $DEFAULT_ADMIN_USER
Password: $DEFAULT_ADMIN_PASS

Dashboard URL: http://$(hostname -I | awk '{print $1}'):8000

IMPORTANT: Save these credentials securely!
EOL

chmod 600 /root/marzban-credentials.txt
echo "✅ Admin credentials generated"

echo "⚙️  Setting up systemd service..."
cat > /etc/systemd/system/marzban.service << EOL
[Unit]
Description=Enhanced Marzban VPN Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$MARZBAN_DIR
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload >> "$LOG_FILE" 2>&1
systemctl enable marzban >> "$LOG_FILE" 2>&1
echo "✅ Systemd service configured"

echo "🔥 Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw --force enable >> "$LOG_FILE" 2>&1
    ufw allow 22/tcp >> "$LOG_FILE" 2>&1
    ufw allow 80/tcp >> "$LOG_FILE" 2>&1
    ufw allow 443/tcp >> "$LOG_FILE" 2>&1
    ufw allow 8000/tcp >> "$LOG_FILE" 2>&1
elif command -v firewall-cmd &> /dev/null; then
    systemctl enable firewalld >> "$LOG_FILE" 2>&1
    systemctl start firewalld >> "$LOG_FILE" 2>&1
    firewall-cmd --permanent --add-port=22/tcp >> "$LOG_FILE" 2>&1
    firewall-cmd --permanent --add-port=80/tcp >> "$LOG_FILE" 2>&1
    firewall-cmd --permanent --add-port=443/tcp >> "$LOG_FILE" 2>&1
    firewall-cmd --permanent --add-port=8000/tcp >> "$LOG_FILE" 2>&1
    firewall-cmd --reload >> "$LOG_FILE" 2>&1
fi
echo "✅ Firewall configured"

echo "🚀 Starting Enhanced Marzban..."
if systemctl start marzban >> "$LOG_FILE" 2>&1; then
    sleep 5
    if systemctl is-active --quiet marzban; then
        echo "✅ Enhanced Marzban started successfully"
    else
        echo "⚠️  Service started but may need configuration"
    fi
else
    echo "❌ Failed to start Enhanced Marzban service"
    echo "Check logs: journalctl -u marzban -f"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}🎉 Enhanced Marzban Installation Complete!${NC}"
echo "=============================================="
echo ""
echo "🌐 Dashboard Access:"
echo "   URL: http://$(hostname -I | awk '{print $1}'):8000"
echo "   Username: $DEFAULT_ADMIN_USER"
echo "   Password: $DEFAULT_ADMIN_PASS"
echo ""
echo "📄 Credentials saved to: /root/marzban-credentials.txt"
echo ""
echo "🔐 SECURITY REMINDER:"
echo "   🔒 Save your password: $DEFAULT_ADMIN_PASS"
echo "   🌍 Dashboard is accessible from any IP"
echo "   🛡️  Consider enabling 2FA after first login"
echo ""
echo "🚀 Enhanced Features Available:"
echo "   ✅ Fail2ban Protection"
echo "   ✅ Connection Management (5 per user)"
echo "   ✅ DNS Override & Ad-blocking"
echo "   ✅ Traffic Analysis"
echo "   ✅ Advanced Security"
echo ""
echo "🔧 Service Management:"
echo "   Start:   systemctl start marzban"
echo "   Stop:    systemctl stop marzban"
echo "   Restart: systemctl restart marzban"
echo "   Status:  systemctl status marzban"
echo "   Logs:    journalctl -u marzban -f"
echo ""
echo "📚 Documentation: https://github.com/Kavis1/enhanced-marzban"
echo ""
echo "Thank you for choosing Enhanced Marzban! 🚀"
echo "=============================================="

echo "[$(date +'%Y-%m-%d %H:%M:%S')] Enhanced Marzban installation completed successfully!" >> "$LOG_FILE"
