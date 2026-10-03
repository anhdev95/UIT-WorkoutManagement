# 07: Ghi kết quả tập (WorkoutLog) + hoàn thành buổi tập

**What to build:** User ghi kết quả thực tế cho từng bài trong lịch, hệ thống tự tính calories; xem lịch sử tập; đánh dấu lịch COMPLETED khi đã có kết quả.

**Blocked by:** 06

**Status:** done

- [x] CRUD `/api/workout-logs/` (mỗi detail tối đa 1 log → trùng 400)
- [x] actual_sets/reps <= 0 → 400; detail của người khác → 400; plan CANCELLED → 400
- [x] `calories_burned` tự tính
- [x] PLANNED→COMPLETED chỉ khi plan có ≥ 1 log
- [x] Test
