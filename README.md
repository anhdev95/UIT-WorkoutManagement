# Hệ thống quản lý lịch tập và theo dõi sức khỏe cá nhân

Đồ án môn **IE221 – Kỹ thuật lập trình Python**.
Backend REST API xây dựng bằng **Python Django + Django REST Framework + SQLite + JWT**, demo bằng **Postman**.

## Chức năng

- Đăng ký, đăng nhập (JWT), 2 vai trò **ADMIN** / **USER**
- Quản lý hồ sơ cá nhân
- Ghi chỉ số sức khỏe theo thời gian, **BMI tự tính** từ chiều cao trong hồ sơ
- Danh mục bài tập (User xem/tìm/lọc, Admin thêm/sửa/xóa)
- Tạo lịch tập, thêm bài tập với mục tiêu sets × reps × kg
- Ghi kết quả tập thực tế (so sánh với mục tiêu), **calories tự tính**
- Thống kê tiến độ tập luyện và cân nặng
- Admin xem danh sách user, khóa/mở tài khoản

## Cài đặt và chạy

Yêu cầu: Python 3.10+

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo         # tạo dữ liệu demo (chạy lại nhiều lần không bị trùng)
python manage.py runserver
```

API chạy tại `http://127.0.0.1:8000/api/`. Trang quản trị Django: `http://127.0.0.1:8000/admin/`.

### Tài khoản demo

| Username | Password | Role |
|---|---|---|
| `admin` | `admin12345` | ADMIN |
| `duc` | `12345678` | USER (có sẵn lịch sử cân nặng và 1 buổi tập đã hoàn thành) |
| `lan` | `12345678` | USER (dùng để demo phân quyền User A / User B) |

Tạo admin khác: `python manage.py createsuperuser` (tự động có role ADMIN).

## Kiểm thử

```bash
python manage.py test              # 70 test: auth, phân quyền, validation, nghiệp vụ, thống kê
```

**Postman:** import `postman/IE221_Fitness_API.postman_collection.json`, sau đó chạy **Run collection** từ trên xuống.
Collection tự lưu token và id vào biến (`access_token`, `admin_token`, `plan_id`, ...) và kiểm tra status code của từng request.
Để chạy lại từ đầu trên database sạch: xóa `db.sqlite3` → `migrate` → `seed_demo`.

## Xác thực

```http
POST /api/auth/login/
{"username": "duc", "password": "12345678"}
```

Các API khác gửi kèm header:

```http
Authorization: Bearer <access_token>
```

## Danh sách API

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Đăng ký (luôn tạo role USER) |
| POST | `/api/auth/login/` | Public | Đăng nhập, trả `access` + `refresh` |
| POST | `/api/auth/token/refresh/` | Public | Lấy access token mới |
| GET, PUT, PATCH | `/api/profile/` | User | Xem/cập nhật hồ sơ |
| GET, POST | `/api/health-records/` | User | Danh sách (`?from=&to=`) / ghi chỉ số |
| GET, PUT, PATCH, DELETE | `/api/health-records/{id}/` | Chủ sở hữu | Chi tiết / sửa / xóa |
| GET | `/api/exercises/` | User | Danh sách (`?muscle_group=`, `?exercise_type=`, `?difficulty=`, `?search=`) |
| GET | `/api/exercises/{id}/` | User | Chi tiết bài tập |
| POST | `/api/exercises/` | Admin | Thêm bài tập |
| PUT, PATCH, DELETE | `/api/exercises/{id}/` | Admin | Sửa / xóa bài tập |
| GET, POST | `/api/workout-plans/` | User | Danh sách (`?status=`, `?date=`) / tạo lịch |
| GET, PUT, PATCH, DELETE | `/api/workout-plans/{id}/` | Chủ sở hữu | Chi tiết (kèm bài tập) / sửa / đổi trạng thái / xóa |
| GET, POST | `/api/workout-plans/{id}/exercises/` | Chủ sở hữu | Danh sách / thêm bài vào lịch |
| GET, PUT, PATCH, DELETE | `/api/workout-plan-details/{id}/` | Chủ sở hữu | Sửa / xóa bài trong lịch |
| GET, POST | `/api/workout-logs/` | User | Lịch sử tập / ghi kết quả |
| GET, PUT, PATCH, DELETE | `/api/workout-logs/{id}/` | Chủ sở hữu | Chi tiết / sửa / xóa kết quả |
| GET | `/api/statistics/overview/` | User | Thống kê tổng quan |
| GET | `/api/statistics/weight-progress/` | User | Cân nặng theo thời gian (`?from=&to=`) |
| GET | `/api/statistics/workout-progress/` | User | Các buổi tập đã hoàn thành |
| GET | `/api/admin/users/` | Admin | Danh sách user (`?role=`, `?search=`) |
| GET | `/api/admin/users/{id}/` | Admin | Chi tiết user |
| PATCH | `/api/admin/users/{id}/status/` | Admin | Khóa/mở tài khoản `{"is_active": false}` |

## Quy tắc nghiệp vụ chính

- User chỉ thấy dữ liệu của chính mình; truy cập dữ liệu người khác trả **404** (không lộ sự tồn tại).
- User thường gọi API chỉ dành cho Admin trả **403**; không có token trả **401**.
- BMI = cân nặng (kg) / chiều cao (m)², hệ thống tự tính và lưu lại tại thời điểm ghi. Phải có chiều cao trong hồ sơ trước.
- Trạng thái lịch tập: `PLANNED → COMPLETED` (cần ít nhất 1 kết quả tập) hoặc `PLANNED → CANCELLED`. Chỉ thêm/sửa bài khi lịch còn `PLANNED`.
- Mỗi bài trong lịch có tối đa 1 kết quả tập; không ghi kết quả cho lịch đã hủy.
- Calories = `calories_per_minute` của bài tập × số phút tập.
- Không xóa được bài tập đang nằm trong lịch tập của người dùng.
- Tài khoản bị khóa không đăng nhập được, token cũ cũng bị từ chối.

## Cấu trúc project

```text
config/       settings, urls gốc
accounts/     User (role), UserProfile, đăng ký, hồ sơ, Admin quản lý user, permission
health/       HealthRecord, tính BMI
workouts/     Exercise, WorkoutPlan, WorkoutPlanDetail, WorkoutLog, thống kê, lệnh seed_demo
postman/      Postman collection
```

Kiến trúc theo Django MVT: **Model** (dữ liệu) → **Serializer** (chuyển đổi JSON + validation) → **View/ViewSet** (xử lý request, phân quyền) → **URL Router**.
