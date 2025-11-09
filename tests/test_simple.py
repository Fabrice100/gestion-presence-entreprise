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
        
        # Le profil est créé automatiquement par le signal
        # On le récupère et le met à jour
        profile = user.employee_profile
        profile.employee_id = 'EMP001'
        profile.department = dept
        profile.save()
        
        self.assertEqual(profile.employee_id, 'EMP001')
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.department, dept)
        self.assertTrue(profile.can_punch)
        
        # Test de la représentation string
        # Format: "EMP001 - employee1"  (car pas de first/last name)
        expected_str = f"EMP001 - {user.username}"
        self.assertEqual(str(profile), expected_str)


class ModelsIntegrityTest(TestCase):
    """Tests d'intégrité des modèles."""
    
    def test_employee_id_unique(self):
        """Test que l'ID employé est unique."""
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        dept = Department.objects.create(name='Test Dept')
        
        # Récupérer les profils auto-créés et mettre à jour
        profile1 = user1.employee_profile
        profile1.employee_id = 'EMP001'
        profile1.department = dept
        profile1.save()
        
        # Tenter de mettre le même ID sur le second profil
        profile2 = user2.employee_profile
        profile2.employee_id = 'EMP001'  # ID en double
        profile2.department = dept
        
        with self.assertRaises(Exception):
            profile2.save()
    
    def test_user_profile_relationship(self):
        """Test de la relation user-profile."""
        user = User.objects.create_user(username='testuser', password='pass')
        dept = Department.objects.create(name='Test')
        
        # Récupérer le profil auto-créé
        profile = user.employee_profile
        profile.employee_id = 'EMP002'
        profile.department = dept
        profile.save()
        
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
        self.assertTrue(
            any(path in response.url for path in ['/accounts/login/', '/dashboard/']),
            msg=f"Redirection inattendue vers {response.url}",
        )


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
        
        # Vérifier que les valeurs par défaut GPS sont cohérentes
        # Note: Les horaires sont gérés par WorkSchedule (Profils Horaires)
        self.assertGreater(settings.allowed_radius_meters, 0)
        self.assertGreater(settings.gps_accuracy_max_meters, 0)
        self.assertIsNotNone(settings.gps_required)
        
        # Coordonnées GPS valides
        self.assertGreaterEqual(settings.site_center_latitude, -90)
        self.assertLessEqual(settings.site_center_latitude, 90)
        self.assertGreaterEqual(settings.site_center_longitude, -180)
        self.assertLessEqual(settings.site_center_longitude, 180)
