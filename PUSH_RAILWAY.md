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

```bash
git push origin main
```

*(Nếu nhánh của bạn là `master`: `git push origin master`)*

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
| `git push` bị từ chối | Kiểm tra đã đăng nhập GitHub (`git config user.name/user.email`), hoặc dùng SSH key / Personal Access Token. |
| Railway không tự deploy | Vào Railway → Project → **Settings** → kiểm tra **Connected Repo** và **Branch** (thường là `main`). |
| Deploy fail trên Railway | Xem **Deployments** → **View Logs**; thường do thiếu dependency trong `requirements.txt` hoặc lỗi Python. |

---

**Tóm tắt:** Chạy `git add .` → `git commit -m "..."` → `git push origin main` tại thư mục `e:\fpt-guard-v2`, Railway sẽ tự deploy backend mới.
