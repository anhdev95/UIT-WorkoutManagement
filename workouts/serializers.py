from django.db.models import Max
from rest_framework import serializers

from .models import Exercise, WorkoutLog, WorkoutPlan, WorkoutPlanDetail


def validate_not_negative(value, label):
    if value is not None and value < 0:
        raise serializers.ValidationError(f'{label} không được âm.')
    return value


def validate_positive(value, label):
    if value is not None and value <= 0:
        raise serializers.ValidationError(f'{label} phải lớn hơn 0.')
    return value


class ExerciseSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'muscle_group', 'exercise_type', 'difficulty',
            'description', 'instruction', 'calories_per_minute', 'created_by', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def validate_calories_per_minute(self, value):
        return validate_not_negative(value, 'Calories mỗi phút')


class WorkoutPlanDetailSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    has_log = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutPlanDetail
        fields = [
            'id', 'workout_plan', 'exercise', 'exercise_name', 'order_number',
            'target_sets', 'target_reps', 'target_weight', 'rest_seconds', 'has_log',
        ]
        read_only_fields = ['id', 'workout_plan']
        extra_kwargs = {'order_number': {'required': False}}

    def get_has_log(self, obj):
        return hasattr(obj, 'log')

    def validate_order_number(self, value):
        if value < 1:
            raise serializers.ValidationError('Thứ tự phải lớn hơn hoặc bằng 1.')
        return value

    def validate_target_sets(self, value):
        return validate_positive(value, 'Số set')

    def validate_target_reps(self, value):
        return validate_positive(value, 'Số rep')

    def validate_target_weight(self, value):
        return validate_not_negative(value, 'Mức tạ')

    def validate_rest_seconds(self, value):
        return validate_not_negative(value, 'Thời gian nghỉ')

    def validate(self, attrs):
        # Plan is passed via context on create, or taken from the instance on update.
        plan = self.context.get('workout_plan') or self.instance.workout_plan
        if plan.status != WorkoutPlan.Status.PLANNED:
            raise serializers.ValidationError('Chỉ được chỉnh sửa bài tập khi lịch tập đang ở trạng thái PLANNED.')
        return attrs

    def create(self, validated_data):
        plan = self.context['workout_plan']
        if 'order_number' not in validated_data:
            current_max = plan.details.aggregate(m=Max('order_number'))['m'] or 0
            validated_data['order_number'] = current_max + 1
        return WorkoutPlanDetail.objects.create(workout_plan=plan, **validated_data)


class WorkoutPlanSerializer(serializers.ModelSerializer):
    details = WorkoutPlanDetailSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutPlan
        fields = ['id', 'name', 'workout_date', 'note', 'status', 'created_at', 'updated_at', 'details']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_status(self, value):
        plan = self.instance
        if plan is None:
            # New plans always start as PLANNED.
            if value != WorkoutPlan.Status.PLANNED:
                raise serializers.ValidationError('Lịch tập mới phải có trạng thái PLANNED.')
            return value

        if value == plan.status:
            return value
        if not plan.can_change_status(value):
            raise serializers.ValidationError(f'Không thể chuyển trạng thái từ {plan.status} sang {value}.')
        if value == WorkoutPlan.Status.COMPLETED and not plan.has_logs():
            raise serializers.ValidationError('Cần ghi kết quả ít nhất một bài tập trước khi hoàn thành lịch tập.')
        return value


class WorkoutLogSerializer(serializers.ModelSerializer):
    workout_plan_detail = serializers.PrimaryKeyRelatedField(
        queryset=WorkoutPlanDetail.objects.none(),
        error_messages={'does_not_exist': 'Không tìm thấy bài tập này trong lịch tập của bạn.'},
    )
    workout_plan = serializers.IntegerField(source='workout_plan_detail.workout_plan_id', read_only=True)
    exercise_name = serializers.CharField(source='workout_plan_detail.exercise.name', read_only=True)
    target_sets = serializers.IntegerField(source='workout_plan_detail.target_sets', read_only=True)
    target_reps = serializers.IntegerField(source='workout_plan_detail.target_reps', read_only=True)
    target_weight = serializers.FloatField(source='workout_plan_detail.target_weight', read_only=True)

    class Meta:
        model = WorkoutLog
        fields = [
            'id', 'workout_plan_detail', 'workout_plan', 'exercise_name',
            'target_sets', 'target_reps', 'target_weight',
            'actual_sets', 'actual_reps', 'actual_weight',
            'duration_minutes', 'calories_burned', 'note', 'completed_at',
        ]
        read_only_fields = ['id', 'calories_burned', 'completed_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only details from the current user's plans can be chosen.
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['workout_plan_detail'].queryset = WorkoutPlanDetail.objects.filter(
                workout_plan__user=request.user
            )

    def validate_actual_sets(self, value):
        return validate_positive(value, 'Số set thực tế')

    def validate_actual_reps(self, value):
        return validate_positive(value, 'Số rep thực tế')

    def validate_actual_weight(self, value):
        return validate_not_negative(value, 'Mức tạ thực tế')

    def validate_duration_minutes(self, value):
        return validate_positive(value, 'Thời gian tập')

    def validate_workout_plan_detail(self, detail):
        # Each planned exercise has at most one log.
        existing = WorkoutLog.objects.filter(workout_plan_detail=detail)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError('Bài tập này đã có kết quả, hãy cập nhật kết quả cũ.')
        return detail

    def validate(self, attrs):
        detail = attrs.get('workout_plan_detail') or self.instance.workout_plan_detail
        if detail.workout_plan.status == WorkoutPlan.Status.CANCELLED:
            raise serializers.ValidationError('Không thể ghi kết quả cho lịch tập đã hủy.')
        return attrs
