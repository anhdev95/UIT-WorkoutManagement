from rest_framework.routers import SimpleRouter

from .views import HealthRecordViewSet

router = SimpleRouter()
router.register('health-records', HealthRecordViewSet, basename='health-record')

urlpatterns = router.urls
