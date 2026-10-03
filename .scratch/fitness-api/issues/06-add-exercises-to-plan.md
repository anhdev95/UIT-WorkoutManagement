# 06: Thêm bài tập vào lịch (WorkoutPlanDetail)

**What to build:** User thêm bài tập vào lịch của mình với mục tiêu sets/reps/weight/nghỉ, xem danh sách bài trong lịch, sửa và xóa từng bài. Xem chi tiết plan thấy luôn các bài.

**Blocked by:** 04, 05

**Status:** done

- [x] `GET/POST /api/workout-plans/{id}/exercises/`
- [x] `PUT/PATCH/DELETE /api/workout-plan-details/{id}/`
- [x] `order_number` tự gán nếu thiếu; target_sets/reps <= 0 → 400; weight âm → 400
- [x] Plan người khác → 404; plan không PLANNED → 400
- [x] Test
