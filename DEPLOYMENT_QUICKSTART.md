# ⚡ Deploy Backend trong 5 phút - Railway

## 🎯 Hướng Dẫn Siêu Nhanh

### Bước 1: Chuẩn Bị (1 phút)

```bash
cd backend-python

# Tạo .gitignore
cat > .gitignore << EOF
__pycache__/
*.pyc
*.db
logs/
data/latest_water_levels.json
.env
*.log
EOF

# Commit code
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Bước 2: Deploy trên Railway (2 phút)

1. **Đăng ký Railway:** https://railway.app (dùng GitHub)
2. **New Project** → **Deploy from GitHub repo**
3. **Chọn repo** `fpt-guard-v2`
4. **Settings:**
   - Root Directory: `backend-python`
   - Start Command: `python app.py`
5. **Variables:** Thêm `PORT=5000`
6. **Deploy!** ✅

### Bước 3: Truy Cập (1 phút)

Railway sẽ tự tạo URL: `https://your-app.railway.app`

**Admin Dashboard:** `https://your-app.railway.app/admin`
- Email: `admin@fptguard.com`
- Password: `admin123`

### Bước 4: Cập Nhật Flutter App (1 phút)

File `lib/services/auth_service.dart`:

```dart
static const String baseUrl = 'https://your-app.railway.app';
```

File `lib/services/api_service.dart`:

```dart
static const String baseUrl = 'https://your-app.railway.app';
```

## ✅ XONG!

Backend đã chạy 24/7, tự động cập nhật dữ liệu mỗi giờ.

---

## 🔧 Sau Khi Deploy

### 1. ĐỔI PASSWORD ADMIN NGAY!

Vào dashboard → Update user → Đổi password

### 2. Test API

```bash
# Health check
curl https://your-app.railway.app/api/health

# Get latest data
curl https://your-app.railway.app/api/latest
```

### 3. Setup Monitoring (Optional)

1. Vào https://uptimerobot.com
2. Thêm monitor: `https://your-app.railway.app/api/health`
3. Nhận alert qua email khi down

---

## 🆘 Troubleshooting

### Lỗi Deploy

**Kiểm tra logs:** Railway → Deployments → View Logs

**Lỗi thường gặp:**

1. **"No module named 'X'"**
   - Đảm bảo `requirements.txt` đầy đủ
   - Rebuild: Railway sẽ tự động install

2. **"Port already in use"**
   - Railway tự động set PORT, không cần lo

3. **"Database error"**
   - Database sẽ tự tạo lần đầu chạy
   - Check logs xem có lỗi gì không

### App Chạy Nhưng Không Cập Nhật Dữ Liệu

```bash
# Trigger manual update
curl -X POST https://your-app.railway.app/api/update

# Check scheduler status
curl https://your-app.railway.app/api/status
```

---

## 📱 Test Connection từ Flutter

```dart
Future<void> testAPI() async {
  final response = await http.get(
    Uri.parse('https://your-app.railway.app/api/health')
  );
  print(response.body);
}
```

---

## 🔗 Links Quan Trọng

- 📖 **Hướng dẫn đầy đủ:** `DEPLOYMENT_GUIDE.md`
- 👥 **User management:** `USER_MANAGEMENT_GUIDE.md`
- ⚡ **Quickstart user:** `USER_MANAGEMENT_QUICKSTART.md`

---

**Chi phí:** $0 (Free tier: $5 credit/tháng)

**Thời gian uptime:** 24/7

**Auto-scaling:** Có

**SSL:** Tự động

**Logs:** Real-time

---

**🎉 Chúc mừng! Backend của bạn đã live!**
