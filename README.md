<p align="center">
  <a href="https://github.com/Kavis1/enhanced-marzban" target="_blank" rel="noopener noreferrer">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://github.com/Gozargah/Marzban-docs/raw/master/screenshots/logo-dark.png">
      <img width="160" height="160" src="https://github.com/Gozargah/Marzban-docs/raw/master/screenshots/logo-light.png">
    </picture>
  </a>
</p>

<h1 align="center"/>Enhanced Marzban</h1>

<p align="center">
    🚀 Расширенная версия Marzban с дополнительными функциями безопасности и мониторинга
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

## 🌟 Что нового в Enhanced Marzban?

Enhanced Marzban - это расширенная версия оригинального проекта Marzban с добавлением корпоративных функций безопасности, мониторинга и управления пользователями.</p>

## 📋 Содержание

- [🚀 Расширенные функции](#-расширенные-функции)
- [⚡ Быстрая установка](#-быстрая-установка)
- [🔧 Конфигурация](#-конфигурация)
- [📖 Документация](#-документация)
- [🔒 Безопасность](#-безопасность)
- [📊 Мониторинг](#-мониторинг)
- [🌐 API](#-api)
- [🤝 Поддержка](#-поддержка)
- [📄 Лицензия](#-лицензия)

## 🚀 Расширенные функции

Enhanced Marzban включает все функции оригинального Marzban плюс дополнительные корпоративные возможности:

### 🔐 Двухфакторная аутентификация (2FA)
- **Google Authenticator** совместимая TOTP аутентификация
- **Резервные коды** для восстановления доступа
- **QR-код генерация** для простой настройки
- **Индивидуальная настройка** 2FA для каждого администратора
- **API эндпоинты** для управления 2FA

### 🛡️ Интеграция с Fail2ban
- **Мониторинг трафика** в реальном времени
- **Обнаружение торрент-трафика** по сигнатурам протоколов
- **Анализ подозрительной активности** (высокая нагрузка, частые подключения)
- **Автоматическая блокировка** пользователей через Fail2ban
- **Настраиваемые пороги** нарушений и длительность блокировки

### 🔗 Ограничение подключений
- **Максимум 5 одновременных подключений** на пользователя (настраивается)
- **Отслеживание по IP-адресам**
- **Мониторинг в реальном времени**
- **Автоматическая очистка** неактивных подключений
- **Индивидуальные лимиты** для каждого пользователя

### 🌐 DNS переопределение и перенаправление
- **Глобальные DNS правила** для всех пользователей
- **Пользовательские DNS правила**
- **Поддержка wildcard доменов** (*.example.com)
- **Приоритетная обработка** правил
- **DNS кэширование** для повышения производительности

### 🚫 Интеграция блокировки рекламы
- **Поддержка множественных списков** блокировки (EasyList, EasyPrivacy и др.)
- **Автоматическое обновление** списков
- **Настройка на уровне пользователя** и узла
- **Пользовательские заблокированные домены**
- **Статистика блокировки** доменов

### 📊 Расширенная безопасность и мониторинг
- **Отслеживание попыток входа** администраторов
- **Управление сессиями** с верификацией 2FA
- **Сбор метрик производительности**
- **Мониторинг состояния системы**
- **Комплексное логирование** с автоматической очисткой

## ⚡ Быстрая установка

### 🚀 Автоматическая установка (Рекомендуется)

Запустите следующую команду для автоматической установки Enhanced Marzban:

```bash
sudo bash -c "$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/main/install.sh)" @ install
```

### 📋 Системные требования

- **Ubuntu 20.04+** или **Debian 11+**
- **Python 3.8+**
- **2GB RAM** (минимум)
- **10GB свободного места** на диске
- **Root доступ** к серверу

### 🔧 Ручная установка

Если вы предпочитаете ручную установку:

```bash
# 1. Установите зависимости
sudo apt update
sudo apt install -y python3-pip python3-venv fail2ban curl wget git nginx

# 2. Клонируйте репозиторий
git clone https://github.com/Kavis1/enhanced-marzban.git
cd enhanced-marzban

# 3. Установите Python зависимости
pip3 install -r requirements.txt

# 4. Настройте базу данных
python3 -c "from app.db import engine; from app.db.models_enhanced import Base; Base.metadata.create_all(bind=engine)"

# 5. Настройте Fail2ban
sudo cp fail2ban/jail.local /etc/fail2ban/
sudo cp fail2ban/filter.d/*.conf /etc/fail2ban/filter.d/
sudo cp fail2ban/action.d/*.conf /etc/fail2ban/action.d/
sudo cp scripts/marzban-fail2ban-action.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/marzban-fail2ban-action.sh

# 6. Запустите приложение
python3 main.py
```

### 🎯 После установки

1. **Создайте администратора:**
```bash
python3 -c "
from app.db import get_db
from app.models.admin import Admin
from app.utils.system import hash_password
db = next(get_db())
admin = Admin(username='admin', hashed_password=hash_password('your_password'), is_sudo=True)
db.add(admin)
db.commit()
print('Администратор создан: admin / your_password')
"
```

2. **Настройте API токен для Fail2ban:**
```bash
sudo nano /usr/local/bin/marzban-fail2ban-action.sh
# Установите MARZBAN_API_TOKEN="ваш-api-токен"
```

3. **Доступ к панели:**
   - Веб-панель: `https://ваш-домен:8000/dashboard/`
   - API документация: `https://ваш-домен:8000/docs`

## 🔧 Конфигурация

### 🔐 Основные настройки безопасности

Создайте файл `.env` с следующими параметрами:

```bash
# Двухфакторная аутентификация
TWO_FACTOR_AUTH_ENABLED=true
TWO_FACTOR_ISSUER_NAME="Enhanced Marzban"
TWO_FACTOR_BACKUP_CODES_COUNT=10

# Интеграция с Fail2ban
FAIL2BAN_ENABLED=true
FAIL2BAN_LOG_PATH="/var/log/marzban/fail2ban.log"
FAIL2BAN_MAX_VIOLATIONS=3
TORRENT_DETECTION_ENABLED=true
TRAFFIC_ANALYSIS_ENABLED=true

# Ограничение подключений
CONNECTION_LIMIT_ENABLED=true
DEFAULT_MAX_CONNECTIONS=5
CONNECTION_TRACKING_INTERVAL=30

# DNS переопределение
DNS_OVERRIDE_ENABLED=true
DNS_OVERRIDE_SERVERS="1.1.1.1,8.8.8.8"
DNS_CACHE_TTL=300

# Блокировка рекламы
ADBLOCK_ENABLED=true
ADBLOCK_UPDATE_INTERVAL=86400
ADBLOCK_DEFAULT_LISTS="easylist,easyprivacy,malware"

# Производительность и очистка
LOG_CLEANUP_ENABLED=true
LOG_RETENTION_DAYS=30
PERFORMANCE_MONITORING_ENABLED=true
```

### 🛡️ Настройка Fail2ban

После установки обновите API токен в скрипте действий:

```bash
sudo nano /usr/local/bin/marzban-fail2ban-action.sh
# Установите MARZBAN_API_TOKEN="ваш-admin-api-токен"
```

### 🌐 Настройка Nginx

Enhanced Marzban включает готовую конфигурацию Nginx с заголовками безопасности:

```nginx
server {
    listen 443 ssl http2;
    server_name ваш-домен.com;

    # SSL конфигурация
    ssl_certificate /etc/ssl/certs/marzban.crt;
    ssl_certificate_key /etc/ssl/private/marzban.key;

    # Заголовки безопасности
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📖 Документация

### 🌐 API Эндпоинты

Enhanced Marzban предоставляет расширенный REST API:

#### 🔐 Двухфакторная аутентификация
- `GET /api/2fa/status` - Получить статус 2FA
- `POST /api/2fa/setup` - Настроить 2FA
- `POST /api/2fa/verify-setup` - Подтвердить и включить 2FA
- `POST /api/2fa/disable` - Отключить 2FA
- `GET /api/2fa/backup-codes` - Получить резервные коды

#### 🛡️ Интеграция с Fail2ban
- `GET /api/fail2ban/status` - Статус сервиса
- `GET /api/fail2ban/statistics` - Статистика нарушений
- `GET /api/fail2ban/violations` - Список нарушений
- `POST /api/fail2ban/action` - Обработка бан/разбан действий

#### 🌐 Управление DNS
- `GET /api/dns/rules` - Получить глобальные DNS правила
- `POST /api/dns/rules` - Создать DNS правило
- `GET /api/dns/users/{user_id}/rules` - Получить пользовательские DNS правила
- `POST /api/dns/resolve` - Тестировать разрешение домена

#### 🚫 Блокировка рекламы
- `GET /api/adblock/lists` - Получить списки блокировки
- `POST /api/adblock/lists` - Создать список блокировки
- `GET /api/adblock/users/{user_id}/settings` - Настройки пользователя
- `POST /api/adblock/check-domain` - Проверить блокировку домена

#### 🔧 Управление сервисами
- `GET /api/enhanced/status` - Статус всех сервисов
- `GET /api/enhanced/health` - Проверка работоспособности
- `GET /api/enhanced/overview` - Обзор сервисов

### 📊 Веб-панель

Enhanced Marzban включает расширенную веб-панель с:

- **Мониторинг сервисов** в реальном времени
- **Управление 2FA** для администраторов
- **Отслеживание нарушений** и их разрешение
- **Мониторинг подключений** по пользователям
- **Управление DNS правилами**
- **Конфигурация блокировки рекламы**


## 🔒 Безопасность

### 🛡️ Функции безопасности

- **Двухфакторная аутентификация** для всех администраторов
- **Мониторинг трафика** в реальном времени
- **Автоматическая блокировка** подозрительных пользователей
- **Ограничение подключений** по IP-адресам
- **Защита от DDoS** через Nginx
- **Заголовки безопасности** HTTP

### 🔍 Мониторинг нарушений

Enhanced Marzban автоматически отслеживает:

- **Торрент-трафик** по сигнатурам протоколов
- **Высокую нагрузку** на полосу пропускания
- **Частые подключения** с одного IP
- **Превышение лимитов** подключений
- **Подозрительную активность** пользователей

## 📊 Мониторинг

### 📈 Метрики производительности

- **Статистика подключений** в реальном времени
- **Использование полосы пропускания**
- **Время отклика сервисов**
- **Частота ошибок**
- **Состояние системы**

### 🚨 Система оповещений

- **Email уведомления** о нарушениях
- **Webhook интеграция**
- **Поддержка Telegram бота**
- **Настраиваемые правила** оповещений

## 🌐 API

Enhanced Marzban предоставляет полный REST API для программного взаимодействия.

Для просмотра документации API в Swagger UI или ReDoc, установите `DOCS=True` в конфигурации и перейдите по адресам `/docs` и `/redoc`.

### 🔧 Управление сервисами

```bash
# Проверка статуса всех сервисов
curl -X GET "https://ваш-домен/api/enhanced/status" \
     -H "Authorization: Bearer ваш-токен"

# Перезапуск сервиса
curl -X POST "https://ваш-домен/api/enhanced/services/fail2ban_logger/restart" \
     -H "Authorization: Bearer ваш-токен"

# Проверка работоспособности
curl -X GET "https://ваш-домен/api/enhanced/health" \
     -H "Authorization: Bearer ваш-токен"
```

## 🤝 Поддержка

### 📞 Получение помощи

- **GitHub Issues:** [Создать issue](https://github.com/Kavis1/enhanced-marzban/issues)
- **GitHub Discussions:** [Обсуждения](https://github.com/Kavis1/enhanced-marzban/discussions)
- **Документация:** [Wiki](https://github.com/Kavis1/enhanced-marzban/wiki)

### 🔧 Обслуживание

#### Управление сервисами
```bash
# Просмотр логов
journalctl -u enhanced-marzban -f

# Просмотр логов Fail2ban
tail -f /var/log/marzban/fail2ban.log

# Очистка старых логов
find /var/log/marzban -name "*.log" -mtime +30 -delete
```

#### Резервное копирование
```bash
# Резервная копия базы данных
pg_dump marzban > backup_$(date +%Y%m%d).sql

# Резервная копия конфигурации
tar -czf config_backup_$(date +%Y%m%d).tar.gz /opt/marzban/.env /etc/fail2ban/
```

### 🚀 Обновления

Для обновления Enhanced Marzban:

```bash
cd /opt/marzban
git pull origin main
pip3 install -r requirements.txt
systemctl restart enhanced-marzban
```

## 📄 Лицензия

Enhanced Marzban распространяется под лицензией [AGPL-3.0](./LICENSE).

Основано на оригинальном проекте [Marzban](https://github.com/Gozargah/Marzban) от команды Gozargah.

## 🙏 Благодарности

- **Оригинальный проект:** [Marzban](https://github.com/Gozargah/Marzban)
- **Xray-core:** [XTLS/Xray-core](https://github.com/XTLS/Xray-core)
- **Fail2ban:** [fail2ban/fail2ban](https://github.com/fail2ban/fail2ban)
- **EasyList:** [easylist.to](https://easylist.to/) за списки блокировки рекламы

---

<p align="center">
  <strong>Enhanced Marzban - Расширенная безопасность для вашего VPN</strong>
</p>

<p align="center">
  Сделано с ❤️ для сообщества
</p>
