from django.db.models import Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import User, UserProfile
from .permissions import IsAdminRole
from .serializers import (
    AdminUserSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserStatusSerializer,
)


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/"""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET / PUT / PATCH /api/profile/ - profile of the logged-in user."""

    serializer_class = ProfileSerializer

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET   /api/admin/users/
    GET   /api/admin/users/{id}/
    PATCH /api/admin/users/{id}/status/
    """

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        queryset = User.objects.select_related('profile').order_by('id')
        params = self.request.query_params

        role = params.get('role')
        if role:
            queryset = queryset.filter(role=role.upper())

        search = params.get('search')
        if search:
            queryset = queryset.filter(Q(username__icontains=search) | Q(email__icontains=search))
        return queryset

    @action(detail=True, methods=['patch'], url_path='status')
    def set_status(self, request, pk=None):
        user = self.get_object()
        serializer = UserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if user.is_admin_role:
            return Response(
                {'detail': 'Không thể khóa/mở tài khoản Admin.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = serializer.validated_data['is_active']
        user.save(update_fields=['is_active'])
        return Response(AdminUserSerializer(user).data)
