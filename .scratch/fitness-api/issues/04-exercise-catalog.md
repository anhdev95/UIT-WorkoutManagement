# 04: Danh mục bài tập

**What to build:** Mọi user đăng nhập xem/tìm/lọc bài tập; chỉ admin thêm/sửa/xóa. Bài tập đang được dùng trong lịch thì không xóa được.

**Blocked by:** 01

**Status:** done

- [x] `GET /api/exercises/` + `?muscle_group=`, `?exercise_type=`, `?difficulty=`, `?search=`
- [x] Admin POST/PUT/PATCH/DELETE → 201/200/204; User → 403
- [x] `name` trùng → 400
- [x] Xóa bài đang dùng → 400 (PROTECT)
- [x] Test
