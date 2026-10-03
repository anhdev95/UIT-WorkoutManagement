from django.contrib import admin

from .models import Exercise, WorkoutLog, WorkoutPlan, WorkoutPlanDetail


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'muscle_group', 'exercise_type', 'difficulty', 'calories_per_minute']
    list_filter = ['muscle_group', 'exercise_type', 'difficulty']
    search_fields = ['name']


class WorkoutPlanDetailInline(admin.TabularInline):
    model = WorkoutPlanDetail
    extra = 0


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'workout_date', 'status']
    list_filter = ['status', 'workout_date']
    inlines = [WorkoutPlanDetailInline]


@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ['workout_plan_detail', 'user', 'actual_sets', 'actual_reps', 'actual_weight', 'completed_at']
