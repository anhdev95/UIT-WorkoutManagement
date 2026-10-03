# 08: Thống kê tiến độ

**What to build:** User xem tổng quan tiến độ (số buổi, phút tập, calories, cân nặng đầu/hiện tại, BMI), biểu đồ cân nặng theo thời gian và tiến độ các buổi đã hoàn thành.

**Blocked by:** 03, 07

**Status:** done

- [x] `GET /api/statistics/overview/` đúng định nghĩa trong spec
- [x] `GET /api/statistics/weight-progress/` (+ `?from=&to=`)
- [x] `GET /api/statistics/workout-progress/`
- [x] Chỉ tính dữ liệu của user hiện tại; user mới không lỗi
- [x] Test
