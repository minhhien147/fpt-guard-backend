# 📋 Deployment Cheat Sheet - FPT Guard Backend

## 🎯 Lựa Chọn Platform Deploy

| Platform | Chi Phí | Thời Gian Setup | Độ Khó | Uptime 24/7 | Tự Động Deploy |
|----------|---------|-----------------|--------|-------------|-----------------|
| **Railway** ⭐ | $0-$5/tháng | 5 phút | ⭐ Dễ | ✅ | ✅ |
| **Render** | $0-$7/tháng | 7 phút | ⭐ Dễ | ⚠️ Free tier sleep | ✅ |
| **VPS (DigitalOcean)** | $6/tháng | 30 phút | ⭐⭐⭐ Khó | ✅ | ❌ |
| **Docker** | Varies | 15 phút | ⭐⭐ Trung bình | ✅ | ❌ |

**Khuyến nghị:** Railway (Free tier, dễ nhất, tự động deploy)

---

## ⚡ Railway - 5 Phút Deploy

```bash
# 1. Commit code
git add backend-python/
git commit -m "Deploy backend"
git push origin main

# 2. Railway.app
# - Login với GitHub
# - New Project → Deploy from GitHub
# - Select repo
# - Root Directory: backend-python
# - Deploy!

# 3. Set Variables
PORT=5000

# 4. Done! 
# URL: https://your-app.railway.app/admin
```

---

## 🎨 Render - 7 Phút Deploy

```bash
# 1. Render.com
# - Sign up với GitHub
# - New Web Service
# - Connect repository

# 2. Settings
Name: fpt-guard-backend
Runtime: Python 3
Root Directory: backend-python
Build: pip install -r requirements.txt
Start: python app.py

# 3. Variables
PORT=5000
PYTHONUNBUFFERED=1

# 4. Deploy!
# URL: https://fpt-guard-backend.onrender.com/admin
```

---

## 💻 VPS - 30 Phút Setup

```bash
# 1. SSH vào server
ssh root@your_server_ip

# 2. Install dependencies
apt update && apt upgrade -y
apt install -y python3 python3-pip nginx supervisor
apt install -y chromium-browser chromium-chromedriver

# 3. Clone code
git clone https://github.com/your-username/fpt-guard-v2.git
cd fpt-guard-v2/backend-python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn

# 4. Config Supervisor
# Tạo file /etc/supervisor/conf.d/fptguard.conf
[program:fptguard]
command=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
directory=/path/to/backend-python
autostart=true
autorestart=true

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fptguard

# 5. Config Nginx
# Tạo file /etc/nginx/sites-available/fptguard
server {
    listen 80;
    server_name your_domain.com;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
    }
}

sudo ln -s /etc/nginx/sites-available/fptguard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 6. SSL (Optional)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com

# Done! https://your_domain.com/admin
```

---

## 🐳 Docker - 15 Phút Deploy

```bash
# 1. Build image
cd backend-python
docker build -t fpt-guard-backend .

# 2. Test local
docker run -p 5000:5000 fpt-guard-backend

# 3. Create docker-compose.yml
version: '3.8'
services:
  backend:
    image: fpt-guard-backend
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: always

# 4. Run
docker-compose up -d

# 5. Check
docker-compose ps
docker-compose logs -f

# URL: http://localhost:5000/admin
```

---

## 🔧 Environment Variables

```bash
# Railway / Render
PORT=5000
HOST=0.0.0.0
API_DEBUG=False
PYTHONUNBUFFERED=1

# Optional
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///data/users.db
```

---

## 📱 Cập Nhật Flutter App

```dart
// lib/services/auth_service.dart
static const String baseUrl = 'https://your-app.railway.app';

// lib/services/api_service.dart  
static const String baseUrl = 'https://your-app.railway.app';
```

---

## 🔐 Security Checklist

```bash
# 1. Đổi admin password ngay!
# Login: https://your-app.railway.app/admin
# Email: admin@fptguard.com
# Password: admin123 → ĐỔI NGAY!

# 2. Setup HTTPS (tự động trên Railway/Render)

# 3. Setup monitoring
# - UptimeRobot.com
# - Monitor URL: https://your-app/api/health
# - Interval: 5 minutes

# 4. Backup database (nếu cần)
# Download file data/users.db định kỳ
```

---

## 🆘 Troubleshooting - Quick Fix

### Backend không start
```bash
# Check logs
# Railway: Deployments → View Logs
# VPS: sudo journalctl -u fptguard -f
# Docker: docker-compose logs -f

# Restart
# Railway: Auto restart
# VPS: sudo supervisorctl restart fptguard
# Docker: docker-compose restart
```

### Scheduler không chạy
```bash
# Check status
curl https://your-app/api/status

# Manual trigger
curl -X POST https://your-app/api/update

# Restart app
```

### CORS Error
```python
# app.py - Allow all (development only)
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}})
```

### Database locked
```python
# database.py - Add timeout
sqlite3.connect(DB_FILE, timeout=10)
```

---

## ✅ Post-Deployment Checklist

- [ ] Backend deployed và chạy
- [ ] Admin dashboard truy cập được
- [ ] Đã đổi admin password
- [ ] Health check API hoạt động: `/api/health`
- [ ] Scheduler tự động cập nhật: `/api/status`
- [ ] Flutter app đã update URL
- [ ] Test login từ Flutter app
- [ ] Test API endpoints từ app
- [ ] Setup monitoring (UptimeRobot)
- [ ] Backup database (nếu cần)

---

## 🔗 Important URLs

```bash
# Admin Dashboard
https://your-app.railway.app/admin

# API Documentation
https://your-app.railway.app/

# Health Check
https://your-app.railway.app/api/health

# Latest Data
https://your-app.railway.app/api/latest

# Stations
https://your-app.railway.app/api/stations
```

---

## 📞 Quick Commands

```bash
# Test API
curl https://your-app/api/health
curl https://your-app/api/latest
curl https://your-app/api/stations

# Manual update
curl -X POST https://your-app/api/update

# Check scheduler
curl https://your-app/api/status

# Test login
curl -X POST https://your-app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@fptguard.com","password":"admin123"}'
```

---

## 📊 Monitoring URLs

| Service | URL | Purpose |
|---------|-----|---------|
| UptimeRobot | https://uptimerobot.com | Uptime monitoring |
| Sentry | https://sentry.io | Error tracking |
| Google Analytics | https://analytics.google.com | Usage analytics |

---

## 🎓 Learning Resources

| Topic | Link |
|-------|------|
| Full Deploy Guide | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| Quick Deploy | [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) |
| User Management | [USER_MANAGEMENT_GUIDE.md](USER_MANAGEMENT_GUIDE.md) |
| API Docs | `https://your-app/` |

---

## 💡 Pro Tips

1. **Railway:** Tốt nhất cho beginners, free tier đủ dùng
2. **Render:** Free tier có giới hạn, paid tốt
3. **VPS:** Kiểm soát tối đa, cần kinh nghiệm Linux
4. **Docker:** Portable, dễ di chuyển giữa các platform

---

## 📈 Scaling

### Traffic thấp (< 1000 users/day)
→ Railway Free tier hoặc Render Free tier

### Traffic trung bình (1000-10000 users/day)
→ Railway Pro ($5/month) hoặc VPS Basic ($6/month)

### Traffic cao (> 10000 users/day)
→ VPS Pro hoặc Cloud (AWS/GCP)

---

**⏱️ Estimated Time:**
- Railway: 5 phút
- Render: 7 phút
- Docker: 15 phút
- VPS: 30 phút

**💰 Cost:**
- Railway: $0 (Free tier)
- Render: $0 (với giới hạn)
- VPS: $6/tháng
- Docker: Depends on hosting

**🎯 Khuyến nghị:**
→ Bắt đầu với **Railway** (dễ nhất, miễn phí, production-ready)

---

**📝 Last Updated:** 2026-01-14
