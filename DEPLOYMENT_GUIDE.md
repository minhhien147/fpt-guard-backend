# 🚀 Hướng Dẫn Deploy Backend Admin Dashboard - FPT Guard 2.0

## 📋 Mục Lục
1. [Tổng Quan](#tổng-quan)
2. [Chuẩn Bị Trước Khi Deploy](#chuẩn-bị-trước-khi-deploy)
3. [Option 1: Deploy lên Railway (Khuyến Nghị)](#option-1-deploy-lên-railway)
4. [Option 2: Deploy lên Render](#option-2-deploy-lên-render)
5. [Option 3: Deploy lên VPS (DigitalOcean/AWS/Azure)](#option-3-deploy-lên-vps)
6. [Option 4: Deploy với Docker](#option-4-deploy-với-docker)
7. [Cấu Hình Theo Dõi 24/7](#cấu-hình-theo-dõi-247)
8. [Bảo Mật và Tối Ưu](#bảo-mật-và-tối-ưu)
9. [Monitoring và Maintenance](#monitoring-và-maintenance)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Tổng Quan

Hướng dẫn này sẽ giúp bạn deploy backend API và Admin Dashboard để:
- ✅ Chạy 24/7 không gián đoạn
- ✅ Tự động cập nhật dữ liệu mực nước mỗi giờ
- ✅ Quản lý users và SOS reports từ xa
- ✅ Có domain riêng và SSL certificate
- ✅ Monitoring và error tracking

---

## 📦 Chuẩn Bị Trước Khi Deploy

### 1. Kiểm Tra Files Cần Thiết

Đảm bảo các file sau đã có trong thư mục `backend-python`:

```
backend-python/
├── app.py                  # Main application
├── requirements.txt        # Python dependencies
├── Procfile               # Process configuration
├── Dockerfile             # Docker configuration
├── config.py              # Configuration
├── auth.py                # Authentication
├── database.py            # Database layer
├── scheduler.py           # Auto-update scheduler
├── mrc_scraper.py         # Web scraper
├── data_processor.py      # Data processing
├── templates/
│   └── admin.html         # Admin dashboard UI
├── static/
│   └── images/
│       └── app_icon.jpg   # App icon
└── data/                  # Data storage (auto-created)
```

### 2. Test Local Trước

```bash
cd backend-python
pip install -r requirements.txt
python app.py
```

Truy cập:
- API: `http://localhost:5000`
- Admin Dashboard: `http://localhost:5000/admin`
- Login: `admin@fptguard.com` / `admin123`

---

## 🚂 Option 1: Deploy lên Railway (Khuyến Nghị)

**Ưu điểm:**
- ✅ Miễn phí $5/tháng credit
- ✅ Tự động deploy từ GitHub
- ✅ SSL certificate tự động
- ✅ Logs real-time
- ✅ Dễ scale

### Bước 1: Chuẩn Bị Repository

```bash
# Tạo .gitignore nếu chưa có
cat > backend-python/.gitignore << EOF
__pycache__/
*.pyc
*.pyo
*.db
logs/
data/latest_water_levels.json
.env
*.log
EOF

# Commit code
git add backend-python/
git commit -m "Prepare backend for deployment"
git push origin main
```

### Bước 2: Deploy trên Railway

1. **Đăng ký Railway**
   - Truy cập: https://railway.app
   - Sign up với GitHub account

2. **Tạo New Project**
   - Click "New Project"
   - Chọn "Deploy from GitHub repo"
   - Chọn repository `fpt-guard-v2`

3. **Cấu Hình Service**
   - Root Directory: `backend-python`
   - Start Command: `python app.py`

4. **Environment Variables**
   
   Click vào "Variables" và thêm:
   ```
   PORT=5000
   HOST=0.0.0.0
   API_DEBUG=False
   PYTHONUNBUFFERED=1
   ```

5. **Domain Setup**
   - Vào "Settings" → "Networking"
   - Railway sẽ tự động tạo domain: `your-app.railway.app`
   - Hoặc thêm custom domain của bạn

6. **Deploy**
   - Railway sẽ tự động deploy
   - Xem logs tại tab "Deployments"

### Bước 3: Truy Cập Dashboard

```
URL: https://your-app.railway.app/admin
Login: admin@fptguard.com / admin123
```

### Bước 4: Cập Nhật Flutter App

Trong file `lib/services/auth_service.dart`:

```dart
static const String baseUrl = 'https://your-app.railway.app';
```

---

## 🎨 Option 2: Deploy lên Render

**Ưu điểm:**
- ✅ Miễn phí tier
- ✅ Auto-deploy từ GitHub
- ✅ SSL miễn phí
- ✅ Easy setup

### Bước 1: Tạo Web Service

1. Truy cập: https://render.com
2. Sign up với GitHub
3. Click "New +" → "Web Service"
4. Connect repository

### Bước 2: Cấu Hình

```yaml
Name: fpt-guard-backend
Runtime: Python 3
Region: Singapore (gần VN nhất)
Branch: main
Root Directory: backend-python
Build Command: pip install -r requirements.txt
Start Command: python app.py
```

### Bước 3: Environment Variables

```
PORT=5000
HOST=0.0.0.0
PYTHONUNBUFFERED=1
```

### Bước 4: Deploy

- Click "Create Web Service"
- Đợi 5-10 phút để build
- URL: `https://fpt-guard-backend.onrender.com`

⚠️ **Lưu ý**: Free tier của Render sẽ sleep sau 15 phút không hoạt động. Cần upgrade để chạy 24/7.

---

## 💻 Option 3: Deploy lên VPS (DigitalOcean/AWS/Azure)

**Ưu điểm:**
- ✅ Kiểm soát hoàn toàn
- ✅ Chạy 24/7 ổn định
- ✅ Có thể customize
- ✅ Performance cao

**Chi phí:** $5-10/tháng

### Bước 1: Tạo VPS

**DigitalOcean:**
1. Truy cập: https://digitalocean.com
2. Tạo Droplet:
   - OS: Ubuntu 22.04 LTS
   - Plan: Basic $6/month (1GB RAM)
   - Region: Singapore
   - SSH Key hoặc Password

### Bước 2: Kết Nối và Cài Đặt

```bash
# SSH vào server
ssh root@your_server_ip

# Update system
apt update && apt upgrade -y

# Install Python 3.11+
apt install -y python3 python3-pip python3-venv

# Install Chrome và dependencies (cho Selenium)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt install -y ./google-chrome-stable_current_amd64.deb
apt install -y chromium-chromedriver

# Install Git
apt install -y git

# Install Nginx (reverse proxy)
apt install -y nginx

# Install Supervisor (process manager)
apt install -y supervisor
```

### Bước 3: Clone Code và Setup

```bash
# Tạo user riêng (bảo mật)
adduser fptguard
usermod -aG sudo fptguard
su - fptguard

# Clone repository
cd /home/fptguard
git clone https://github.com/your-username/fpt-guard-v2.git
cd fpt-guard-v2/backend-python

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

### Bước 4: Cấu Hình Gunicorn

Tạo file `gunicorn_config.py`:

```python
# /home/fptguard/fpt-guard-v2/backend-python/gunicorn_config.py
bind = "127.0.0.1:5000"
workers = 4
threads = 2
timeout = 120
accesslog = "/home/fptguard/fpt-guard-v2/backend-python/logs/gunicorn_access.log"
errorlog = "/home/fptguard/fpt-guard-v2/backend-python/logs/gunicorn_error.log"
loglevel = "info"
```

### Bước 5: Cấu Hình Supervisor (Auto-restart)

Tạo file `/etc/supervisor/conf.d/fptguard.conf`:

```ini
[program:fptguard]
command=/home/fptguard/fpt-guard-v2/backend-python/venv/bin/gunicorn -c gunicorn_config.py app:app
directory=/home/fptguard/fpt-guard-v2/backend-python
user=fptguard
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/fptguard.err.log
stdout_logfile=/var/log/fptguard.out.log
environment=PATH="/home/fptguard/fpt-guard-v2/backend-python/venv/bin"
```

Khởi động:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fptguard
sudo supervisorctl status
```

### Bước 6: Cấu Hình Nginx (Reverse Proxy)

Tạo file `/etc/nginx/sites-available/fptguard`:

```nginx
server {
    listen 80;
    server_name your_domain.com;  # Hoặc IP address

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (nếu cần)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /home/fptguard/fpt-guard-v2/backend-python/static;
        expires 30d;
    }

    # Logs
    access_log /var/log/nginx/fptguard_access.log;
    error_log /var/log/nginx/fptguard_error.log;
}
```

Kích hoạt:

```bash
sudo ln -s /etc/nginx/sites-available/fptguard /etc/nginx/sites-enabled/
sudo nginx -t  # Test config
sudo systemctl restart nginx
```

### Bước 7: Cài SSL Certificate (HTTPS)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Lấy SSL certificate (miễn phí)
sudo certbot --nginx -d your_domain.com

# Auto-renew certificate
sudo certbot renew --dry-run
```

### Bước 8: Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow 'OpenSSH'
sudo ufw enable
sudo ufw status
```

### Bước 9: Kiểm Tra

```bash
# Kiểm tra service
sudo supervisorctl status fptguard

# Xem logs
tail -f /var/log/fptguard.out.log
tail -f /home/fptguard/fpt-guard-v2/backend-python/logs/api.log

# Test API
curl http://localhost:5000/api/health
```

Truy cập: `https://your_domain.com/admin`

---

## 🐳 Option 4: Deploy với Docker

### Bước 1: Build Docker Image

```bash
cd backend-python

# Build image
docker build -t fpt-guard-backend:latest .

# Test local
docker run -p 5000:5000 fpt-guard-backend:latest
```

### Bước 2: Deploy lên Docker Hub

```bash
# Login Docker Hub
docker login

# Tag image
docker tag fpt-guard-backend:latest your-username/fpt-guard-backend:latest

# Push
docker push your-username/fpt-guard-backend:latest
```

### Bước 3: Deploy trên Server với Docker Compose

Tạo file `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: your-username/fpt-guard-backend:latest
    container_name: fptguard-backend
    restart: always
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
      - HOST=0.0.0.0
      - API_DEBUG=False
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Nginx reverse proxy (optional)
  nginx:
    image: nginx:alpine
    container_name: fptguard-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
```

Chạy:

```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f
```

---

## ⏰ Cấu Hình Theo Dõi 24/7

### 1. Đảm Bảo Scheduler Hoạt Động

Backend đã có built-in scheduler sẽ tự động:
- ✅ Cập nhật dữ liệu mực nước mỗi giờ
- ✅ Lưu vào `data/latest_water_levels.json`
- ✅ Lưu lịch sử vào `data/historical_data.csv`

Kiểm tra scheduler:

```bash
# Gọi API
curl https://your-domain.com/api/status

# Response sẽ có:
{
  "success": true,
  "data": {
    "scheduler_running": true,
    "next_update": "2024-01-20T11:00:00",
    "last_update": "2024-01-20T10:00:00"
  }
}
```

### 2. Setup Uptime Monitoring

**Option A: UptimeRobot (Miễn phí)**

1. Truy cập: https://uptimerobot.com
2. Tạo Monitor:
   - Type: HTTP(s)
   - URL: `https://your-domain.com/api/health`
   - Interval: 5 minutes
   - Alert: Email/SMS khi down

**Option B: Pingdom**

1. Truy cập: https://pingdom.com
2. Setup monitoring tương tự
3. Nhận alert khi server down

### 3. Setup Health Check Endpoint

API đã có endpoint `/api/health`:

```json
GET /api/health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:00:00",
  "scheduler_running": true
}
```

### 4. Auto-Update Data Trigger (Backup)

Nếu muốn backup, setup cron job để trigger update:

```bash
# Edit crontab
crontab -e

# Thêm dòng này (cập nhật mỗi giờ)
0 * * * * curl -X POST https://your-domain.com/api/update
```

---

## 🔒 Bảo Mật và Tối Ưu

### 1. Đổi Admin Password

**QUAN TRỌNG:** Đổi password admin ngay sau khi deploy!

```bash
# Truy cập admin dashboard
https://your-domain.com/admin

# Login với:
Email: admin@fptguard.com
Password: admin123

# Sau đó update profile hoặc tạo admin mới
```

Hoặc update trực tiếp database:

```python
# Tạo script change_admin_password.py
import sqlite3
import hashlib

def change_admin_password(new_password):
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    conn = sqlite3.connect('data/users.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (password_hash, 'admin@fptguard.com')
    )
    conn.commit()
    conn.close()
    print("Password changed successfully!")

change_admin_password("YourNewSecurePassword123!")
```

### 2. Environment Variables (Bảo Mật)

Tạo file `.env` (KHÔNG commit vào Git):

```bash
# .env
SECRET_KEY=your-secret-key-here-very-long-random-string
DATABASE_URL=sqlite:///data/users.db
API_DEBUG=False
ALLOWED_ORIGINS=https://your-domain.com
```

Update `config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
API_DEBUG = os.getenv('API_DEBUG', 'False') == 'True'
```

### 3. Rate Limiting

Cài đặt Flask-Limiter:

```bash
pip install Flask-Limiter
```

Thêm vào `app.py`:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Áp dụng cho login endpoint
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # ...existing code...
```

### 4. CORS Configuration

Update CORS trong `app.py`:

```python
from flask_cors import CORS

# Chỉ cho phép domain Flutter app
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-flutter-app-domain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### 5. Database Backup

Setup auto-backup database:

```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="/home/fptguard/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/home/fptguard/fpt-guard-v2/backend-python/data/users.db"

# Tạo backup
cp $DB_FILE $BACKUP_DIR/users_db_$DATE.db

# Xóa backup cũ hơn 30 ngày
find $BACKUP_DIR -name "users_db_*.db" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Cron job:

```bash
# Backup mỗi ngày lúc 2AM
0 2 * * * /home/fptguard/backup_db.sh
```

---

## 📊 Monitoring và Maintenance

### 1. Log Management

**Xem logs real-time:**

```bash
# API logs
tail -f backend-python/logs/api.log

# Scheduler logs
tail -f backend-python/logs/scheduler.log

# System logs (VPS)
sudo journalctl -u fptguard -f
```

**Log rotation** (tránh logs quá lớn):

```bash
# /etc/logrotate.d/fptguard
/home/fptguard/fpt-guard-v2/backend-python/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 fptguard fptguard
}
```

### 2. Performance Monitoring

**Cài đặt monitoring tools:**

```bash
# Install htop (CPU/RAM monitoring)
sudo apt install htop

# Monitor
htop
```

**API Response Time Monitoring:**

```python
# Thêm vào app.py
import time
from functools import wraps

def measure_time(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{f.__name__} took {end_time - start_time:.2f}s")
        return result
    return decorated_function

# Áp dụng cho endpoints
@app.route('/api/latest', methods=['GET'])
@measure_time
def get_latest_data():
    # ...existing code...
```

### 3. Error Tracking với Sentry (Optional)

```bash
pip install sentry-sdk[flask]
```

```python
# app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### 4. Database Optimization

```python
# Thêm indexes để tăng tốc queries
# database.py

def create_indexes(self):
    """Tạo indexes cho performance"""
    cursor = self.conn.cursor()
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email 
        ON users(email)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_token 
        ON sessions(token)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_activity_user_id 
        ON user_activity(user_id, created_at)
    """)
    
    self.conn.commit()
```

### 5. Auto-Update Code từ GitHub

```bash
#!/bin/bash
# update_app.sh

cd /home/fptguard/fpt-guard-v2
git pull origin main
cd backend-python
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart fptguard
echo "App updated and restarted"
```

---

## 🆘 Troubleshooting

### Vấn Đề 1: Server Không Start

**Kiểm tra:**

```bash
# Xem logs
sudo journalctl -u fptguard -n 50

# Kiểm tra port
sudo netstat -tulpn | grep 5000

# Kiểm tra process
ps aux | grep python
```

**Giải pháp:**

```bash
# Restart service
sudo supervisorctl restart fptguard

# Hoặc restart toàn bộ
sudo systemctl restart supervisor
```

### Vấn Đề 2: Scheduler Không Chạy

**Kiểm tra:**

```bash
curl http://localhost:5000/api/status

# Xem scheduler logs
tail -f logs/scheduler.log
```

**Giải pháp:**

```bash
# Trigger manual update
curl -X POST http://localhost:5000/api/update

# Restart app
sudo supervisorctl restart fptguard
```

### Vấn Đề 3: Selenium/Chrome Error

**Lỗi thường gặp:** "ChromeDriver not found"

**Giải pháp:**

```bash
# Cài đặt Chrome và ChromeDriver
sudo apt install -y chromium-browser chromium-chromedriver

# Hoặc download manual
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
VERSION=$(cat LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/$VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

### Vấn Đề 4: Database Locked

**Lỗi:** "database is locked"

**Giải pháp:**

```python
# Update database.py để thêm timeout
def __init__(self):
    self.conn = sqlite3.connect(
        DB_FILE, 
        check_same_thread=False,
        timeout=10  # Thêm timeout
    )
```

### Vấn Đề 5: High Memory Usage

**Kiểm tra:**

```bash
free -h
top
```

**Giải pháp:**

```bash
# Giảm số Gunicorn workers
# gunicorn_config.py
workers = 2  # Thay vì 4

# Restart
sudo supervisorctl restart fptguard
```

### Vấn Đề 6: CORS Error

**Lỗi:** "Access to fetch has been blocked by CORS policy"

**Giải pháp:**

```python
# app.py
from flask_cors import CORS

# Allow all origins (development only)
CORS(app, resources={r"/*": {"origins": "*"}})

# Production: specify exact domains
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-flutter-app.com"]
    }
})
```

---

## 📱 Kết Nối Flutter App

### Update API URL

**File: `lib/services/auth_service.dart`**

```dart
class AuthService {
  // Development
  // static const String baseUrl = 'http://10.0.2.2:5000';
  
  // Production
  static const String baseUrl = 'https://your-domain.com';
  
  // ... rest of code
}
```

**File: `lib/services/api_service.dart`**

```dart
class ApiService {
  static const String baseUrl = 'https://your-domain.com';
  
  // ... rest of code
}
```

### Test Connection

```dart
// Test trong Flutter
Future<void> testConnection() async {
  try {
    final response = await http.get(
      Uri.parse('${AuthService.baseUrl}/api/health')
    );
    
    if (response.statusCode == 200) {
      print('✅ Backend connected successfully');
      print(response.body);
    }
  } catch (e) {
    print('❌ Connection failed: $e');
  }
}
```

---

## 🎓 Best Practices Checklist

### Pre-Deployment
- [ ] Test locally đầy đủ
- [ ] Kiểm tra tất cả API endpoints
- [ ] Test admin dashboard
- [ ] Test scheduler tự động cập nhật
- [ ] Đảm bảo có `.gitignore` đúng

### Deployment
- [ ] Chọn hosting platform phù hợp
- [ ] Setup environment variables
- [ ] Configure domain và SSL
- [ ] Setup monitoring (UptimeRobot)
- [ ] Test health check endpoint

### Post-Deployment
- [ ] Đổi admin password ngay lập tức
- [ ] Test truy cập admin dashboard
- [ ] Kiểm tra logs không có error
- [ ] Test auto-update scheduler
- [ ] Update Flutter app với URL mới
- [ ] Test end-to-end flow từ app

### Security
- [ ] HTTPS enabled (SSL certificate)
- [ ] Strong admin password
- [ ] Rate limiting enabled
- [ ] CORS configured properly
- [ ] Firewall rules setup (VPS)
- [ ] Database backup scheduled

### Monitoring
- [ ] Uptime monitoring active
- [ ] Log rotation configured
- [ ] Error tracking setup (Sentry)
- [ ] Performance monitoring
- [ ] Disk space monitoring

---

## 📞 Support và Resources

### Documentation
- API Docs: `/` endpoint trên server
- User Management Guide: `USER_MANAGEMENT_GUIDE.md`
- Quickstart: `USER_MANAGEMENT_QUICKSTART.md`

### Helpful Commands

```bash
# Check server status
curl https://your-domain.com/api/health

# Check scheduler status
curl https://your-domain.com/api/status

# Manual trigger update
curl -X POST https://your-domain.com/api/update

# Check latest data
curl https://your-domain.com/api/latest

# Get all stations
curl https://your-domain.com/api/stations
```

### Monitoring Dashboard URLs

```
Admin Dashboard: https://your-domain.com/admin
API Documentation: https://your-domain.com/
Health Check: https://your-domain.com/api/health
```

---

## 🎉 Kết Luận

Sau khi hoàn thành deployment:

1. ✅ Backend chạy 24/7 trên server
2. ✅ Tự động cập nhật dữ liệu mực nước mỗi giờ
3. ✅ Admin dashboard truy cập được từ bất kỳ đâu
4. ✅ HTTPS secure với SSL certificate
5. ✅ Monitoring và alerts khi có vấn đề
6. ✅ Flutter app kết nối thành công với backend

**URL Quan Trọng:**
- 🌐 Admin Dashboard: `https://your-domain.com/admin`
- 📊 API: `https://your-domain.com/api`
- ❤️ Health Check: `https://your-domain.com/api/health`

**Default Admin Login:**
- Email: `admin@fptguard.com`
- Password: `admin123` (NHỚ ĐỔI NGAY!)

---

## 📝 Quick Reference

### Railway Deploy
```bash
git push origin main
# Auto-deploy on Railway
```

### VPS Commands
```bash
# Restart app
sudo supervisorctl restart fptguard

# View logs
tail -f /var/log/fptguard.out.log

# Update code
cd /home/fptguard/fpt-guard-v2 && git pull && sudo supervisorctl restart fptguard
```

### Docker Commands
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Restart
docker-compose restart
```

---

**🚀 Chúc bạn deploy thành công!**

Nếu gặp vấn đề, hãy kiểm tra phần [Troubleshooting](#troubleshooting) hoặc xem logs để debug.
