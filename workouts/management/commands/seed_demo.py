from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User, UserProfile
from health.models import HealthRecord
from workouts.models import Exercise, WorkoutLog, WorkoutPlan, WorkoutPlanDetail

EXERCISES = [
    # name, muscle_group, exercise_type, difficulty, calories_per_minute, description
    ('Bench Press', 'CHEST', 'STRENGTH', 'INTERMEDIATE', 6, 'Đẩy ngực với thanh đòn trên ghế phẳng.'),
    ('Incline Dumbbell Press', 'CHEST', 'STRENGTH', 'INTERMEDIATE', 6, 'Đẩy ngực trên với tạ đơn, ghế dốc 30–45 độ.'),
    ('Shoulder Press', 'SHOULDERS', 'STRENGTH', 'INTERMEDIATE', 5, 'Đẩy vai qua đầu với tạ đơn.'),
    ('Squat', 'LEGS', 'STRENGTH', 'INTERMEDIATE', 8, 'Gánh tạ đùi sau.'),
    ('Deadlift', 'BACK', 'STRENGTH', 'ADVANCED', 8, 'Kéo tạ từ sàn.'),
    ('Pull Up', 'BACK', 'STRENGTH', 'INTERMEDIATE', 7, 'Hít xà đơn.'),
    ('Bicep Curl', 'ARMS', 'STRENGTH', 'BEGINNER', 4, 'Cuốn tạ tay trước.'),
    ('Plank', 'CORE', 'STRENGTH', 'BEGINNER', 4, 'Giữ thẳng người trên khuỷu tay.'),
    ('Running', 'CARDIO', 'CARDIO', 'BEGINNER', 10, 'Chạy bộ.'),
    ('Yoga Stretching', 'FULL_BODY', 'FLEXIBILITY', 'BEGINNER', 3, 'Giãn cơ toàn thân.'),
]


class Command(BaseCommand):
    help = 'Create demo data: admin, users, exercises, health records and a completed workout.'

    def create_user(self, username, password, role, **profile):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@example.com', 'role': role, 'is_staff': role == User.Role.ADMIN,
                      'is_superuser': role == User.Role.ADMIN},
        )
        if created:
            user.set_password(password)
            user.save()
        UserProfile.objects.update_or_create(user=user, defaults=profile)
        return user

    @transaction.atomic
    def handle(self, *args, **options):
        admin = self.create_user('admin', 'admin12345', User.Role.ADMIN, full_name='Quản trị viên')
        duc = self.create_user(
            'duc', '12345678', User.Role.USER,
            full_name='Nguyễn Trần Đức', gender='MALE', date_of_birth=date(2004, 1, 1),
            height_cm=168, fitness_goal='GAIN_MUSCLE', activity_level='MODERATE',
        )
        self.create_user('lan', '12345678', User.Role.USER, full_name='Trần Thị Lan', height_cm=158)

        exercises = {}
        for name, muscle, ex_type, difficulty, cal, description in EXERCISES:
            exercises[name], _ = Exercise.objects.get_or_create(
                name=name,
                defaults={'muscle_group': muscle, 'exercise_type': ex_type, 'difficulty': difficulty,
                          'calories_per_minute': cal, 'description': description, 'created_by': admin},
            )

        for day, weight in [(date(2026, 9, 1), 72.0), (date(2026, 9, 15), 71.5)]:
            HealthRecord.objects.get_or_create(
                user=duc, recorded_date=day,
                defaults={'weight_kg': weight, 'bmi': HealthRecord.calculate_bmi(weight, 168)},
            )

        plan, created = WorkoutPlan.objects.get_or_create(
            user=duc, name='Push Day (tuần trước)', workout_date=date(2026, 9, 28),
        )
        if created:
            targets = [('Bench Press', 4, 10, 50, 90), ('Shoulder Press', 3, 10, 15, 60)]
            actuals = [(4, 9, 50, 12), (3, 10, 15, 8)]
            for order, (target, actual) in enumerate(zip(targets, actuals), start=1):
                name, sets, reps, weight, rest = target
                detail = WorkoutPlanDetail.objects.create(
                    workout_plan=plan, exercise=exercises[name], order_number=order,
                    target_sets=sets, target_reps=reps, target_weight=weight, rest_seconds=rest,
                )
                a_sets, a_reps, a_weight, minutes = actual
                WorkoutLog.objects.create(
                    user=duc, workout_plan_detail=detail, actual_sets=a_sets,
                    actual_reps=a_reps, actual_weight=a_weight, duration_minutes=minutes,
                )
            plan.status = WorkoutPlan.Status.COMPLETED
            plan.save()

        self.stdout.write(self.style.SUCCESS(
            'Demo data ready. Accounts: admin/admin12345 (ADMIN), duc/12345678, lan/12345678 (USER).'
        ))
