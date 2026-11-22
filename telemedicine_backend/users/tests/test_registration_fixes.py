"""
Test suite for registration fixes and improvements.
Tests atomic transactions, race conditions, and data integrity.
"""
from django.test import TestCase, TransactionTestCase, override_settings
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()
from users.models.profiles import DoctorProfile, PatientProfile, TMCProfile
from users.models.users import EmailVerificationOTP


class RegistrationTransactionTests(TransactionTestCase):
    """Test database transactions in registration."""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()
    
    def test_registration_creates_user_and_profile_atomically(self):
        """Test that user and profile are created atomically."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
            'phone_number': '+1234567890',
            'password': 'testpass123',
            'role': 'doctor'
        }
        
        response = self.client.post('/users/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created
        user = User.objects.get(email='john@test.com')
        self.assertTrue(user.is_doctor)
        self.assertFalse(user.is_patient)
        self.assertFalse(user.is_tmc_operator)
        self.assertFalse(user.is_email_verified)
        self.assertEqual(response.data["next_step"], "VERIFY_EMAIL")
        self.assertTrue(EmailVerificationOTP.objects.filter(user=user, consumed_at__isnull=True).exists())
        
        # Verify profile was created
        profile = DoctorProfile.objects.get(user=user)
        self.assertIsNotNone(profile)
    
    def test_duplicate_email_returns_error(self):
        """Test that duplicate email registration fails."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'duplicate@test.com',
            'phone_number': '+1234567890',
            'password': 'testpass123',
            'role': 'patient'
        }
        
        # First registration should succeed
        response1 = self.client.post('/users/register/', data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Second registration with same email should fail
        data['phone_number'] = '+9876543210'  # Different phone
        response2 = self.client.post('/users/register/', data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response2.data.get('error', {}))
    
    def test_duplicate_phone_returns_error(self):
        """Test that duplicate phone registration fails."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test1@test.com',
            'phone_number': '+1234567890',
            'password': 'testpass123',
            'role': 'patient'
        }
        
        # First registration should succeed
        response1 = self.client.post('/users/register/', data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Second registration with same phone should fail
        data['email'] = 'test2@test.com'  # Different email
        response2 = self.client.post('/users/register/', data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response2.data.get('error', {}))
    
    def test_patient_registration_with_optional_fields(self):
        """Test patient registration with optional fields."""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@test.com',
            'phone_number': '+1111111111',
            'password': 'testpass123',
            'role': 'patient',
            'gender': 'F',
            'age': 30,
            'address': '123 Main St'
        }
        
        response = self.client.post('/users/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email='jane@test.com')
        self.assertFalse(user.is_email_verified)
        self.assertEqual(response.data.get("next_step"), "VERIFY_EMAIL")
        self.assertTrue(
            EmailVerificationOTP.objects.filter(
                user=user,
                purpose=EmailVerificationOTP.Purpose.PATIENT_EMAIL_VERIFICATION,
                consumed_at__isnull=True,
            ).exists()
        )
        profile = PatientProfile.objects.get(user=user)
        
        self.assertEqual(profile.gender, 'F')
        self.assertEqual(profile.age, 30)
        self.assertEqual(profile.address, '123 Main St')

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_BASE_URL="http://localhost:3000",
    )
    def test_doctor_must_verify_email_before_login(self):
        data = {
            'first_name': 'Verify',
            'last_name': 'Doctor',
            'email': 'verifydoc@test.com',
            'phone_number': '+1111111112',
            'password': 'testpass123',
            'role': 'doctor'
        }
        register_response = self.client.post('/users/register/', data, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Verify your IRME doctor account")
        self.assertIn("/verify-email", mail.outbox[0].body)
        self.assertTrue(mail.outbox[0].alternatives)

        blocked_login = self.client.post('/users/login/', {
            'email': data['email'],
            'password': data['password'],
        }, format='json')
        self.assertEqual(blocked_login.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(blocked_login.data["next_step"], "VERIFY_EMAIL")

        otp = register_response.data["dev_otp"]
        verify_response = self.client.post('/users/verify-email/', {
            'email': data['email'],
            'otp': otp,
        }, format='json')
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, "Your IRME doctor email is verified")
        body_second = mail.outbox[1].body
        self.assertTrue("/doctor/profile" in body_second or "doctor%2Fprofile" in body_second)

        login_response = self.client.post('/users/login/', {
            'email': data['email'],
            'password': data['password'],
        }, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["doctor_onboarding"]["next_step"], "COMPLETE_PROFILE")

    @override_settings(
        DEBUG=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_BASE_URL="http://localhost:3000",
    )
    def test_patient_must_verify_email_before_login(self):
        data = {
            'first_name': 'Pat',
            'last_name': 'Verify',
            'email': 'verifypatient@test.com',
            'phone_number': '+1333333333',
            'password': 'testpass123',
            'role': 'patient',
            'gender': 'M',
            'age': 25,
            'address': 'Somewhere',
        }
        register_response = self.client.post('/users/register/', data, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Verify your IRME patient account")
        self.assertIn("/verify-email", mail.outbox[0].body)

        blocked_login = self.client.post('/users/login/', {
            'email': data['email'],
            'password': data['password'],
        }, format='json')
        self.assertEqual(blocked_login.status_code, status.HTTP_403_FORBIDDEN)

        otp = register_response.data["dev_otp"]
        verify_response = self.client.post('/users/verify-email/', {
            'email': data['email'],
            'otp': otp,
        }, format='json')
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, "Welcome to IRME — patient email verified")

        login_response = self.client.post('/users/login/', {
            'email': data['email'],
            'password': data['password'],
        }, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["user_type"], "patient")


class CacheKeyTests(TestCase):
    """Test standardized cache key strategies."""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()
    
    def test_registration_sets_user_cache_key(self):
        """Test that registration uses standardized cache keys."""
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'cachetest@test.com',
            'phone_number': '+2222222222',
            'password': 'testpass123',
            'role': 'doctor'
        }
        
        response = self.client.post('/users/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email='cachetest@test.com')
        
        # Check that standardized cache key was set
        cache_key = f"users:user:{user.id}"
        cached_value = cache.get(cache_key)
        self.assertIsNotNone(cached_value)
        self.assertEqual(cached_value, user.id)
    
    def test_profile_cache_key_standardized(self):
        """Test that profile uses standardized cache key."""
        # Create user and login
        user = User.objects.create_user(
            email='cacheprofile@test.com',
            password='testpass123',
            is_doctor=True
        )
        DoctorProfile.objects.create(user=user)
        
        # Login
        login_response = self.client.post('/users/login/', {
            'email': 'cacheprofile@test.com',
            'password': 'testpass123'
        }, format='json')
        
        token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Get profile
        response = self.client.get('/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check cache key
        cache_key = f"users:profile:{user.id}"
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)


class ProfileQueryOptimizationTests(TestCase):
    """Test query optimization with select_related."""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        
        # Create test user
        self.user = User.objects.create_user(
            email='querytest@test.com',
            password='testpass123',
            is_doctor=True
        )
        DoctorProfile.objects.create(user=self.user)
        
        # Login
        login_response = self.client.post('/users/login/', {
            'email': 'querytest@test.com',
            'password': 'testpass123'
        }, format='json')
        
        token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def test_profile_fetch_uses_select_related(self):
        """Test that profile fetch doesn't cause N+1 queries."""
        from django.test.utils import override_settings
        from django.db import connection
        
        # Clear queries
        connection.queries_log.clear()
        
        # Fetch profile
        response = self.client.get('/users/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Count queries - should be minimal (1-2 queries max)
        query_count = len(connection.queries)
        
        # With select_related, should be 1-2 queries
        # Without select_related, would be 2+ queries
        self.assertLessEqual(query_count, 3, 
            f"Too many queries ({query_count}). Expected 1-3, got {query_count}")


class DatabaseIndexTests(TestCase):
    """Test that database indexes are properly created."""
    
    def test_profile_indexes_exist(self):
        """Test that indexes exist on profile models."""
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check DoctorProfile indexes
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'users_doctorprofile'
                AND indexname LIKE '%specialty%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            self.assertGreater(len(indexes), 0, "Specialty index should exist")
            
            # Check PatientProfile indexes
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'users_patientprofile'
                AND indexname LIKE '%gender%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            self.assertGreater(len(indexes), 0, "Gender index should exist")

