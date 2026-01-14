# 📚 Hướng Dẫn Quản Lý Người Dùng - FPT Guard 2.0

## 🎯 Tổng Quan

Hệ thống quản lý người dùng của FPT Guard 2.0 bao gồm:

- ✅ **Authentication System**: Đăng ký, đăng nhập, JWT tokens
- ✅ **Admin Dashboard**: Giao diện web để quản lý users
- ✅ **User Analytics**: Theo dõi hoạt động và thống kê
- ✅ **SOS Management**: Quản lý báo cáo khẩn cấp
- ✅ **Activity Tracking**: Ghi nhận hành vi người dùng

---

## 🚀 Cài Đặt và Chạy Backend

### 1. Cài đặt dependencies

```bash
cd backend-python
pip install -r requirements.txt
```

### 2. Khởi động server

```bash
python app.py
```

Server sẽ chạy tại: `http://localhost:5000`

### 3. Truy cập Admin Dashboard

Mở trình duyệt và truy cập: **http://localhost:5000/admin**

**Tài khoản admin mặc định:**
- Email: `admin@fptguard.com`
- Password: `admin123`

⚠️ **Lưu ý**: Đổi mật khẩu admin ngay sau khi đăng nhập lần đầu!

---

## 📱 Cấu Hình Flutter App

### 1. Cập nhật API URL

Mở file `lib/services/auth_service.dart` và thay đổi `baseUrl`:

```dart
static const String baseUrl = 'http://YOUR_SERVER_IP:5000';
```

**Các trường hợp:**
- Local testing (Android Emulator): `http://10.0.2.2:5000`
- Local testing (iOS Simulator): `http://localhost:5000`
- Real device (cùng WiFi): `http://192.168.x.x:5000` (IP máy tính)
- Production: `https://your-domain.com`

### 2. Build và chạy app

```bash
flutter pub get
flutter run
```

---

## 🎨 Admin Dashboard - Hướng Dẫn Sử Dụng

### Các Tính Năng Chính

#### 1️⃣ **Dashboard Overview**
- **Tổng số người dùng**: Số lượng users đã đăng ký
- **Người dùng hoạt động**: Users đăng nhập trong 7 ngày
- **Người dùng mới**: Users đăng ký trong 7 ngày
- **Báo cáo SOS**: Số báo cáo đang chờ xử lý

#### 2️⃣ **Quản Lý Người Dùng**
- Xem danh sách tất cả users
- Tìm kiếm theo tên, email, MSSV
- Xem chi tiết user và lịch sử hoạt động
- Khóa/mở khóa tài khoản
- Thay đổi vai trò (user/admin)

#### 3️⃣ **Quản Lý SOS Reports**
- Xem danh sách báo cáo SOS
- Xem vị trí trên Google Maps
- Cập nhật trạng thái: Pending → Resolved/Cancelled
- Xem thông tin người báo cáo

#### 4️⃣ **Thống Kê & Phân Tích**
- Top 10 users hoạt động nhiều nhất
- Thống kê hoạt động theo loại
- Xu hướng sử dụng app

---

## 🔐 API Endpoints

### Authentication APIs

#### **POST** `/api/auth/register`
Đăng ký tài khoản mới

```json
{
  "full_name": "Nguyễn Văn A",
  "student_id": "SE123456",
  "phone": "0123456789",
  "email": "user@example.com",
  "password": "password123"
}
```

#### **POST** `/api/auth/login`
Đăng nhập

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {...},
    "token": "eyJ0eXAi...",
    "refresh_token": "dGVzdC...",
    "expires_at": "2024-01-20T10:00:00"
  }
}
```

#### **POST** `/api/auth/logout`
Đăng xuất (requires authentication)

**Headers:**
```
Authorization: Bearer <token>
```

#### **GET** `/api/auth/me`
Lấy thông tin user hiện tại (requires authentication)

#### **PUT** `/api/auth/update`
Cập nhật profile (requires authentication)

```json
{
  "full_name": "Tên mới",
  "phone": "0987654321",
  "student_id": "SE999999"
}
```

---

### Admin APIs (Requires Admin Role)

#### **GET** `/api/admin/users`
Lấy danh sách users

Query params:
- `limit`: Số lượng (default: 100)
- `offset`: Vị trí bắt đầu (default: 0)
- `role`: Filter theo role (optional)

#### **GET** `/api/admin/users/<user_id>`
Xem chi tiết user

#### **PUT** `/api/admin/users/<user_id>`
Cập nhật thông tin user

```json
{
  "full_name": "...",
  "email": "...",
  "role": "user|admin",
  "is_active": true|false
}
```

#### **GET** `/api/admin/statistics`
Lấy thống kê tổng quan

#### **GET** `/api/admin/sos`
Lấy danh sách SOS reports

Query params:
- `status`: pending|resolved|cancelled
- `limit`: Số lượng (default: 100)

#### **PUT** `/api/admin/sos/<report_id>`
Cập nhật trạng thái SOS

```json
{
  "status": "resolved"
}
```

---

### SOS APIs

#### **POST** `/api/sos`
Tạo báo cáo SOS (requires authentication)

```json
{
  "latitude": 10.123,
  "longitude": 105.456,
  "message": "Cần hỗ trợ khẩn cấp!"
}
```

---

### Activity Tracking

#### **POST** `/api/activity/track`
Theo dõi hoạt động (requires authentication)

```json
{
  "action": "view_water_level",
  "details": {
    "screen": "water_level",
    "station_id": "can_tho"
  }
}
```

---

## 💾 Database Schema

### Users Table
```sql
- id: INTEGER PRIMARY KEY
- full_name: TEXT
- student_id: TEXT UNIQUE
- phone: TEXT
- email: TEXT UNIQUE
- password_hash: TEXT
- role: TEXT (user|admin)
- is_active: INTEGER (0|1)
- created_at: TEXT
- updated_at: TEXT
- last_login: TEXT
```

### Sessions Table
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK)
- token: TEXT UNIQUE
- refresh_token: TEXT UNIQUE
- device_info: TEXT (JSON)
- ip_address: TEXT
- created_at: TEXT
- expires_at: TEXT
- is_active: INTEGER
```

### User Activity Table
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK)
- action: TEXT
- details: TEXT (JSON)
- ip_address: TEXT
- created_at: TEXT
```

### SOS Reports Table
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FK)
- location_lat: REAL
- location_lon: REAL
- message: TEXT
- status: TEXT (pending|resolved|cancelled)
- created_at: TEXT
- updated_at: TEXT
```

---

## 📊 User Analytics - Các Hoạt Động Được Theo Dõi

1. **user_created**: User đăng ký tài khoản
2. **logged_in**: User đăng nhập
3. **logged_out**: User đăng xuất
4. **profile_updated**: User cập nhật profile
5. **sos_created**: User tạo báo cáo SOS
6. **view_water_level**: Xem mực nước
7. **view_news**: Xem tin tức
8. **view_tide**: Xem thủy triều
9. **add_contact**: Thêm liên hệ
10. **update_location**: Cập nhật vị trí

### Cách Sử Dụng Activity Tracking trong Flutter

```dart
import '../services/auth_service.dart';

// Track khi user xem một screen
await AuthService().trackActivity(
  'view_water_level',
  {'station_id': 'can_tho', 'timestamp': DateTime.now().toIso8601String()}
);

// Track khi user thực hiện hành động
await AuthService().trackActivity(
  'add_contact',
  {'contact_name': 'Emergency', 'phone': '113'}
);
```

---

## 🔒 Bảo Mật

### 1. Password Hashing
- Sử dụng SHA256 để hash password
- Không lưu plain text password

### 2. Token Management
- JWT-like tokens (custom implementation)
- Token expires sau 7 ngày
- Refresh token để gia hạn session

### 3. Role-Based Access Control
- **User role**: Chỉ truy cập API cơ bản
- **Admin role**: Truy cập tất cả API và dashboard

### 4. Input Validation
- Validate email format
- Password tối thiểu 6 ký tự
- Sanitize user inputs

---

## 🚀 Deployment

### Option 1: Heroku

```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create fpt-guard-api

# Push code
git push heroku main

# Set environment variables
heroku config:set API_HOST=0.0.0.0
heroku config:set API_PORT=5000

# View logs
heroku logs --tail
```

### Option 2: DigitalOcean / AWS / VPS

1. **Setup server** (Ubuntu 20.04+)
2. **Install Python 3.13**
3. **Clone repository**
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Run with production server**:
   ```bash
   # Install gunicorn
   pip install gunicorn
   
   # Run
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

6. **Setup Nginx** (reverse proxy)
7. **Setup SSL** with Let's Encrypt
8. **Setup systemd** service for auto-restart

### Option 3: Docker

```bash
# Build
docker build -t fpt-guard-api .

# Run
docker run -p 5000:5000 fpt-guard-api
```

---

## 📈 Monitoring & Analytics

### Metrics to Track

1. **User Growth**
   - Daily active users (DAU)
   - Monthly active users (MAU)
   - New registrations per day

2. **Feature Usage**
   - Most viewed screens
   - SOS reports frequency
   - Water level checks

3. **Performance**
   - API response times
   - Error rates
   - Server uptime

### Recommended Tools

- **Google Analytics**: Web analytics
- **Mixpanel**: User behavior analytics
- **Sentry**: Error tracking
- **Grafana**: Metrics dashboard

---

## 🆘 SOS Management Best Practices

1. **Response Time**: Phản hồi SOS trong vòng 5-10 phút
2. **Prioritization**: Ưu tiên theo mức độ khẩn cấp
3. **Follow-up**: Liên hệ lại sau khi resolved
4. **Documentation**: Ghi chú chi tiết về từng case
5. **Analytics**: Phân tích patterns để cải thiện

---

## 📞 Support & Contact

- **Email**: support@fptguard.com
- **Documentation**: [GitHub Wiki](https://github.com/your-repo)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)

---

## 🎓 Training for Admins

### Checklist cho Admin mới

- [ ] Đọc toàn bộ guide này
- [ ] Đăng nhập vào dashboard
- [ ] Đổi password admin
- [ ] Tạo 1-2 test users
- [ ] Test các tính năng quản lý user
- [ ] Test SOS management workflow
- [ ] Hiểu cách đọc analytics
- [ ] Biết cách export data nếu cần

### Video Tutorials (Recommended to Create)

1. Getting Started with Admin Dashboard
2. Managing Users Effectively
3. Handling SOS Reports
4. Reading Analytics and Reports
5. Security Best Practices

---

## 📝 Changelog

### Version 2.0.0 (Current)
- ✅ Complete user management system
- ✅ JWT-based authentication
- ✅ Admin dashboard
- ✅ User analytics
- ✅ SOS management
- ✅ Activity tracking

### Planned for Version 2.1.0
- 🔜 Two-factor authentication (2FA)
- 🔜 Email notifications
- 🔜 Advanced analytics charts
- 🔜 Export reports to PDF/CSV
- 🔜 Push notifications integration
- 🔜 User feedback system

---

## ⚖️ License & Compliance

- Tuân thủ GDPR (nếu có users EU)
- Tuân thủ PDPA (Việt Nam)
- Bảo mật dữ liệu cá nhân
- Quyền xóa dữ liệu theo yêu cầu

---

**🎉 Chúc bạn thành công với FPT Guard 2.0!**
