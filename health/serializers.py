from django.utils import timezone
from rest_framework import serializers

from .models import HealthRecord


class HealthRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthRecord
        fields = [
            'id', 'weight_kg', 'bmi', 'body_fat_percent', 'waist_cm',
            'note', 'recorded_date', 'created_at',
        ]
        read_only_fields = ['id', 'bmi', 'created_at']

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError('Cân nặng phải lớn hơn 0.')
        return value

    def validate_body_fat_percent(self, value):
        if value is not None and not (0 < value < 100):
            raise serializers.ValidationError('Tỷ lệ mỡ phải nằm trong khoảng (0, 100).')
        return value

    def validate_waist_cm(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Vòng eo phải lớn hơn 0.')
        return value

    def validate_recorded_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('Ngày ghi nhận không được ở tương lai.')
        return value

    def validate(self, attrs):
        # BMI needs the height stored in the user's profile.
        user = self.context['request'].user
        profile = getattr(user, 'profile', None)
        height_cm = profile.height_cm if profile else None
        if not height_cm:
            raise serializers.ValidationError(
                {'height_cm': 'Vui lòng cập nhật chiều cao trong hồ sơ trước khi ghi chỉ số sức khỏe.'}
            )

        weight_kg = attrs.get('weight_kg', getattr(self.instance, 'weight_kg', None))
        attrs['bmi'] = HealthRecord.calculate_bmi(weight_kg, height_cm)
        return attrs
