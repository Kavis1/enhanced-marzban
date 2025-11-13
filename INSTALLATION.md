# Enhanced Marzban Installation Guide

## 🚀 One-Line Installation

The Enhanced Marzban installation script provides a complete, automated deployment solution that installs and configures all components with minimal user intervention.

### Quick Installation

```bash
sudo bash -c "$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/main/install.sh)" @ install
```

### Installation with Custom Domain

```bash
sudo bash -c "$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/main/install.sh)" @ install --domain your-domain.com
```

### Silent Installation (No Prompts)

```bash
sudo bash -c "$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/main/install.sh)" @ install --silent
```

## 📋 What Gets Installed

### System Dependencies
- **Python 3.8+** with pip, venv, and development tools
- **PostgreSQL** database server with client tools
- **Redis** server for caching and session management
- **Nginx** web server with modern configuration
- **Fail2ban** intrusion prevention system
- **Certbot** for SSL certificate management
- **UFW/Firewalld** firewall configuration
- **Essential tools**: curl, wget, git, openssl, jq, htop

### Enhanced Marzban Components
- **Complete Enhanced Marzban** application from GitHub
- **Database setup** with all enhanced tables and migrations
- **Configuration files** with secure defaults
- **Systemd service** for automatic startup
- **Nginx configuration** with security headers and SSL
- **Fail2ban integration** with custom filters and actions
- **Management scripts** for easy administration

### Security Features
- **Random secure passwords** for admin and database
- **API tokens** for service integration
- **SSL certificates** (Let's Encrypt or self-signed)
- **Firewall rules** for required ports only
- **File permissions** set correctly for security
- **Log rotation** to prevent disk space issues

## 📊 Post-Installation

After successful installation, you'll see:

### Access Information
- **Web Panel URL**: https://your-domain-or-ip/dashboard/
- **API Documentation**: https://your-domain-or-ip/docs
- **Admin Username**: admin
- **Admin Password**: [randomly generated 16-character password]
- **API Token**: [randomly generated 32-character token]

### Important File Locations
- **Configuration**: `/opt/enhanced-marzban/.env`
- **Nginx Config**: `/etc/nginx/sites-available/enhanced-marzban`
- **Fail2ban Config**: `/etc/fail2ban/jail.local`
- **Action Script**: `/usr/local/bin/marzban-fail2ban-action.sh`
-_Log Files_*: `/var/log/marzban/`
- **Backups**: `/var/backups/marzban/`

### Service Management
```bash
# Using systemctl
systemctl start enhanced-marzban
systemctl stop enhanced-marzban
systemctl restart enhanced-marzban
systemctl status enhanced-marzban

# Using management script
/usr/local/bin/marzban-management start
/usr/local/bin/marzban-management stop
/usr/local/bin/marzban-management restart
/usr/local/bin/marzban-management status
/usr/local/bin/marzban-management logs
/usr/local/bin/marzban-management update
/usr/local/bin/marzban-management backup
/usr/local/bin/marzban-management health
```

## 🛠️ System Requirements

### Minimum Requirements
- **OS**: Any Linux distribution
- **RAM**: 2GB (4GB recommended)
- **Disk**: 10GB free space
- **Network**: Internet connection for package downloads
- **Access**: Root privileges (sudo)

### Recommended for Production
- **RAM**: 4GB or more
- **Disk**: 20GB+ SSD storage
- **CPU**: 2+ cores
- **Domain**: Registered domain name for SSL certificates
- **Firewall**: Properly configured network security

## 🚨 Troubleshooting

### Installation Fails
The script includes automatic rollback functionality. If installation fails:
1. Check the error message displayed
2. Review logs in `/var/log/marzban/install.log`
3. Ensure system meets requirements
4. Try running with `--silent` flag to avoid prompts

### Service Issues
```bash
# Check service status
systemctl status enhanced-marzban

# View logs
journalctl -u enhanced-marzban -f

# Check application health
/usr/local/bin/marzban-management health
```

### Network Issues
```bash
# Check firewall status
ufw status  # Ubuntu/Debian
firewall-cmd --list-all  # CentOS/RHEL

# Test web panel access
curl -k https://localhost:8000/api/enhanced/health
```

## 📞 Support

- **GitHub Issues**: [Create an issue](https://github.com/Kavis1/enhanced-marzban/issues)
- **Documentation**: [Project Wiki](https://github.com/Kavis1/enhanced-marzban/wiki)
- **Repository**: [Enhanced Marzban](https://github.com/Kavis1/enhanced-marzban)

## 🔄 Updates

To update Enhanced Marzban to the latest version:

```bash
/usr/local/bin/marzban-management update
```

Or manually:
```bash
cd /opt/enhanced-marzban
git pull origin main
pip3 install -r requirements.txt
systemctl restart enhanced-marzban
```

---

**Enhanced Marzban** - Advanced VPN panel with enterprise security features
