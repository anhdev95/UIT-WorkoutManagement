from django.contrib import admin

from .models import HealthRecord


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'recorded_date', 'weight_kg', 'bmi', 'body_fat_percent', 'waist_cm']
    list_filter = ['recorded_date']
