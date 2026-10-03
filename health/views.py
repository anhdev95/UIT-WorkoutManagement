from django.utils.dateparse import parse_date
from rest_framework import serializers, viewsets

from .models import HealthRecord
from .serializers import HealthRecordSerializer


def get_date_param(request, name):
    """Read a YYYY-MM-DD query param; return None if missing, 400 if invalid."""
    value = request.query_params.get(name)
    if not value:
        return None
    try:
        parsed = parse_date(value)
    except ValueError:
        parsed = None
    if parsed is None:
        raise serializers.ValidationError({name: 'Ngày không hợp lệ, định dạng đúng là YYYY-MM-DD.'})
    return parsed


class HealthRecordViewSet(viewsets.ModelViewSet):
    """CRUD /api/health-records/ - only records of the logged-in user."""

    serializer_class = HealthRecordSerializer

    def get_queryset(self):
        # Filtering by owner means other users' records return 404.
        queryset = HealthRecord.objects.filter(user=self.request.user)

        date_from = get_date_param(self.request, 'from')
        if date_from:
            queryset = queryset.filter(recorded_date__gte=date_from)

        date_to = get_date_param(self.request, 'to')
        if date_to:
            queryset = queryset.filter(recorded_date__lte=date_to)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
