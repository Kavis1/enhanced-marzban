#!/bin/bash

# Enhanced Marzban VPN System - Uninstaller
# Version: 1.0.0

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=============================================="
echo "Enhanced Marzban VPN System Uninstaller v1.0.0"
echo "=============================================="
echo ""

# Check if running in non-interactive mode (piped from curl)
if [[ ! -t 0 ]] || [[ ! -t 1 ]]; then
    echo -e "${YELLOW}Detected non-interactive mode (piped execution)${NC}"
    echo -e "${YELLOW}Enabling automatic removal...${NC}"
    FORCE_REMOVE=true
    echo ""
else
    FORCE_REMOVE=false
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}[ERROR]${NC} This script must be run as root. Please use: sudo $0"
    exit 1
fi

echo -e "${RED}⚠️  WARNING: This will remove Enhanced Marzban and all its components!${NC}"
echo ""
echo "Components to be removed:"
echo "  • Enhanced Marzban Service"
echo "  • Application Directory (/opt/marzban)"
echo "  • Configuration Files"
echo "  • Log Files"
echo "  • System Service"
echo ""

if [[ "$FORCE_REMOVE" != "true" ]]; then
    read -p "Are you sure you want to proceed? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Uninstallation cancelled."
        exit 0
    fi
fi

echo ""
echo "🗑️  Removing Enhanced Marzban..."

# Stop and disable service
echo "🛑 Stopping services..."
systemctl stop marzban 2>/dev/null || true
systemctl disable marzban 2>/dev/null || true

# Remove service file
if [[ -f "/etc/systemd/system/marzban.service" ]]; then
    rm -f /etc/systemd/system/marzban.service
    echo "✅ Removed systemd service"
fi

systemctl daemon-reload

# Remove application directory
if [[ -d "/opt/marzban" ]]; then
    rm -rf /opt/marzban
    echo "✅ Removed application directory"
fi

# Remove configuration files
rm -rf /etc/marzban 2>/dev/null || true
echo "✅ Removed configuration files"

# Remove log files
rm -rf /var/log/marzban* 2>/dev/null || true
echo "✅ Removed log files"

# Remove credentials file
rm -f /root/marzban-credentials.txt 2>/dev/null || true
echo "✅ Removed credentials file"

echo ""
echo "=============================================="
echo -e "${GREEN}Enhanced Marzban Removal Complete!${NC}"
echo "=============================================="
echo ""
echo "🗑️  Removed Components:"
echo "   ✓ Enhanced Marzban Service"
echo "   ✓ Application Directory"
echo "   ✓ Configuration Files"
echo "   ✓ Log Files"
echo "   ✓ System Service"
echo ""
echo "🎯 Enhanced Marzban has been completely removed from your system."
echo ""

# Self-destruct
echo "🔥 Self-destructing uninstall script..."
sleep 2
rm -f "${BASH_SOURCE[0]}"
echo "✅ Uninstall script removed."
