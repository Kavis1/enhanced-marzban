# Enhanced Marzban - Advanced VPN Panel

This is an enhanced version of the original [Marzban](https://github.com/Gozargah/Marzban) project with additional security, monitoring, and management features.

## 🚀 Enhanced Features

### 1. Two-Factor Authentication (2FA)
- **Google Authenticator** compatible TOTP authentication
- **Backup codes** for account recovery
- **Per-admin** 2FA configuration
- **QR code generation** for easy setup
- **API endpoints** for 2FA management

### 2. Fail2ban Integration
- **Traffic monitoring** with automatic violation detection
- **Torrent traffic detection** using protocol signatures
- **Suspicious activity analysis** (high bandwidth, rapid connections)
- **Automatic user suspension** through Fail2ban
- **Configurable violation thresholds**
- **Integration with system firewall**

### 3. Connection Limiting
- **Maximum 5 simultaneous connections** per user (configurable)
- **IP-based connection tracking**
- **Real-time connection monitoring**
- **Automatic connection cleanup**
- **Per-user connection limits**
- **Connection violation logging**

### 4. DNS Override/Redirection
- **Global DNS rules** for all users
- **User-specific DNS rules**
- **Domain wildcard support** (*.example.com)
- **Priority-based rule processing**
- **DNS caching** for performance
- **XRay integration** for seamless operation

### 5. Ad-blocking Integration
- **Multiple ad-block lists** support (EasyList, EasyPrivacy, etc.)
- **Automatic list updates**
- **Per-user ad-blocking** configuration
- **Per-node ad-blocking** for Marzban nodes
- **Custom blocked domains** per user
- **Domain blocking statistics**

### 6. Enhanced Security & Monitoring
- **Admin login attempt tracking**
- **Session management** with 2FA verification
- **Performance metrics** collection
- **System health monitoring**
- **Comprehensive logging**
- **Automatic log cleanup**

## 📋 Requirements

- **Python 3.8+**
- **PostgreSQL/MySQL/SQLite** (database)
- **Redis** (optional, for caching)
- **Fail2ban** (for traffic monitoring)
- **Nginx** (recommended for production)

## 🛠 Installation

### Quick Installation

```bash
# Clone the enhanced repository
git clone https://github.com/your-repo/enhanced-marzban.git
cd enhanced-marzban

# Run the installation script
sudo chmod +x scripts/install-enhanced-marzban.sh
sudo ./scripts/install-enhanced-marzban.sh
```

### Manual Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Setup database:**
```bash
python -c "from app.db import engine; from app.db.models_enhanced import Base; Base.metadata.create_all(bind=engine)"
```

3. **Configure Fail2ban:**
```bash
# Copy configuration files
sudo cp fail2ban/jail.local /etc/fail2ban/
sudo cp fail2ban/filter.d/*.conf /etc/fail2ban/filter.d/
sudo cp fail2ban/action.d/*.conf /etc/fail2ban/action.d/
sudo cp scripts/marzban-fail2ban-action.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/marzban-fail2ban-action.sh

# Restart Fail2ban
sudo systemctl restart fail2ban
```

4. **Start the application:**
```bash
python main.py
```

## ⚙️ Configuration

### Environment Variables

Add these to your `.env` file or environment:

```bash
# Two-Factor Authentication
TWO_FACTOR_AUTH_ENABLED=true
TWO_FACTOR_ISSUER_NAME="Enhanced Marzban"
TWO_FACTOR_BACKUP_CODES_COUNT=10

# Fail2ban Integration
FAIL2BAN_ENABLED=true
FAIL2BAN_LOG_PATH="/var/log/marzban/fail2ban.log"
FAIL2BAN_MAX_VIOLATIONS=3
TORRENT_DETECTION_ENABLED=true
TRAFFIC_ANALYSIS_ENABLED=true

# Connection Limiting
CONNECTION_LIMIT_ENABLED=true
DEFAULT_MAX_CONNECTIONS=5
CONNECTION_TRACKING_INTERVAL=30

# DNS Override
DNS_OVERRIDE_ENABLED=true
DNS_OVERRIDE_SERVERS="1.1.1.1,8.8.8.8"
DNS_CACHE_TTL=300

# Ad-blocking
ADBLOCK_ENABLED=true
ADBLOCK_UPDATE_INTERVAL=86400
ADBLOCK_DEFAULT_LISTS="easylist,easyprivacy,malware"

# Performance and Cleanup
LOG_CLEANUP_ENABLED=true
LOG_RETENTION_DAYS=30
PERFORMANCE_MONITORING_ENABLED=true
```

### Fail2ban Configuration

Update the API token in the action script:
```bash
sudo nano /usr/local/bin/marzban-fail2ban-action.sh
# Set MARZBAN_API_TOKEN="your-admin-api-token"
```

## 🔧 API Endpoints

### Two-Factor Authentication
- `GET /api/2fa/status` - Get 2FA status
- `POST /api/2fa/setup` - Setup 2FA
- `POST /api/2fa/verify-setup` - Verify and enable 2FA
- `POST /api/2fa/disable` - Disable 2FA
- `GET /api/2fa/backup-codes` - Get backup codes

### Fail2ban Integration
- `GET /api/fail2ban/status` - Get service status
- `GET /api/fail2ban/statistics` - Get violation statistics
- `GET /api/fail2ban/violations` - List violations
- `POST /api/fail2ban/action` - Handle ban/unban actions

### DNS Management
- `GET /api/dns/rules` - Get global DNS rules
- `POST /api/dns/rules` - Create DNS rule
- `GET /api/dns/users/{user_id}/rules` - Get user DNS rules
- `POST /api/dns/resolve` - Test domain resolution

### Ad-blocking
- `GET /api/adblock/lists` - Get ad-block lists
- `POST /api/adblock/lists` - Create ad-block list
- `GET /api/adblock/users/{user_id}/settings` - Get user settings
- `POST /api/adblock/check-domain` - Check if domain is blocked

### Enhanced Services
- `GET /api/enhanced/status` - Get all services status
- `GET /api/enhanced/health` - Health check
- `GET /api/enhanced/overview` - Services overview

## 🎛 Web Panel Features

### Admin Dashboard
- **Enhanced service status** monitoring
- **2FA setup and management**
- **Violation tracking** and resolution
- **Connection monitoring** per user
- **DNS rule management**
- **Ad-block configuration**

### User Management
- **Connection limits** per user
- **Custom DNS rules** per user
- **Ad-blocking preferences**
- **Violation history**
- **Traffic analysis**

### System Monitoring
- **Real-time metrics**
- **Service health status**
- **Performance graphs**
- **Log viewing**
- **Alert management**

## 🔒 Security Features

### Enhanced Authentication
- **2FA for all admin accounts**
- **Session management** with timeout
- **Login attempt tracking**
- **IP-based access control**

### Traffic Monitoring
- **Real-time connection tracking**
- **Torrent detection** with protocol analysis
- **Bandwidth monitoring**
- **Suspicious activity detection**

### Automated Protection
- **Fail2ban integration** for automatic banning
- **Connection limit enforcement**
- **Rate limiting** on API endpoints
- **DDoS protection** through Nginx

## 📊 Monitoring & Analytics

### Performance Metrics
- **Connection statistics**
- **Bandwidth usage**
- **Service response times**
- **Error rates**

### Health Monitoring
- **Service availability**
- **Database performance**
- **Memory and CPU usage**
- **Disk space monitoring**

### Alerting
- **Email notifications** for violations
- **Webhook integration**
- **Telegram bot** support
- **Custom alert rules**

## 🚀 Performance Optimizations

### Database
- **Connection pooling**
- **Query optimization**
- **Index optimization**
- **Automatic cleanup**

### Caching
- **DNS query caching**
- **User session caching**
- **Configuration caching**
- **Redis integration**

### Network
- **HTTP/2 support**
- **Gzip compression**
- **Static file caching**
- **CDN integration**

## 🔧 Maintenance

### Log Management
```bash
# View service logs
journalctl -u enhanced-marzban -f

# View Fail2ban logs
tail -f /var/log/marzban/fail2ban.log

# Cleanup old logs
find /var/log/marzban -name "*.log" -mtime +30 -delete
```

### Database Maintenance
```bash
# Backup database
pg_dump marzban > backup_$(date +%Y%m%d).sql

# Cleanup old records
python -c "from app.services.cleanup import cleanup_old_records; cleanup_old_records()"
```

### Service Management
```bash
# Restart services
sudo systemctl restart enhanced-marzban
sudo systemctl restart fail2ban
sudo systemctl restart nginx

# Check service status
sudo systemctl status enhanced-marzban
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original [Marzban](https://github.com/Gozargah/Marzban) project
- [Fail2ban](https://github.com/fail2ban/fail2ban) for traffic monitoring
- [EasyList](https://easylist.to/) for ad-blocking lists
- Community contributors and testers

## 📞 Support

- **Documentation:** [Wiki](https://github.com/your-repo/enhanced-marzban/wiki)
- **Issues:** [GitHub Issues](https://github.com/your-repo/enhanced-marzban/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-repo/enhanced-marzban/discussions)
- **Telegram:** [@enhanced_marzban](https://t.me/enhanced_marzban)
