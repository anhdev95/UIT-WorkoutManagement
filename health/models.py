from django.conf import settings
from django.db import models
from django.utils import timezone


class HealthRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='health_records')
    weight_kg = models.FloatField()
    bmi = models.FloatField(blank=True, null=True)
    body_fat_percent = models.FloatField(blank=True, null=True)
    waist_cm = models.FloatField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    recorded_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_date', '-created_at']
        constraints = [
            models.CheckConstraint(condition=models.Q(weight_kg__gt=0), name='health_weight_positive'),
        ]

    @staticmethod
    def calculate_bmi(weight_kg, height_cm):
        """BMI = weight_kg / (height_m ^ 2), rounded to 2 decimals."""
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 2)

    def __str__(self):
        return f'{self.user.username} - {self.recorded_date}: {self.weight_kg} kg'
