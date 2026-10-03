# 01: Khởi tạo project + đăng ký/đăng nhập JWT

**What to build:** Django project chạy được; người dùng đăng ký tài khoản (role USER) và đăng nhập nhận access/refresh token; refresh token hoạt động. Admin tạo bằng `createsuperuser` có role ADMIN.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] `requirements.txt`, `.gitignore`, settings DRF + Simple JWT, custom User có `role`
- [x] `POST /api/auth/register/` → 201; username/email trùng → 400; password < 8 → 400; client gửi `role` bị bỏ qua
- [x] `POST /api/auth/login/` đúng → access + refresh; sai → 401; user bị khóa → 401
- [x] `POST /api/auth/token/refresh/` hoạt động
- [x] API protected không token → 401
- [x] Permission class `IsAdminRole` dùng lại được cho các ticket sau
- [x] Test cho các case trên
