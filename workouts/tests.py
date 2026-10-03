from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests import create_user
from health.models import HealthRecord

from .models import Exercise, WorkoutLog, WorkoutPlan, WorkoutPlanDetail


def create_exercise(name='Bench Press', **kwargs):
    defaults = {'muscle_group': 'CHEST', 'exercise_type': 'STRENGTH', 'calories_per_minute': 6}
    defaults.update(kwargs)
    return Exercise.objects.create(name=name, **defaults)


class ExerciseTests(APITestCase):
    url = '/api/exercises/'

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin12345')
        self.user = create_user('duc')
        create_exercise('Bench Press', description='Đẩy ngực với thanh đòn')
        create_exercise('Squat', muscle_group='LEGS')
        create_exercise('Running', muscle_group='CARDIO', exercise_type='CARDIO')

    def test_user_get_exercises(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)

    def test_filter_and_search(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(len(self.client.get(f'{self.url}?muscle_group=chest').data), 1)
        self.assertEqual(len(self.client.get(f'{self.url}?exercise_type=CARDIO').data), 1)
        res = self.client.get(f'{self.url}?search=press')
        self.assertEqual([e['name'] for e in res.data], ['Bench Press'])

    def test_admin_create_exercise(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(self.url, {'name': 'Plank', 'muscle_group': 'CORE', 'exercise_type': 'STRENGTH'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['created_by'], 'admin')

    def test_admin_update_and_delete_exercise(self):
        self.client.force_authenticate(self.admin)
        squat = Exercise.objects.get(name='Squat')
        res = self.client.patch(f'{self.url}{squat.id}/', {'difficulty': 'ADVANCED'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.delete(f'{self.url}{squat.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_duplicate_name(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(self.url, {'name': 'Squat', 'muscle_group': 'LEGS', 'exercise_type': 'STRENGTH'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_write_exercise(self):
        self.client.force_authenticate(self.user)
        squat = Exercise.objects.get(name='Squat')
        res = self.client.post(self.url, {'name': 'Plank', 'muscle_group': 'CORE', 'exercise_type': 'STRENGTH'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(f'{self.url}{squat.id}/').status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_delete_exercise_in_use(self):
        squat = Exercise.objects.get(name='Squat')
        plan = WorkoutPlan.objects.create(user=self.user, name='Leg Day', workout_date='2026-10-05')
        WorkoutPlanDetail.objects.create(workout_plan=plan, exercise=squat, order_number=1, target_sets=4, target_reps=8)
        self.client.force_authenticate(self.admin)
        res = self.client.delete(f'{self.url}{squat.id}/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Exercise.objects.filter(id=squat.id).exists())

    def test_no_token(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)


class WorkoutTestBase(APITestCase):
    def setUp(self):
        self.user = create_user('duc')
        self.other = create_user('lan')
        self.bench = create_exercise('Bench Press')
        self.shoulder = create_exercise('Shoulder Press', muscle_group='SHOULDERS', calories_per_minute=None)
        self.client.force_authenticate(self.user)

    def create_plan(self, user=None, **kwargs):
        data = {'name': 'Push Day', 'workout_date': '2026-10-05'}
        data.update(kwargs)
        return WorkoutPlan.objects.create(user=user or self.user, **data)

    def add_detail(self, plan, exercise=None, order=1):
        return WorkoutPlanDetail.objects.create(
            workout_plan=plan, exercise=exercise or self.bench, order_number=order,
            target_sets=4, target_reps=10, target_weight=50,
        )


class WorkoutPlanTests(WorkoutTestBase):
    url = '/api/workout-plans/'

    def test_create_plan(self):
        res = self.client.post(self.url, {'name': 'Push Day', 'workout_date': '2026-10-05'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['status'], 'PLANNED')

    def test_create_plan_must_be_planned(self):
        res = self.client.post(self.url, {'name': 'X', 'workout_date': '2026-10-05', 'status': 'COMPLETED'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_own_plans_and_filters(self):
        self.create_plan()
        self.create_plan(name='Leg Day', workout_date='2026-10-06', status='CANCELLED')
        self.create_plan(user=self.other)
        self.assertEqual(len(self.client.get(self.url).data), 2)
        self.assertEqual(len(self.client.get(f'{self.url}?status=PLANNED').data), 1)
        self.assertEqual(len(self.client.get(f'{self.url}?date=2026-10-06').data), 1)

    def test_get_update_delete_own_plan(self):
        plan = self.create_plan()
        self.add_detail(plan)
        res = self.client.get(f'{self.url}{plan.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['details'][0]['exercise_name'], 'Bench Press')

        res = self.client.patch(f'{self.url}{plan.id}/', {'name': 'Push Day A'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.delete(f'{self.url}{plan.id}/').status_code, status.HTTP_204_NO_CONTENT)

    def test_other_users_plan_is_404(self):
        plan = self.create_plan(user=self.other)
        self.assertEqual(self.client.get(f'{self.url}{plan.id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(f'{self.url}{plan.id}/', {'name': 'x'}).status_code, 404)
        self.assertEqual(self.client.delete(f'{self.url}{plan.id}/').status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_plan(self):
        plan = self.create_plan()
        res = self.client.patch(f'{self.url}{plan.id}/', {'status': 'CANCELLED'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # CANCELLED is final
        res = self.client.patch(f'{self.url}{plan.id}/', {'status': 'PLANNED'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_requires_log(self):
        plan = self.create_plan()
        detail = self.add_detail(plan)
        res = self.client.patch(f'{self.url}{plan.id}/', {'status': 'COMPLETED'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        WorkoutLog.objects.create(user=self.user, workout_plan_detail=detail, actual_sets=4, actual_reps=9)
        res = self.client.patch(f'{self.url}{plan.id}/', {'status': 'COMPLETED'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_invalid_date_filter(self):
        self.assertEqual(self.client.get(f'{self.url}?date=05-10-2026').status_code, 400)


class WorkoutPlanDetailTests(WorkoutTestBase):
    def test_add_exercise_to_plan_with_auto_order(self):
        plan = self.create_plan()
        url = f'/api/workout-plans/{plan.id}/exercises/'
        res = self.client.post(url, {'exercise': self.bench.id, 'target_sets': 4, 'target_reps': 10, 'target_weight': 50})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['order_number'], 1)
        res = self.client.post(url, {'exercise': self.shoulder.id, 'target_sets': 3, 'target_reps': 10})
        self.assertEqual(res.data['order_number'], 2)
        self.assertEqual(len(self.client.get(url).data), 2)

    def test_invalid_targets(self):
        plan = self.create_plan()
        url = f'/api/workout-plans/{plan.id}/exercises/'
        for bad in [{'target_sets': 0}, {'target_reps': 0}, {'target_weight': -1}]:
            data = {'exercise': self.bench.id, 'target_sets': 4, 'target_reps': 10, **bad}
            self.assertEqual(self.client.post(url, data).status_code, status.HTTP_400_BAD_REQUEST, bad)

    def test_cannot_add_to_other_users_plan(self):
        plan = self.create_plan(user=self.other)
        res = self.client.post(
            f'/api/workout-plans/{plan.id}/exercises/',
            {'exercise': self.bench.id, 'target_sets': 4, 'target_reps': 10},
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_add_to_cancelled_plan(self):
        plan = self.create_plan(status='CANCELLED')
        res = self.client.post(
            f'/api/workout-plans/{plan.id}/exercises/',
            {'exercise': self.bench.id, 'target_sets': 4, 'target_reps': 10},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_and_delete_detail(self):
        detail = self.add_detail(self.create_plan())
        url = f'/api/workout-plan-details/{detail.id}/'
        res = self.client.patch(url, {'target_reps': 12})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['target_reps'], 12)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_change_detail_of_completed_plan(self):
        detail = self.add_detail(self.create_plan(status='COMPLETED'))
        url = f'/api/workout-plan-details/{detail.id}/'
        self.assertEqual(self.client.patch(url, {'target_reps': 12}).status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 400)

    def test_other_users_detail_is_404(self):
        detail = self.add_detail(self.create_plan(user=self.other))
        url = f'/api/workout-plan-details/{detail.id}/'
        self.assertEqual(self.client.patch(url, {'target_reps': 12}).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)


class WorkoutLogTests(WorkoutTestBase):
    url = '/api/workout-logs/'

    def setUp(self):
        super().setUp()
        self.plan = self.create_plan()
        self.detail = self.add_detail(self.plan)

    def log_data(self, **kwargs):
        data = {'workout_plan_detail': self.detail.id, 'actual_sets': 4, 'actual_reps': 9,
                'actual_weight': 50, 'duration_minutes': 12}
        data.update(kwargs)
        return data

    def test_create_log_and_calories(self):
        res = self.client.post(self.url, self.log_data())
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['calories_burned'], 72)  # 6 kcal/min * 12 min
        self.assertEqual(res.data['target_reps'], 10)
        self.assertEqual(res.data['actual_reps'], 9)

    def test_calories_null_when_exercise_has_no_rate(self):
        detail = self.add_detail(self.plan, exercise=self.shoulder, order=2)
        res = self.client.post(self.url, self.log_data(workout_plan_detail=detail.id))
        self.assertIsNone(res.data['calories_burned'])

    def test_invalid_actual_values(self):
        for bad in [{'actual_sets': 0}, {'actual_reps': 0}, {'actual_weight': -1}]:
            self.assertEqual(self.client.post(self.url, self.log_data(**bad)).status_code, 400, bad)

    def test_one_log_per_detail(self):
        self.client.post(self.url, self.log_data())
        res = self.client.post(self.url, self.log_data())
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_log_other_users_detail(self):
        other_detail = self.add_detail(self.create_plan(user=self.other))
        res = self.client.post(self.url, self.log_data(workout_plan_detail=other_detail.id))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(WorkoutLog.objects.exists())

    def test_cannot_log_cancelled_plan(self):
        self.plan.status = 'CANCELLED'
        self.plan.save()
        res = self.client.post(self.url, self.log_data())
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_log_recalculates_calories(self):
        log = self.client.post(self.url, self.log_data()).data
        res = self.client.patch(f'{self.url}{log["id"]}/', {'duration_minutes': 20})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['calories_burned'], 120)

    def test_other_users_log_is_404(self):
        other_detail = self.add_detail(self.create_plan(user=self.other))
        log = WorkoutLog.objects.create(user=self.other, workout_plan_detail=other_detail, actual_sets=3, actual_reps=8)
        self.assertEqual(self.client.get(f'{self.url}{log.id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(self.client.get(self.url).data), 0)


class StatisticsTests(WorkoutTestBase):
    def test_empty_overview_for_new_user(self):
        res = self.client.get('/api/statistics/overview/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_workouts'], 0)
        self.assertIsNone(res.data['current_weight'])

    def test_overview_and_progress(self):
        # Health records
        HealthRecord.objects.create(user=self.user, weight_kg=72, bmi=25.51, recorded_date='2026-09-01')
        HealthRecord.objects.create(user=self.user, weight_kg=70.5, bmi=24.98, recorded_date='2026-10-01')
        HealthRecord.objects.create(user=self.other, weight_kg=50, bmi=20, recorded_date='2026-10-01')

        # One completed plan with two logs, one planned, one cancelled
        done = self.create_plan(status='COMPLETED')
        d1 = self.add_detail(done, order=1)
        d2 = self.add_detail(done, exercise=self.shoulder, order=2)
        WorkoutLog.objects.create(user=self.user, workout_plan_detail=d1, actual_sets=4, actual_reps=9, duration_minutes=12)
        WorkoutLog.objects.create(user=self.user, workout_plan_detail=d2, actual_sets=3, actual_reps=10, duration_minutes=8)
        self.create_plan(name='Leg Day', workout_date='2026-10-07')
        self.create_plan(name='Cancelled', status='CANCELLED')

        res = self.client.get('/api/statistics/overview/')
        self.assertEqual(res.data['total_workouts'], 2)
        self.assertEqual(res.data['completed_workouts'], 1)
        self.assertEqual(res.data['total_training_minutes'], 20)
        self.assertEqual(res.data['total_calories_burned'], 72)
        self.assertEqual(res.data['starting_weight'], 72)
        self.assertEqual(res.data['current_weight'], 70.5)
        self.assertEqual(res.data['weight_change'], -1.5)
        self.assertEqual(res.data['bmi'], 24.98)

        res = self.client.get('/api/statistics/weight-progress/')
        self.assertEqual([r['weight'] for r in res.data], [72, 70.5])
        res = self.client.get('/api/statistics/weight-progress/?from=2026-09-15')
        self.assertEqual(len(res.data), 1)

        res = self.client.get('/api/statistics/workout-progress/')
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['exercises'], 2)
        self.assertEqual(res.data[0]['total_minutes'], 20)
        self.assertEqual(res.data[0]['total_calories'], 72)

    def test_no_token(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/statistics/overview/').status_code, 401)
