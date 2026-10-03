# 05: Lịch tập (WorkoutPlan)

**What to build:** User tạo, xem, sửa, xóa lịch tập của mình, lọc theo trạng thái/ngày; không thấy lịch người khác. Trạng thái chuyển theo quy tắc.

**Blocked by:** 01

**Status:** done

- [x] CRUD `/api/workout-plans/`, lọc `?status=`, `?date=`
- [x] Plan người khác → 404
- [x] Tạo mới luôn PLANNED; chuyển PLANNED→CANCELLED được; chuyển không hợp lệ → 400
- [x] (PLANNED→COMPLETED yêu cầu log — hoàn thiện ở ticket 07)
- [x] Test
