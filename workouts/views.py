from django.db.models import ProtectedError, Q
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminRoleOrReadOnly
from health.views import get_date_param

from .models import Exercise, WorkoutLog, WorkoutPlan, WorkoutPlanDetail
from .serializers import (
    ExerciseSerializer,
    WorkoutLogSerializer,
    WorkoutPlanDetailSerializer,
    WorkoutPlanSerializer,
)


class ExerciseViewSet(viewsets.ModelViewSet):
    """
    GET /api/exercises/ (filter: muscle_group, exercise_type, difficulty, search)
    POST / PUT / PATCH / DELETE - ADMIN only.
    """

    serializer_class = ExerciseSerializer
    permission_classes = [IsAdminRoleOrReadOnly]

    def get_queryset(self):
        queryset = Exercise.objects.select_related('created_by')
        params = self.request.query_params

        for field in ['muscle_group', 'exercise_type', 'difficulty']:
            value = params.get(field)
            if value:
                queryset = queryset.filter(**{field: value.upper()})

        search = params.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        exercise = self.get_object()
        try:
            exercise.delete()
        except ProtectedError:
            return Response(
                {'detail': 'Không thể xóa bài tập đang được sử dụng trong lịch tập.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """
    CRUD /api/workout-plans/ (filter: status, date)
    GET / POST /api/workout-plans/{id}/exercises/
    """

    serializer_class = WorkoutPlanSerializer

    def get_queryset(self):
        # Only the current user's plans -> other users' plans return 404.
        queryset = WorkoutPlan.objects.filter(user=self.request.user).prefetch_related(
            'details__exercise', 'details__log'
        )

        plan_status = self.request.query_params.get('status')
        if plan_status:
            queryset = queryset.filter(status=plan_status.upper())

        workout_date = get_date_param(self.request, 'date')
        if workout_date:
            queryset = queryset.filter(workout_date=workout_date)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status=WorkoutPlan.Status.PLANNED)

    @action(detail=True, methods=['get', 'post'], url_path='exercises')
    def exercises(self, request, pk=None):
        plan = self.get_object()

        if request.method == 'GET':
            serializer = WorkoutPlanDetailSerializer(plan.details.all(), many=True)
            return Response(serializer.data)

        serializer = WorkoutPlanDetailSerializer(
            data=request.data, context={'request': request, 'workout_plan': plan}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WorkoutPlanDetailViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """GET / PUT / PATCH / DELETE /api/workout-plan-details/{id}/"""

    serializer_class = WorkoutPlanDetailSerializer

    def get_queryset(self):
        return WorkoutPlanDetail.objects.filter(workout_plan__user=self.request.user).select_related(
            'workout_plan', 'exercise'
        )

    def perform_destroy(self, instance):
        if instance.workout_plan.status != WorkoutPlan.Status.PLANNED:
            raise serializers.ValidationError(
                {'detail': 'Chỉ được xóa bài tập khi lịch tập đang ở trạng thái PLANNED.'}
            )
        instance.delete()


class WorkoutLogViewSet(viewsets.ModelViewSet):
    """CRUD /api/workout-logs/ - actual results of the current user."""

    serializer_class = WorkoutLogSerializer

    def get_queryset(self):
        return WorkoutLog.objects.filter(user=self.request.user).select_related(
            'workout_plan_detail__exercise', 'workout_plan_detail__workout_plan'
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
