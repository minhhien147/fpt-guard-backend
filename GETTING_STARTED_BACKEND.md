# 🚀 Bắt Đầu với Backend FPT Guard 2.0

## 👋 Chào mừng!

Đây là hướng dẫn cho người mới hoàn toàn. Bạn sẽ học cách:
1. ✅ Chạy backend local để test
2. ✅ Deploy lên internet để chạy 24/7
3. ✅ Truy cập admin dashboard
4. ✅ Kết nối với Flutter app

**Thời gian:** 15-30 phút  
**Kinh nghiệm cần:** Không cần (hướng dẫn từng bước)

---

## 📋 Bạn Cần Gì?

### Phần Mềm
- [ ] Python 3.11+ ([Download](https://python.org))
- [ ] Git ([Download](https://git-scm.com))
- [ ] Trình duyệt web (Chrome/Firefox)
- [ ] Code editor (VS Code khuyến nghị)

### Tài Khoản (Miễn Phí)
- [ ] GitHub account
- [ ] Railway account (dùng GitHub để đăng ký)

---

## 🎯 Phần 1: Chạy Local (10 phút)

### Bước 1: Mở Terminal/Command Prompt

**Windows:**
- Nhấn `Win + R`
- Gõ `cmd` và Enter

**Mac/Linux:**
- Nhấn `Cmd + Space`
- Gõ `terminal` và Enter

### Bước 2: Clone Project

```bash
# Di chuyển đến thư mục muốn lưu project
cd Desktop

# Clone project
git clone https://github.com/your-username/fpt-guard-v2.git

# Vào thư mục backend
cd fpt-guard-v2/backend-python
```

### Bước 3: Cài Đặt Dependencies

```bash
# Windows
python -m pip install -r requirements.txt

# Mac/Linux
python3 -m pip install -r requirements.txt
```

⏳ **Đợi 2-3 phút** để cài đặt...

### Bước 4: Chạy Server

```bash
# Windows
python app.py

# Mac/Linux
python3 app.py
```

✅ **Thành công!** Bạn sẽ thấy:
```
MEKONG RIVER WATER LEVEL MONITORING - API SERVER
======================================================================

Khởi động scheduler...
Khởi động Flask API server...
  → Host: 0.0.0.0
  → Port: 5000
  → API URL: http://localhost:5000
```

### Bước 5: Test Backend

**Mở trình duyệt** và truy cập:

1. **API Home:** http://localhost:5000
   - Sẽ thấy danh sách tất cả endpoints

2. **Admin Dashboard:** http://localhost:5000/admin
   - Login:
     - Email: `admin@fptguard.com`
     - Password: `admin123`

3. **Health Check:** http://localhost:5000/api/health
   - Kiểm tra backend đang chạy

✅ **Nếu thấy được 3 trang trên → Backend đang chạy OK!**

---

## 🌐 Phần 2: Deploy Lên Internet (5 phút)

Bây giờ backend chỉ chạy trên máy bạn. Để chạy 24/7 trên internet:

### Option A: Railway (Khuyến Nghị - Dễ Nhất)

#### Bước 1: Đăng Ký Railway
1. Truy cập: https://railway.app
2. Click **"Login with GitHub"**
3. Authorize Railway

#### Bước 2: Tạo Project
1. Click **"New Project"**
2. Chọn **"Deploy from GitHub repo"**
3. Chọn repository `fpt-guard-v2`
4. Railway sẽ tự động detect và deploy!

#### Bước 3: Cấu Hình (quan trọng!)
1. Click vào project vừa tạo
2. Vào **"Settings"**
3. Tìm **"Root Directory"** → Nhập: `backend-python`
4. Click **"Variables"** → Thêm:
   ```
   PORT=5000
   ```
5. Click **"Deployments"** → Chờ deploy (3-5 phút)

#### Bước 4: Lấy URL
1. Vào tab **"Settings"** → **"Networking"**
2. Copy URL (dạng: `https://your-app.railway.app`)
3. Lưu lại URL này!

#### Bước 5: Test Online
Mở trình duyệt, truy cập:
```
https://your-app.railway.app/admin
```

Login:
- Email: `admin@fptguard.com`
- Password: `admin123`

✅ **Thấy admin dashboard → Deploy thành công!**

---

## 📱 Phần 3: Kết Nối Flutter App (5 phút)

### Bước 1: Mở Project Flutter

```bash
cd ..  # Ra khỏi thư mục backend-python
# Giờ bạn đang ở thư mục fpt-guard-v2
```

### Bước 2: Cập Nhật API URL

Mở file `lib/services/auth_service.dart`:

**Tìm dòng:**
```dart
static const String baseUrl = 'http://10.0.2.2:5000';
```

**Đổi thành:**
```dart
static const String baseUrl = 'https://your-app.railway.app';
```

*(Thay `your-app.railway.app` bằng URL Railway của bạn)*

### Bước 3: Cập Nhật API Service

Mở file `lib/services/api_service.dart`:

**Tìm dòng:**
```dart
static const String baseUrl = 'http://10.0.2.2:5000';
```

**Đổi thành:**
```dart
static const String baseUrl = 'https://your-app.railway.app';
```

### Bước 4: Test App

```bash
flutter pub get
flutter run
```

**Test các tính năng:**
- [ ] Đăng ký tài khoản mới
- [ ] Đăng nhập
- [ ] Xem mực nước sông
- [ ] Tạo báo cáo SOS (test)

✅ **Nếu mọi thứ hoạt động → Hoàn tất!**

---

## 🎓 Phần 4: Làm Chủ Admin Dashboard

### Truy Cập Dashboard

```
URL: https://your-app.railway.app/admin
Email: admin@fptguard.com
Password: admin123
```

### Các Tab Chính

#### 1️⃣ **Dashboard** (Trang chủ)
- Xem tổng số users
- Users hoạt động 7 ngày
- Users mới 7 ngày
- Báo cáo SOS chưa xử lý

#### 2️⃣ **Người dùng** (Users Tab)
- Xem danh sách tất cả users
- Tìm kiếm theo tên, email, MSSV
- Click "Xem" để xem chi tiết user
- Click "Khóa/Mở" để quản lý tài khoản

#### 3️⃣ **Báo cáo SOS** (SOS Tab)
- Xem tất cả báo cáo khẩn cấp
- Click vào tọa độ GPS → Mở Google Maps
- Dropdown để thay đổi trạng thái:
  - Pending: Chưa xử lý
  - Resolved: Đã xử lý
  - Cancelled: Hủy

#### 4️⃣ **Hoạt động** (Activity Tab)
- Top 10 users hoạt động nhiều nhất
- Thống kê theo loại hoạt động

### Tính Năng Tự Động

✅ **Tự động refresh mỗi 30 giây**  
✅ **Tự động cập nhật dữ liệu mực nước mỗi giờ**  
✅ **Chạy 24/7 không cần bạn làm gì**

---

## 🔐 Bảo Mật QUAN TRỌNG

### ⚠️ ĐỔI MẬT KHẨU ADMIN NGAY!

1. Login vào dashboard
2. Tạo admin mới:
   - Click tab **"Người dùng"**
   - Tìm user có email của bạn
   - Click **"Xem"**
   - Có thể update role thành "admin"

3. Hoặc dùng script Python để đổi pass:

```python
# change_password.py
import sqlite3
import hashlib

new_password = "YourNewSecurePassword123!"
password_hash = hashlib.sha256(new_password.encode()).hexdigest()

conn = sqlite3.connect('data/users.db')
cursor = conn.cursor()
cursor.execute(
    "UPDATE users SET password_hash = ? WHERE email = ?",
    (password_hash, 'admin@fptguard.com')
)
conn.commit()
conn.close()
print("✅ Password changed!")
```

Chạy:
```bash
python change_password.py
```

---

## 📊 Monitoring

### Setup Uptime Monitoring (Miễn Phí)

1. Truy cập: https://uptimerobot.com
2. Đăng ký (free)
3. **New Monitor:**
   - Type: HTTP(s)
   - URL: `https://your-app.railway.app/api/health`
   - Friendly Name: FPT Guard Backend
   - Monitoring Interval: 5 minutes
   - Alert Contacts: Your email

4. Click **Create Monitor**

✅ Bây giờ bạn sẽ nhận email nếu backend down!

---

## 🆘 Troubleshooting

### Vấn Đề 1: Backend local không chạy

**Lỗi:** `ModuleNotFoundError: No module named 'flask'`

**Giải pháp:**
```bash
pip install -r requirements.txt
```

---

### Vấn Đề 2: Port 5000 đã được sử dụng

**Lỗi:** `Address already in use`

**Giải pháp Windows:**
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Giải pháp Mac/Linux:**
```bash
lsof -ti:5000 | xargs kill -9
```

---

### Vấn Đề 3: Railway deploy failed

**Kiểm tra:**
1. Vào **Deployments** tab
2. Click vào deployment failed
3. Xem **Logs**

**Lỗi thường gặp:**
- Root Directory sai → Set `backend-python`
- Thiếu dependencies → Railway tự fix

---

### Vấn Đề 4: Flutter app không kết nối được backend

**Kiểm tra:**
1. URL có đúng không?
2. Có HTTPS chưa? (Railway auto có)
3. Test URL trong browser trước

**Test:**
```bash
curl https://your-app.railway.app/api/health
```

Phải return JSON:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "scheduler_running": true
}
```

---

### Vấn Đề 5: Scheduler không cập nhật dữ liệu

**Kiểm tra:**
```bash
curl https://your-app.railway.app/api/status
```

Nếu `scheduler_running: false`:

**Giải pháp:**
1. Restart app (Railway auto restart)
2. Hoặc trigger manual:
```bash
curl -X POST https://your-app.railway.app/api/update
```

---

## 📚 Học Thêm

### Tài Liệu Nâng Cao

| Tài liệu | Khi nào đọc |
|----------|-------------|
| [README.md](README.md) | Tổng quan backend |
| [DEPLOYMENT_COMPARISON.md](DEPLOYMENT_COMPARISON.md) | So sánh platforms |
| [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) | Deploy nhanh Railway |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Hướng dẫn đầy đủ tất cả platforms |
| [USER_MANAGEMENT_GUIDE.md](USER_MANAGEMENT_GUIDE.md) | API docs chi tiết |

### Video Tutorials (Khuyến Nghị)

1. **Setup Local:** 10 phút
2. **Deploy Railway:** 5 phút
3. **Admin Dashboard Tour:** 15 phút
4. **Connect Flutter App:** 10 phút

*(Tự quay hoặc tìm trên YouTube)*

---

## ✅ Checklist Hoàn Thành

### Local Development
- [ ] Python đã cài đặt
- [ ] Dependencies đã cài
- [ ] Backend chạy local OK
- [ ] Truy cập được admin dashboard local
- [ ] API endpoints hoạt động

### Deployment
- [ ] Railway account tạo xong
- [ ] Backend deploy thành công
- [ ] Có URL public
- [ ] Admin dashboard online OK
- [ ] Đã đổi admin password

### Flutter Integration
- [ ] Cập nhật API URL trong code
- [ ] Flutter app connect thành công
- [ ] Đăng ký/đăng nhập hoạt động
- [ ] Xem mực nước hoạt động
- [ ] SOS system hoạt động

### Monitoring
- [ ] Setup UptimeRobot
- [ ] Test alert email
- [ ] Check logs định kỳ

---

## 🎉 Chúc Mừng!

Bạn đã hoàn thành setup backend FPT Guard 2.0!

**Bây giờ bạn có:**
- ✅ Backend chạy 24/7 trên Railway
- ✅ Admin dashboard để quản lý
- ✅ Auto-update dữ liệu mỗi giờ
- ✅ Flutter app kết nối thành công
- ✅ Monitoring để track uptime

**Next Steps:**
1. Thêm users để test
2. Test tất cả features
3. Share link cho bạn bè test
4. Monitor và improve

---

## 💬 Cần Trợ Giúp?

### Documentation
- Đọc [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) để biết thêm chi tiết

### Community
- GitHub Issues: Report bugs
- Discord/Slack: Chat với team

### Support
- Email: support@fptguard.com

---

**📝 Cập nhật:** 2026-01-14  
**🎓 Bởi:** FPT Guard Development Team

**❤️ Made with love for FPT University students**
