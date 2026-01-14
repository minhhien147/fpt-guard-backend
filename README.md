# 🌊 FPT Guard 2.0 - Backend API & Admin Dashboard

Backend API cho ứng dụng giám sát mực nước sông Mekong với Admin Dashboard quản lý người dùng.

## 📋 Tính Năng

### 🌊 Water Level Monitoring
- ✅ Tự động scrape dữ liệu từ MRC mỗi giờ
- ✅ 5 trạm quan trắc chính ở ĐBSCL
- ✅ Cảnh báo ngưỡng lũ tự động
- ✅ Lưu trữ lịch sử dữ liệu

### 👥 User Management
- ✅ Đăng ký/Đăng nhập với JWT
- ✅ Quản lý profile người dùng
- ✅ Role-based access (User/Admin)
- ✅ Session management
- ✅ Activity tracking

### 🎨 Admin Dashboard
- ✅ Web UI quản lý users
- ✅ Thống kê và analytics
- ✅ Quản lý báo cáo SOS
- ✅ Theo dõi hoạt động người dùng
- ✅ Chạy trên trình duyệt, không cần app

### 🆘 SOS System
- ✅ Báo cáo khẩn cấp với GPS
- ✅ Quản lý trạng thái (Pending/Resolved/Cancelled)
- ✅ Xem vị trí trên Google Maps

## 🚀 Quick Start

### 1️⃣ Chạy Local (Development)

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy server
python app.py

# Server chạy tại: http://localhost:5000
# Admin dashboard: http://localhost:5000/admin
```

**Login mặc định:**
- Email: `admin@fptguard.com`
- Password: `admin123`

### 2️⃣ Deploy Production (5 phút)

**Railway (Khuyến nghị - Free):**

```bash
# Đọc hướng dẫn chi tiết
📖 DEPLOYMENT_QUICKSTART.md

# Hoặc hướng dẫn đầy đủ
📖 DEPLOYMENT_GUIDE.md
```

**Các option khác:**
- Railway (Free $5/tháng)
- Render (Free tier)
- VPS (DigitalOcean/AWS)
- Docker

## 📚 Documentation

> 🗺️ **Không biết đọc tài liệu nào?** Xem [DOCS_INDEX.md](DOCS_INDEX.md) - Hướng dẫn chọn tài liệu phù hợp

### 📖 Deployment Guides

| File | Dành Cho | Thời Gian | Độ Khó |
|------|----------|-----------|--------|
| **[🆕 Getting Started](GETTING_STARTED_BACKEND.md)** | Người mới hoàn toàn | 30 phút | ⭐ Dễ |
| **[⚡ Quick Deploy](DEPLOYMENT_QUICKSTART.md)** | Deploy nhanh Railway | 5 phút | ⭐ Dễ |
| **[📖 Full Guide](DEPLOYMENT_GUIDE.md)** | Tất cả platforms | 60 phút | ⭐⭐ Medium |
| **[🔍 Comparison](DEPLOYMENT_COMPARISON.md)** | So sánh platforms | 10 phút | ⭐ Dễ |
| **[📋 Cheat Sheet](DEPLOYMENT_CHEATSHEET.md)** | Tham khảo nhanh | 2 phút | ⭐ Dễ |

### 👥 User Management

| File | Dành Cho | Thời Gian | Độ Khó |
|------|----------|-----------|--------|
| **[User Management Guide](USER_MANAGEMENT_GUIDE.md)** | Admin & API docs | 20 phút | ⭐⭐ Medium |
| **[User Quickstart](USER_MANAGEMENT_QUICKSTART.md)** | Quickstart | 5 phút | ⭐ Dễ |

### 🗺️ Navigation

| File | Mô Tả |
|------|-------|
| **[📖 Docs Index](DOCS_INDEX.md)** | Tìm tài liệu phù hợp với bạn |
| **[📱 Main README](../README.md)** | Project overview |

## 🗂️ Cấu Trúc Project

```
backend-python/
├── app.py                  # Main Flask application
├── auth.py                 # Authentication & authorization
├── database.py             # Database layer (SQLite)
├── scheduler.py            # Auto-update scheduler
├── mrc_scraper.py          # Web scraper cho MRC
├── data_processor.py       # Data processing
├── config.py               # Configuration
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── Procfile               # Heroku/Railway config
│
├── templates/
│   └── admin.html         # Admin dashboard UI
│
├── static/
│   └── images/            # Static assets
│
├── data/                  # Data storage (auto-created)
│   ├── users.db           # SQLite database
│   ├── latest_water_levels.json
│   └── historical_data.csv
│
├── logs/                  # Logs (auto-created)
│   ├── api.log
│   └── scheduler.log
│
└── docs/                  # Documentation
    ├── DEPLOYMENT_GUIDE.md
    ├── DEPLOYMENT_QUICKSTART.md
    ├── USER_MANAGEMENT_GUIDE.md
    └── USER_MANAGEMENT_QUICKSTART.md
```

## 🔌 API Endpoints

### General
- `GET /` - API information
- `GET /api/health` - Health check
- `GET /admin` - Admin dashboard (Web UI)

### Water Level
- `GET /api/stations` - Danh sách trạm
- `GET /api/stations/<id>` - Chi tiết trạm
- `GET /api/latest` - Dữ liệu mới nhất
- `GET /api/alerts` - Cảnh báo hiện tại
- `GET /api/historical/<id>` - Dữ liệu lịch sử
- `POST /api/update` - Trigger cập nhật
- `GET /api/status` - Trạng thái scheduler

### Authentication
- `POST /api/auth/register` - Đăng ký
- `POST /api/auth/login` - Đăng nhập
- `POST /api/auth/logout` - Đăng xuất
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Thông tin user
- `PUT /api/auth/update` - Cập nhật profile

### Admin (Requires Admin Role)
- `GET /api/admin/users` - Danh sách users
- `GET /api/admin/users/<id>` - Chi tiết user
- `PUT /api/admin/users/<id>` - Cập nhật user
- `GET /api/admin/statistics` - Thống kê
- `GET /api/admin/sos` - Danh sách SOS
- `PUT /api/admin/sos/<id>` - Cập nhật SOS

### SOS
- `POST /api/sos` - Tạo báo cáo SOS

### Activity Tracking
- `POST /api/activity/track` - Track hoạt động

## 🛠️ Tech Stack

- **Framework:** Flask 3.1.0
- **Database:** SQLite (có thể upgrade lên PostgreSQL)
- **Web Scraping:** Selenium + BeautifulSoup
- **Scheduler:** APScheduler
- **Authentication:** Custom JWT-like tokens
- **CORS:** Flask-CORS

## ⚙️ Configuration

File `config.py` chứa các cấu hình:

```python
# Các trạm quan trắc
STATIONS = {
    "can_tho": {...},
    "my_thuan": {...},
    "vinh_long": {...},
    "tan_chau": {...},
    "chau_doc": {...}
}

# Cập nhật tự động
UPDATE_INTERVAL = 3600  # 1 giờ

# API Settings
API_HOST = "0.0.0.0"
API_PORT = 5000
API_DEBUG = True
```

## 🔐 Security

- ✅ Password hashing (SHA256)
- ✅ JWT-like token authentication
- ✅ Role-based access control
- ✅ Session management
- ✅ Input validation
- ✅ CORS protection
- ⚠️ **NHỚ ĐỔI ADMIN PASSWORD sau khi deploy!**

## 📊 Admin Dashboard Features

### Dashboard Overview
- 📈 Tổng số người dùng
- 👤 Users hoạt động (7 ngày)
- 🆕 Users mới (7 ngày)
- 🆘 Báo cáo SOS chưa xử lý

### User Management
- 🔍 Tìm kiếm users
- 👁️ Xem chi tiết user
- 🔒 Khóa/mở khóa tài khoản
- 👑 Thay đổi role (User/Admin)
- 📜 Xem lịch sử hoạt động

### SOS Management
- 📍 Xem vị trí trên Google Maps
- ✅ Cập nhật trạng thái
- 📞 Thông tin người báo cáo
- ⏰ Timestamp

### Analytics
- 🏆 Top 10 users hoạt động
- 📊 Hoạt động theo loại
- 📈 Thống kê sử dụng

## 🔄 Auto-Update Scheduler

Scheduler tự động chạy mỗi giờ:

1. ✅ Scrape dữ liệu từ MRC
2. ✅ Xử lý và validate
3. ✅ Lưu vào JSON (latest)
4. ✅ Append vào CSV (historical)
5. ✅ Log kết quả

Kiểm tra scheduler:

```bash
curl http://localhost:5000/api/status
```

## 📱 Kết Nối với Flutter App

### Update API URL

**Development (Android Emulator):**
```dart
static const String baseUrl = 'http://10.0.2.2:5000';
```

**Development (iOS Simulator):**
```dart
static const String baseUrl = 'http://localhost:5000';
```

**Production:**
```dart
static const String baseUrl = 'https://your-domain.com';
```

### Files cần update:
- `lib/services/auth_service.dart`
- `lib/services/api_service.dart`

## 🐛 Debugging

### Xem Logs

```bash
# API logs
tail -f logs/api.log

# Scheduler logs
tail -f logs/scheduler.log
```

### Test Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Get stations
curl http://localhost:5000/api/stations

# Get latest data
curl http://localhost:5000/api/latest

# Login test
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@fptguard.com","password":"admin123"}'
```

## 🌍 Environment Variables

Khi deploy, set các variables sau:

```bash
PORT=5000                    # Port (tự động trên Railway/Render)
HOST=0.0.0.0                 # Host
API_DEBUG=False              # Production mode
PYTHONUNBUFFERED=1           # Show logs real-time
```

## 📦 Dependencies

Main dependencies (xem `requirements.txt` đầy đủ):

```
flask==3.1.0
flask-cors==5.0.0
selenium==4.27.1
beautifulsoup4==4.12.3
pandas==2.2.3
APScheduler==3.11.0
passlib==1.7.4
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Linux/Mac
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Chrome/Selenium Error
```bash
# Install Chrome
sudo apt install -y chromium-browser chromium-chromedriver
```

### Database Locked
```python
# Thêm timeout vào database connection
sqlite3.connect(DB_FILE, timeout=10)
```

## 📈 Monitoring

### Health Check
```bash
# Setup monitoring với UptimeRobot
URL: https://your-domain.com/api/health
Interval: 5 minutes
```

### Logs
```bash
# Production logs (VPS)
sudo journalctl -u fptguard -f

# Docker logs
docker-compose logs -f
```

## 🎯 Roadmap

### Version 2.0 (Current) ✅
- Water level monitoring
- User management
- Admin dashboard
- SOS system
- Activity tracking

### Version 2.1 (Planned) 🔜
- Two-factor authentication (2FA)
- Email notifications
- Advanced analytics charts
- Export reports (PDF/CSV)
- Push notifications
- User feedback system

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## 📄 License

MIT License - Xem file LICENSE

## 👥 Support

- **Email:** support@fptguard.com
- **Documentation:** Xem các file `.md` trong thư mục này
- **Issues:** GitHub Issues

## 🎓 Quick Links

| Task | Link |
|------|------|
| 🚀 Deploy ngay (5 phút) | [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) |
| 📖 Deploy đầy đủ | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| 👥 Quản lý users | [USER_MANAGEMENT_GUIDE.md](USER_MANAGEMENT_GUIDE.md) |
| ⚡ User quickstart | [USER_MANAGEMENT_QUICKSTART.md](USER_MANAGEMENT_QUICKSTART.md) |

## ✅ Checklist Deployment

- [ ] Test local thành công
- [ ] Chọn hosting platform
- [ ] Deploy backend
- [ ] Đổi admin password
- [ ] Test admin dashboard
- [ ] Update Flutter app URL
- [ ] Test end-to-end
- [ ] Setup monitoring
- [ ] Setup backup (nếu cần)

---

**🌊 FPT Guard 2.0 - Bảo vệ cộng đồng ĐBSCL khỏi lũ lụt**

Được phát triển với ❤️ bởi FPT University Students
