from django.conf import settings
from django.db import models


class Exercise(models.Model):
    class MuscleGroup(models.TextChoices):
        CHEST = 'CHEST', 'Chest'
        BACK = 'BACK', 'Back'
        LEGS = 'LEGS', 'Legs'
        SHOULDERS = 'SHOULDERS', 'Shoulders'
        ARMS = 'ARMS', 'Arms'
        CORE = 'CORE', 'Core'
        FULL_BODY = 'FULL_BODY', 'Full body'
        CARDIO = 'CARDIO', 'Cardio'

    class ExerciseType(models.TextChoices):
        STRENGTH = 'STRENGTH', 'Strength'
        CARDIO = 'CARDIO', 'Cardio'
        FLEXIBILITY = 'FLEXIBILITY', 'Flexibility'
        RECOVERY = 'RECOVERY', 'Recovery'

    class Difficulty(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Beginner'
        INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
        ADVANCED = 'ADVANCED', 'Advanced'

    name = models.CharField(max_length=100, unique=True)
    muscle_group = models.CharField(max_length=20, choices=MuscleGroup.choices)
    exercise_type = models.CharField(max_length=20, choices=ExerciseType.choices)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    instruction = models.TextField(blank=True, null=True)
    calories_per_minute = models.FloatField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='created_exercises',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkoutPlan(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    # Allowed status changes: PLANNED -> COMPLETED / CANCELLED. Other changes are rejected.
    ALLOWED_TRANSITIONS = {
        Status.PLANNED: {Status.COMPLETED, Status.CANCELLED},
        Status.COMPLETED: set(),
        Status.CANCELLED: set(),
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workout_plans')
    name = models.CharField(max_length=100)
    workout_date = models.DateField()
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PLANNED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-workout_date', '-created_at']

    def can_change_status(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS[self.status]

    def has_logs(self):
        return WorkoutLog.objects.filter(workout_plan_detail__workout_plan=self).exists()

    def __str__(self):
        return f'{self.name} ({self.workout_date})'


class WorkoutPlanDetail(models.Model):
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='details')
    # PROTECT: an exercise used in a plan cannot be deleted.
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name='plan_details')
    order_number = models.PositiveIntegerField()
    target_sets = models.PositiveIntegerField()
    target_reps = models.PositiveIntegerField()
    target_weight = models.FloatField(blank=True, null=True)
    rest_seconds = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['order_number', 'id']
        constraints = [
            models.CheckConstraint(condition=models.Q(order_number__gte=1), name='detail_order_min_1'),
            models.CheckConstraint(condition=models.Q(target_sets__gt=0), name='detail_sets_positive'),
            models.CheckConstraint(condition=models.Q(target_reps__gt=0), name='detail_reps_positive'),
        ]

    def __str__(self):
        return f'{self.workout_plan.name} - {self.exercise.name}'


class WorkoutLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workout_logs')
    # One actual result per planned exercise (plan vs actual is compared 1-1).
    workout_plan_detail = models.OneToOneField(WorkoutPlanDetail, on_delete=models.CASCADE, related_name='log')
    actual_sets = models.PositiveIntegerField()
    actual_reps = models.PositiveIntegerField()
    actual_weight = models.FloatField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(blank=True, null=True)
    calories_burned = models.FloatField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']
        constraints = [
            models.CheckConstraint(condition=models.Q(actual_sets__gt=0), name='log_sets_positive'),
            models.CheckConstraint(condition=models.Q(actual_reps__gt=0), name='log_reps_positive'),
        ]

    def calculate_calories(self):
        """calories = exercise.calories_per_minute * duration_minutes (None if data is missing)."""
        per_minute = self.workout_plan_detail.exercise.calories_per_minute
        if per_minute is None or not self.duration_minutes:
            return None
        return round(per_minute * self.duration_minutes, 2)

    def save(self, *args, **kwargs):
        self.calories_burned = self.calculate_calories()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Log of {self.workout_plan_detail}'
