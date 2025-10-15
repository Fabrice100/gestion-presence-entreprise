"""
Tests simples et fonctionnels pour valider la structure.

Tests de base pour s'assurer que les composants principaux
fonctionnent correctement.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import EmployeeProfile, Department


class SimpleStructureTest(TestCase):
    """Tests de base de la structure du projet."""
    
    def test_user_creation(self):
        """Test simple de création d'utilisateur."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.get_full_name(), 'Test User')
    
    def test_department_creation(self):
        """Test simple de création de département."""
        dept = Department.objects.create(
            name='IT Department',
            description='Information Technology'
        )
        
        self.assertEqual(dept.name, 'IT Department')
        self.assertTrue(dept.is_active)
        self.assertEqual(str(dept), 'IT Department')
    
    def test_employee_profile_creation(self):
        """Test simple de création de profil employé."""
        user = User.objects.create_user(
            username='employee1',
            password='pass123'
        )
        
        dept = Department.objects.create(
            name='HR',
            description='Human Resources'
        )
        
        profile = EmployeeProfile.objects.create(
            user=user,
            employee_id='EMP001',
            department=dept
        )
        
        self.assertEqual(profile.employee_id, 'EMP001')
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.department, dept)
        self.assertTrue(profile.can_punch)
        
        # Test de la représentation string
        expected_str = f"{user.get_full_name()} (EMP001)"
        self.assertEqual(str(profile), expected_str)


class ModelsIntegrityTest(TestCase):
    """Tests d'intégrité des modèles."""
    
    def test_employee_id_unique(self):
        """Test que l'ID employé est unique."""
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        dept = Department.objects.create(name='Test Dept')
        
        # Créer premier profil
        EmployeeProfile.objects.create(
            user=user1,
            employee_id='EMP001',
            department=dept
        )
        
        # Tenter de créer second profil avec même ID
        with self.assertRaises(Exception):
            EmployeeProfile.objects.create(
                user=user2,
                employee_id='EMP001',  # ID en double
                department=dept
            )
    
    def test_user_profile_relationship(self):
        """Test de la relation user-profile."""
        user = User.objects.create_user(username='testuser', password='pass')
        dept = Department.objects.create(name='Test')
        
        profile = EmployeeProfile.objects.create(
            user=user,
            employee_id='EMP002',
            department=dept
        )
        
        # Test relation inverse
        self.assertEqual(user.employee_profile, profile)
        self.assertEqual(profile.user, user)


class BasicViewsTest(TestCase):
    """Tests de base des vues principales."""
    
    def test_login_page_loads(self):
        """Test que la page de connexion se charge."""
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
    
    def test_punch_page_requires_auth(self):
        """Test que la page de pointage nécessite une authentification."""
        response = self.client.get('/attendance/punch/')
        # Doit rediriger vers login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class SecurityTest(TestCase):
    """Tests de sécurité de base."""
    
    def test_password_hashing(self):
        """Test que les mots de passe sont hashés."""
        user = User.objects.create_user(
            username='secureuser',
            password='supersecret123'
        )
        
        # Le mot de passe ne doit pas être stocké en clair
        self.assertNotEqual(user.password, 'supersecret123')
        self.assertTrue(user.password.startswith('pbkdf2_'))
        
        # Mais doit pouvoir être vérifié
        self.assertTrue(user.check_password('supersecret123'))
        self.assertFalse(user.check_password('wrongpassword'))


class ConfigurationTest(TestCase):
    """Tests de configuration du système."""
    
    def test_company_settings_singleton(self):
        """Test du pattern singleton pour CompanySettings."""
        from attendance.admin_models import CompanySettings
        
        # Charger les settings (crée une instance si elle n'existe pas)
        settings1 = CompanySettings.load()
        settings2 = CompanySettings.load()
        
        # Doivent être la même instance
        self.assertEqual(settings1.id, settings2.id)
        self.assertEqual(settings1, settings2)
    
    def test_company_settings_defaults(self):
        """Test des valeurs par défaut des paramètres d'entreprise."""
        from attendance.admin_models import CompanySettings
        
        settings = CompanySettings.load()
        
        # Vérifier que les valeurs par défaut sont cohérentes
        self.assertIsNotNone(settings.company_name)
        self.assertGreater(settings.allowed_radius_meters, 0)
        self.assertGreater(settings.gps_accuracy_max_meters, 0)
        
        # Coordonnées GPS valides
        self.assertGreaterEqual(settings.site_center_latitude, -90)
        self.assertLessEqual(settings.site_center_latitude, 90)
        self.assertGreaterEqual(settings.site_center_longitude, -180)
        self.assertLessEqual(settings.site_center_longitude, 180)