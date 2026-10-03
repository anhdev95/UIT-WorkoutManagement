# 02: Hồ sơ cá nhân

**What to build:** Sau khi đăng ký, user có sẵn profile; xem và cập nhật hồ sơ (họ tên, giới tính, ngày sinh, chiều cao, mục tiêu, mức vận động).

**Blocked by:** 01

**Status:** done

- [x] Profile tạo trong lúc register
- [x] `GET /api/profile/` → 200, kèm username/email/role read-only
- [x] `PUT/PATCH /api/profile/` cập nhật; `height_cm <= 0` → 400; ngày sinh tương lai → 400; enum sai → 400
- [x] Không token → 401
- [x] Test
