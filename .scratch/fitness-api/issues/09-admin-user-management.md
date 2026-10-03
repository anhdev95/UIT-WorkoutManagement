# 09: Admin quản lý người dùng

**What to build:** Admin xem danh sách/chi tiết user và khóa/mở tài khoản; user bị khóa không đăng nhập được.

**Blocked by:** 01

**Status:** done

- [x] `GET /api/admin/users/` (+ `?search=`, `?role=`), `GET /api/admin/users/{id}/`
- [x] `PATCH /api/admin/users/{id}/status/` với `{"is_active": false}`
- [x] Không khóa chính mình/admin khác → 400; User thường gọi → 403
- [x] Test
