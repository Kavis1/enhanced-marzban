<p align="center">
  <a href="https://github.com/Kavis1/enhanced-marzban" target="_blank" rel="noopener noreferrer">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://github.com/Gozargah/Marzban-docs/raw/master/screenshots/logo-dark.png">
      <img width="160" height="160" src="https://github.com/Gozargah/Marzban-docs/raw/master/screenshots/logo-light.png">
    </picture>
  </a>
</p>

<h1 align="center">Enhanced Marzban</h1>

<p align="center">
    🚀 An enhanced version of Marzban with additional security and monitoring features
</p>

<p align="center">
    <strong>Powered by <a href="https://github.com/XTLS/Xray-core">Xray-core</a> | Based on <a href="https://github.com/Gozargah/Marzban">Original Marzban</a></strong>
</p>

<br/>
<p align="center">
    <a href="https://github.com/Kavis1/enhanced-marzban">
        <img src="https://img.shields.io/github/stars/Kavis1/enhanced-marzban?style=flat-square&logo=github" />
    </a>
    <a href="https://github.com/Kavis1/enhanced-marzban/releases">
        <img src="https://img.shields.io/github/v/release/Kavis1/enhanced-marzban?style=flat-square&logo=github" />
    </a>
    <a href="https://github.com/Kavis1/enhanced-marzban/blob/main/LICENSE">
        <img src="https://img.shields.io/github/license/Kavis1/enhanced-marzban?style=flat-square" />
    </a>
    <a href="https://github.com/Kavis1/enhanced-marzban/issues">
        <img src="https://img.shields.io/github/issues/Kavis1/enhanced-marzban?style=flat-square" />
    </a>
    <a href="https://github.com/Kavis1/enhanced-marzban/pulls">
        <img src="https://img.shields.io/github/issues-pr/Kavis1/enhanced-marzban?style=flat-square" />
    </a>
</p>

<p align="center">
  <a href="https://github.com/Kavis1/enhanced-marzban" target="_blank" rel="noopener noreferrer" >
    <img src="https://github.com/Gozargah/Marzban-docs/raw/master/screenshots/preview.png" alt="Enhanced Marzban screenshots" width="600" height="auto">
  </a>
</p>

## 🌟 What's new in Enhanced Marzban?

Enhanced Marzban is an extended version of the original Marzban project with the addition of enterprise security, monitoring, and user management features.</p>

## 📋 Table of Contents

- [🚀 Enhanced Features](#-enhanced-features)
- [⚡ Quick Installation](#-quick-installation)
- [🔧 Configuration](#-configuration)
- [📖 Documentation](#-documentation)
- [🔒 Security](#-security)
- [📊 Monitoring](#-monitoring)
- [🌐 API](#-api)
- [🤝 Support](#-support)
- [📄 License](#-license)

## 🚀 Enhanced Features

Enhanced Marzban includes all the features of the original Marzban plus additional enterprise capabilities:

### 🔐 Two-Factor Authentication (2FA)
- **Google Authenticator** compatible TOTP authentication
- **Backup codes** for access recovery
- **QR code generation** for easy setup
- **Individual 2FA setup** for each administrator
- **API endpoints** for 2FA management

### 🛡️ Fail2ban Integration
- **Real-time traffic monitoring**
- **Torrent traffic detection** based on protocol signatures
- **Suspicious activity analysis** (high load, frequent connections)
- **Automatic user blocking** via Fail2ban
- **Customizable violation thresholds** and blocking duration

### 🔗 Connection Limiting
- **Maximum of 5 simultaneous connections** per user (configurable)
- **IP-based tracking**
- **Real-time monitoring**
- **Automatic cleanup** of inactive connections
- **Individual limits** for each user

### 🌐 DNS Override and Redirection
- **Global DNS rules** for all users
- **Custom DNS rules**
- **Wildcard domain support** (*.example.com)
- **Priority processing** of rules
- **DNS caching** for improved performance

### 🚫 Ad-Blocking Integration
- **Support for multiple block lists** (EasyList, EasyPrivacy, etc.)
- **Automatic list updates**
- **User and node-level customization**
- **Custom blocked domains**
- **Domain blocking statistics**

### 📊 Enhanced Security and Monitoring
- **Tracking of administrator login attempts**
- **Session management** with 2FA verification
- **Performance metrics collection**
- **System status monitoring**
- **Comprehensive logging** with automatic cleanup

## ⚡ Quick Installation

### 🚀 Automatic Installation (Recommended)

Run the following command for automatic installation of Enhanced Marzban:

```bash
sudo bash -c "$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/main/install.sh)" @ install
```

### 📋 System Requirements

- **Any Linux system**
- **Python 3.8+**
- **2GB RAM** (minimum)
- **10GB of free disk space**
- **Root access** to the server

### 🎯 After Installation

1. **Access the panel:**
   - Web panel: `https://your-domain:8000/dashboard/`
   - API documentation: `https://your-domain:8000/docs`

## 🔧 Configuration

### 🔐 Basic Security Settings

Create a `.env` file with the following parameters:

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

# Ad Blocking
ADBLOCK_ENABLED=true
ADBLOCK_UPDATE_INTERVAL=86400
ADBLOCK_DEFAULT_LISTS="easylist,easyprivacy,malware"

# Performance and Cleanup
LOG_CLEANUP_ENABLED=true
LOG_RETENTION_DAYS=30
PERFORMANCE_MONITORING_ENABLED=true
```

## 📖 Documentation

### 🌐 API Endpoints

Enhanced Marzban provides an extended REST API for managing all features. To view the API documentation in Swagger UI or ReDoc, set `DOCS=True` in the configuration and go to `/docs` and `/redoc`.

## 🤝 Support

### 📞 Getting Help

- **GitHub Issues:** [Create an issue](https://github.com/Kavis1/enhanced-marzban/issues)
- **GitHub Discussions:** [Discussions](https://github.com/Kavis1/enhanced-marzban/discussions)
- **Documentation:** [Wiki](https://github.com/Kavis1/enhanced-marzban/wiki)

## 📄 License

Enhanced Marzban is distributed under the [AGPL-3.0](./LICENSE) license.

Based on the original [Marzban](https://github.com/Gozargah/Marzban) project from the Gozargah team.

---

<p align="center">
  <strong>Enhanced Marzban - Advanced security for your VPN</strong>
</p>

<p align="center">
  Made with ❤️ for the community
</p>
