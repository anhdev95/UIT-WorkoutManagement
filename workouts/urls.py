from django.urls import path
from rest_framework.routers import SimpleRouter

from .statistics_views import StatisticsOverviewView, WeightProgressView, WorkoutProgressView
from .views import ExerciseViewSet, WorkoutLogViewSet, WorkoutPlanDetailViewSet, WorkoutPlanViewSet

router = SimpleRouter()
router.register('exercises', ExerciseViewSet, basename='exercise')
router.register('workout-plans', WorkoutPlanViewSet, basename='workout-plan')
router.register('workout-plan-details', WorkoutPlanDetailViewSet, basename='workout-plan-detail')
router.register('workout-logs', WorkoutLogViewSet, basename='workout-log')

urlpatterns = [
    path('statistics/overview/', StatisticsOverviewView.as_view(), name='statistics-overview'),
    path('statistics/weight-progress/', WeightProgressView.as_view(), name='statistics-weight-progress'),
    path('statistics/workout-progress/', WorkoutProgressView.as_view(), name='statistics-workout-progress'),
] + router.urls
