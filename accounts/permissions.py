from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRole(BasePermission):
    """Only users with role ADMIN."""

    message = 'Chỉ Admin mới được thực hiện thao tác này.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin_role)


class IsAdminRoleOrReadOnly(BasePermission):
    """Any logged-in user can read, only ADMIN can write."""

    message = 'Chỉ Admin mới được thêm, sửa hoặc xóa dữ liệu này.'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_admin_role
