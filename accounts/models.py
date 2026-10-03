from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    """createsuperuser always creates an account with role ADMIN (and its profile)."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        user = super().create_superuser(username, email, password, **extra_fields)
        UserProfile.objects.create(user=user)
        return user


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        USER = 'USER', 'User'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)

    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'

    class FitnessGoal(models.TextChoices):
        LOSE_WEIGHT = 'LOSE_WEIGHT', 'Lose weight'
        GAIN_MUSCLE = 'GAIN_MUSCLE', 'Gain muscle'
        MAINTAIN = 'MAINTAIN', 'Maintain'
        IMPROVE_HEALTH = 'IMPROVE_HEALTH', 'Improve health'

    class ActivityLevel(models.TextChoices):
        LOW = 'LOW', 'Low'
        MODERATE = 'MODERATE', 'Moderate'
        HIGH = 'HIGH', 'High'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    height_cm = models.FloatField(blank=True, null=True)
    fitness_goal = models.CharField(max_length=20, choices=FitnessGoal.choices, blank=True, null=True)
    activity_level = models.CharField(max_length=10, choices=ActivityLevel.choices, blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(height_cm__isnull=True) | models.Q(height_cm__gt=0),
                name='profile_height_positive',
            ),
        ]

    def __str__(self):
        return f'Profile of {self.user.username}'
