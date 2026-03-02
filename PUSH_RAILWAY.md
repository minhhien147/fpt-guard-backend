# 🚂 Hướng dẫn Push Backend lên Railway

**URL backend:** `https://web-production-dd806.up.railway.app`

---

## Cách 1: Push từ thư mục gốc dự án (khuyến nghị)

Backend nằm trong `backend-python/`. Railway thường cấu hình **Root Directory = backend-python**, nên bạn push toàn bộ repo.

### Bước 1: Mở terminal tại thư mục dự án

```bash
cd e:\fpt-guard-v2
```

### Bước 2: Kiểm tra thay đổi

```bash
git status
```

Bạn sẽ thấy các file backend đã sửa (ví dụ: `backend-python/database.py`, `backend-python/auth.py`, `backend-python/app.py`).

### Bước 3: Thêm và commit

```bash
git add backend-python/
git commit -m "Backend: auto logout khi admin khóa tài khoản (403 Account disabled)"
```

*(Hoặc commit tất cả: `git add .` rồi `git commit -m "..."`)*

### Bước 4: Push lên GitHub

- **Nếu nhánh của bạn là `main`:**
  ```bash
  git push origin main
  ```
- **Nếu nhánh của bạn là `master`** (thường gặp):
  ```bash
  git push origin master
  ```
  Hoặc push `master` lên nhánh `main` trên GitHub:
  ```bash
  git push origin master:main
  ```

### Bước 5: Railway tự deploy

- Railway đã kết nối GitHub repo → **tự động build và deploy** khi có `git push`.
- Đợi 2–5 phút, vào **Railway Dashboard** → **Deployments** để xem trạng thái.
- Khi deploy xong, backend mới chạy tại:  
  `https://web-production-dd806.up.railway.app`

---

## Cách 2: Chỉ push thư mục backend (repo riêng)

Nếu bạn dùng **repo riêng chỉ chứa code backend** (ví dụ clone mỗi `backend-python`):

```bash
cd e:\fpt-guard-v2\backend-python
git add .
git commit -m "Auto logout khi admin khóa tài khoản"
git push origin main
```

---

## ⚠️ Deploy mới có mất user không?

Backend dùng **SQLite**, file database: `data/users.db`.

| Trường hợp | Kết quả |
|------------|--------|
| **Chưa cấu hình Volume** | Mỗi lần deploy = container mới → file `data/users.db` mất → **mất hết user cũ**. |
| **Đã gắn Volume cho thư mục `data`** | Database nằm trên Volume → **user và dữ liệu được giữ** khi deploy. |

### Cách giữ user khi deploy (Railway Volume)

1. Vào **Railway Dashboard** → chọn project backend.
2. Chọn **Service** (backend của bạn).
3. Tab **Variables** hoặc **Settings** → tìm **Volumes** (hoặc **Data**).
4. **Add Volume** (hoặc **Mount**):
   - **Mount Path:** `data` (hoặc `/app/data` tùy Railway).
   - Lưu ý: thư mục `data/` trong code phải trùng với mount path (app đang dùng `data/users.db`).
5. **Redeploy** một lần để Volume được gắn.

Sau khi Volume đã gắn, mọi lần push/deploy mới **sẽ không mất user** (database nằm trên Volume).

### Nếu đã deploy và mất user rồi

- Vào **Admin** (hoặc trang **Register** nếu có): tạo lại tài khoản admin.
- Hoặc dùng script/API tạo user admin (xem README/GETTING_STARTED_BACKEND).
- Sau đó **bật Volume** như trên để lần sau không mất nữa.

---

## 📦 Backup ở đâu?

**Railway không có nút "Backup" sẵn** cho SQLite. Bạn có thể backup như sau:

### 1. Tải file database qua API (khuyến nghị)

Backend có endpoint **chỉ Admin** dùng để tải file database:

- **URL:** `GET https://web-production-dd806.up.railway.app/api/admin/backup`
- **Header:** `Authorization: Bearer <token_admin>`
- **Cách lấy token:** Đăng nhập Admin → dùng token trong session (hoặc gọi API login lấy token).

**Ví dụ (trình duyệt):** Đăng nhập xong vào Admin, mở DevTools (F12) → Application/Storage xem token, rồi mở tab mới:

```
https://web-production-dd806.up.railway.app/api/admin/backup
```

(Kèm header `Authorization: Bearer <token>` — hoặc dùng Postman/curl với token.)

**Ví dụ (curl):**
```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -o users_backup.db \
  "https://web-production-dd806.up.railway.app/api/admin/backup"
```

File tải về là bản copy `users.db` (user, session, SOS reports). Lưu file này định kỳ (máy tính, Google Drive, v.v.) là đã backup.

### 2. Railway Volume (giữ data khi deploy)

- Trong Railway: **Architecture** → chọn service **back-end** → **Variables** hoặc **Settings** → **Volumes**.
- Thêm Volume, mount path: `data` (hoặc `/app/data` tùy cấu hình).
- Volume **không thay thế backup**: nếu Volume lỗi hoặc project bị xóa vẫn mất data. Nên vẫn **tải backup qua API** định kỳ.

### 3. Nơi lưu file backup

- Máy tính: lưu file `.db` vào thư mục an toàn.
- Google Drive / OneDrive: upload file backup định kỳ.
- Không lưu token admin hoặc file backup lên repo/public.

---

## 🔓 Khóa nhầm nick Admin

Nếu bạn khóa nhầm tài khoản admin và không đăng nhập được ("Account is disabled"):

### Bước 1: Cấu hình mã khôi phục trên Railway

1. Vào **Railway** → project **back-end** → tab **Variables**.
2. Thêm biến môi trường:
   - **ADMIN_RECOVERY_KEY** = một chuỗi bí mật bạn tự đặt (ví dụ: `MySecretRecovery2024`).
3. (Tùy chọn) Nếu email admin không phải `admin@fptguard.com`, thêm:
   - **ADMIN_EMAIL** = email tài khoản admin cần mở khóa.
4. Lưu → Railway sẽ redeploy (hoặc redeploy thủ công).

### Bước 2: Gọi API mở khóa

Dùng Postman, curl hoặc trình duyệt (cần gửi POST):

```bash
curl -X POST "https://web-production-dd806.up.railway.app/api/recover-admin" \
  -H "Content-Type: application/json" \
  -d "{\"recovery_key\": \"MySecretRecovery2024\"}"
```

*(Thay `MySecretRecovery2024` bằng giá trị **ADMIN_RECOVERY_KEY** bạn đã set.)*

Nếu thành công, response: `"message": "Admin account has been unlocked. You can log in again."`

### Bước 3: Đăng nhập lại

Vào https://web-production-dd806.up.railway.app/admin và đăng nhập bằng email + password admin như bình thường.

**Lưu ý:** Sau khi mở khóa xong, có thể xóa biến **ADMIN_RECOVERY_KEY** trên Railway (hoặc đổi sang chuỗi khác) để tránh lộ.

---

## Kiểm tra sau khi push

1. **Health check**
   ```bash
   curl https://web-production-dd806.up.railway.app/api/health
   ```

2. **Admin**
   - Mở: https://web-production-dd806.up.railway.app/admin
   - Đăng nhập → Khóa một user → Mở app bằng tài khoản đó → App phải tự chuyển về màn Login.

---

## Lỗi thường gặp

| Lỗi | Cách xử lý |
|-----|------------|
| `src refspec main does not match any` | Bạn đang ở nhánh `master`. Dùng `git push origin master` hoặc `git push origin master:main`. |
| `git push` bị từ chối | Kiểm tra đã đăng nhập GitHub (`git config user.name/user.email`), hoặc dùng SSH key / Personal Access Token. |
| Railway không tự deploy | Vào Railway → Project → **Settings** → kiểm tra **Connected Repo** và **Branch** (`main` hoặc `master`). |
| Deploy fail trên Railway | Xem **Deployments** → **View Logs**; thường do thiếu dependency trong `requirements.txt` hoặc lỗi Python. |

---

**Tóm tắt:** Chạy `git add .` → `git commit -m "..."` → `git push origin main` tại thư mục `e:\fpt-guard-v2`, Railway sẽ tự deploy backend mới.
