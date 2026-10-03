# Spec: Fitness API (IE221 – Quản lý lịch tập & theo dõi sức khỏe)

Baseline: `IE221_QuanLyLichTap_Claude_Context.md` (7 bảng, Django + DRF + SQLite + Simple JWT, demo bằng Postman).
File này chỉ ghi các quyết định bổ sung cho những chỗ baseline còn mơ hồ.

## Quyết định đã chốt

### Chung
- Django project ở **gốc repo** (`manage.py` ở root), package cấu hình `config/`, 3 app `accounts`, `workouts`, `health`.
- Dependency tối thiểu: Django 5.2 LTS, djangorestframework, djangorestframework-simplejwt. Không dùng django-filter (lọc bằng query param trong `get_queryset`).
- Code, enum, comment: tiếng Anh. Message lỗi validation trả cho client: tiếng Việt. README: tiếng Việt.
- Không phân trang (dữ liệu đồ án nhỏ, demo Postman dễ đọc).
- ViewSet hỗ trợ cả PUT và PATCH.
- Scope: làm **toàn bộ** ~32 API, kể cả Admin User và 3 API thống kê.

### Auth & Role
- Login bằng `username` + `password` (Simple JWT mặc định).
- `email` bắt buộc, unique (so sánh không phân biệt hoa thường).
- Password tối thiểu 8 ký tự, hash bằng Django.
- Field `role` (ADMIN/USER) là nguồn duy nhất cho phân quyền API. Register luôn tạo `USER`, bỏ qua `role` client gửi.
- `createsuperuser` tạo user `role=ADMIN`.
- Tài khoản bị khóa (`is_active=False`): login → 401, token cũ → 401 (Simple JWT tự kiểm tra `is_active`).
- Admin không được khóa/mở tài khoản Admin (kể cả chính mình) (400).

### Profile
- UserProfile được tạo ngay trong lúc register (trong serializer, không dùng signal).
- `GET/PUT/PATCH /api/profile/` trả cả thông tin user (username, email, role – read-only) và profile.
- `height_cm > 0`; `date_of_birth` không ở tương lai.

### HealthRecord
- BMI tính khi tạo/sửa và **lưu snapshot** (đổi chiều cao sau này không làm đổi record cũ). Làm tròn 2 chữ số.
- Chưa có `height_cm` trong profile → 400 ("Vui lòng cập nhật chiều cao trong hồ sơ trước").
- `weight_kg > 0`, `body_fat_percent` trong (0, 100), `waist_cm > 0`; `recorded_date` mặc định hôm nay, không ở tương lai.
- Lọc `?from=&to=` theo `recorded_date`. Sắp xếp mới nhất trước.

### Exercise
- `name` unique. User: chỉ đọc. Admin: CRUD. User POST/PUT/DELETE → 403.
- Lọc `?muscle_group=`, `?exercise_type=`, `?difficulty=`, `?search=` (name/description).
- `created_by` = admin tạo. Xóa Exercise đang được dùng trong WorkoutPlanDetail → `PROTECT`, trả 400.

### WorkoutPlan / Detail
- Truy cập dữ liệu người khác → **404** (lọc queryset theo `request.user`). Lỗi role → 403.
- Lọc `?status=`, `?date=`. Response chi tiết plan kèm danh sách detail (exercise name).
- Thêm bài: `POST/GET /api/workout-plans/{id}/exercises/`; sửa/xóa: `/api/workout-plan-details/{id}/`.
- `order_number` tự gán = max + 1 nếu không gửi.
- Chỉ thêm/sửa/xóa detail khi plan đang `PLANNED` (400 nếu không).
- Chuyển trạng thái hợp lệ: `PLANNED → COMPLETED` (yêu cầu ≥ 1 WorkoutLog), `PLANNED → CANCELLED`. Các chuyển khác → 400. Tạo mới luôn là `PLANNED`.

### WorkoutLog
- **Mỗi detail tối đa 1 log** (OneToOne). Nhập sai thì sửa bằng PUT/PATCH. (ERD đổi từ 1:N thành 1:1.)
- `user` gán từ `request.user`. Log cho detail của người khác → 400 "Không tìm thấy bài tập này trong lịch tập của bạn" (giống id không tồn tại, không lộ dữ liệu).
- Không ghi log cho plan `CANCELLED` (400).
- `calories_burned` read-only, tự tính = `exercise.calories_per_minute × duration_minutes` nếu đủ dữ liệu, ngược lại null.
- `actual_sets > 0`, `actual_reps > 0`, `actual_weight >= 0`, `duration_minutes > 0`.
- Có DELETE để đủ CRUD.

### Statistics (chỉ dữ liệu của user hiện tại)
- `overview`: `total_workouts` = số plan khác CANCELLED; `completed_workouts` = số plan COMPLETED; `total_training_minutes` = tổng `duration_minutes` của log; `total_calories_burned`; `starting_weight` = record có `recorded_date` sớm nhất; `current_weight` = muộn nhất; `weight_change` = current − starting; `bmi` = BMI của record mới nhất. Không có dữ liệu → null/0.
- `weight-progress`: danh sách `{date, weight, bmi}` tăng dần theo ngày, hỗ trợ `?from=&to=`.
- `workout-progress`: mỗi plan COMPLETED → `{date, name, exercises, total_minutes, total_calories}`, tăng dần theo ngày.

### Kiểm thử & demo
- Django `APITestCase` cho từng app, bám bảng test case trong baseline.
- Management command `seed_demo` tạo admin, user `duc`, 4+ exercise, plan mẫu.
- Postman collection trong `postman/`, dùng biến `{{base_url}}`, `{{access_token}}`.
