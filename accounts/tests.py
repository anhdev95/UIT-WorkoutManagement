from rest_framework import status
from rest_framework.test import APITestCase

from .models import User, UserProfile


def create_user(username='duc', role=User.Role.USER, **kwargs):
    user = User.objects.create_user(
        username=username, email=f'{username}@example.com', password='12345678', role=role, **kwargs
    )
    UserProfile.objects.create(user=user)
    return user


class RegisterTests(APITestCase):
    url = '/api/auth/register/'

    def test_register_valid(self):
        res = self.client.post(self.url, {
            'username': 'duc', 'email': 'duc@example.com', 'password': '12345678', 'role': 'ADMIN',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', res.data)
        user = User.objects.get(username='duc')
        self.assertEqual(user.role, User.Role.USER)  # role from client is ignored
        self.assertTrue(user.check_password('12345678'))  # password is hashed
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_duplicate_username(self):
        create_user('duc')
        res = self.client.post(self.url, {'username': 'duc', 'email': 'new@example.com', 'password': '12345678'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email_case_insensitive(self):
        create_user('duc')
        res = self.client.post(self.url, {'username': 'other', 'email': 'DUC@example.com', 'password': '12345678'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data)

    def test_short_password(self):
        res = self.client.post(self.url, {'username': 'duc', 'email': 'duc@example.com', 'password': '123'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    url = '/api/auth/login/'

    def setUp(self):
        self.user = create_user('duc')

    def test_login_success_returns_jwt(self):
        res = self.client.post(self.url, {'username': 'duc', 'password': '12345678'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_login_wrong_password(self):
        res = self.client.post(self.url, {'username': 'duc', 'password': 'wrongpass'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_locked_user(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(self.url, {'username': 'duc', 'password': '12345678'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        refresh = self.client.post(self.url, {'username': 'duc', 'password': '12345678'}).data['refresh']
        res = self.client.post('/api/auth/token/refresh/', {'refresh': refresh})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

    def test_access_protected_api_with_token(self):
        access = self.client.post(self.url, {'username': 'duc', 'password': '12345678'}).data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        res = self.client.get('/api/profile/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class CreateSuperuserTests(APITestCase):
    def test_superuser_has_admin_role_and_profile(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin12345')
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(UserProfile.objects.filter(user=admin).exists())


class ProfileTests(APITestCase):
    url = '/api/profile/'

    def setUp(self):
        self.user = create_user('duc')
        self.client.force_authenticate(self.user)

    def test_get_profile(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'duc')
        self.assertEqual(res.data['role'], 'USER')

    def test_update_profile(self):
        res = self.client.put(self.url, {
            'full_name': 'Nguyễn Trần Đức', 'gender': 'MALE', 'date_of_birth': '2004-01-01',
            'height_cm': 168, 'fitness_goal': 'GAIN_MUSCLE', 'activity_level': 'MODERATE',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.height_cm, 168)
        self.assertEqual(self.user.profile.full_name, 'Nguyễn Trần Đức')

    def test_cannot_change_role_via_profile(self):
        self.client.patch(self.url, {'role': 'ADMIN'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.USER)

    def test_invalid_height(self):
        res = self.client.patch(self.url, {'height_cm': 0})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_future_date_of_birth(self):
        res = self.client.patch(self.url, {'date_of_birth': '2999-01-01'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_goal(self):
        res = self.client.patch(self.url, {'fitness_goal': 'FLY'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_token(self):
        self.client.force_authenticate(None)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminUserTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin12345')
        self.user = create_user('duc')
        self.other = create_user('lan')

    def test_admin_list_users(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/users/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)

    def test_admin_filter_users(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/users/?role=USER&search=lan')
        self.assertEqual([u['username'] for u in res.data], ['lan'])

    def test_admin_user_detail(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get(f'/api/admin/users/{self.user.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'duc')

    def test_user_cannot_list_users(self):
        self.client.force_authenticate(self.user)
        res = self.client.get('/api/admin/users/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_lock_and_unlock_user(self):
        self.client.force_authenticate(self.admin)
        res = self.client.patch(f'/api/admin/users/{self.user.id}/status/', {'is_active': False})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_active'])

        # Locked user cannot log in
        self.client.force_authenticate(None)
        res = self.client.post('/api/auth/login/', {'username': 'duc', 'password': '12345678'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.admin)
        res = self.client.patch(f'/api/admin/users/{self.user.id}/status/', {'is_active': True})
        self.assertTrue(res.data['is_active'])

    def test_locked_user_old_token_rejected(self):
        access = self.client.post('/api/auth/login/', {'username': 'duc', 'password': '12345678'}).data['access']
        self.user.is_active = False
        self.user.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(self.client.get('/api/profile/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_lock_admin(self):
        self.client.force_authenticate(self.admin)
        res = self.client.patch(f'/api/admin/users/{self.admin.id}/status/', {'is_active': False})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_lock(self):
        self.client.force_authenticate(self.user)
        res = self.client.patch(f'/api/admin/users/{self.other.id}/status/', {'is_active': False})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
