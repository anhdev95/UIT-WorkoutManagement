# 03: Chỉ số sức khỏe + BMI

**What to build:** User ghi cân nặng/body fat/vòng eo theo ngày, hệ thống tự tính BMI từ chiều cao trong hồ sơ; xem lịch sử, lọc theo khoảng ngày, sửa, xóa.

**Blocked by:** 02

**Status:** done

- [x] CRUD `/api/health-records/`, lọc `?from=&to=`
- [x] BMI = weight / (height_m²), làm tròn 2 chữ số, read-only, snapshot
- [x] Chưa có chiều cao → 400; weight <= 0 → 400
- [x] Record của người khác → 404
- [x] Test (BMI đúng công thức, validation, ownership)
