from django.db.models import Count, Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from health.models import HealthRecord
from health.views import get_date_param

from .models import WorkoutLog, WorkoutPlan


class StatisticsOverviewView(APIView):
    """GET /api/statistics/overview/ - workout and health summary of the current user."""

    def get(self, request):
        user = request.user
        plans = WorkoutPlan.objects.filter(user=user)
        log_totals = WorkoutLog.objects.filter(user=user).aggregate(
            minutes=Sum('duration_minutes'), calories=Sum('calories_burned')
        )

        records = HealthRecord.objects.filter(user=user).order_by('recorded_date', 'created_at')
        first_record = records.first()
        last_record = records.last()

        starting_weight = first_record.weight_kg if first_record else None
        current_weight = last_record.weight_kg if last_record else None
        weight_change = None
        if first_record:
            weight_change = round(current_weight - starting_weight, 2)

        return Response({
            'total_workouts': plans.exclude(status=WorkoutPlan.Status.CANCELLED).count(),
            'completed_workouts': plans.filter(status=WorkoutPlan.Status.COMPLETED).count(),
            'total_training_minutes': log_totals['minutes'] or 0,
            'total_calories_burned': round(log_totals['calories'] or 0, 2),
            'starting_weight': starting_weight,
            'current_weight': current_weight,
            'weight_change': weight_change,
            'bmi': last_record.bmi if last_record else None,
        })


class WeightProgressView(APIView):
    """GET /api/statistics/weight-progress/?from=&to= - weight over time (oldest first)."""

    def get(self, request):
        records = HealthRecord.objects.filter(user=request.user).order_by('recorded_date', 'created_at')

        date_from = get_date_param(request, 'from')
        if date_from:
            records = records.filter(recorded_date__gte=date_from)

        date_to = get_date_param(request, 'to')
        if date_to:
            records = records.filter(recorded_date__lte=date_to)

        data = [
            {'date': record.recorded_date, 'weight': record.weight_kg, 'bmi': record.bmi}
            for record in records
        ]
        return Response(data)


class WorkoutProgressView(APIView):
    """GET /api/statistics/workout-progress/ - completed workouts over time (oldest first)."""

    def get(self, request):
        plans = (
            WorkoutPlan.objects.filter(user=request.user, status=WorkoutPlan.Status.COMPLETED)
            .annotate(
                exercises=Count('details'),
                total_minutes=Sum('details__log__duration_minutes'),
                total_calories=Sum('details__log__calories_burned'),
            )
            .order_by('workout_date', 'id')
        )

        data = [
            {
                'date': plan.workout_date,
                'name': plan.name,
                'exercises': plan.exercises,
                'total_minutes': plan.total_minutes or 0,
                'total_calories': round(plan.total_calories or 0, 2),
            }
            for plan in plans
        ]
        return Response(data)
