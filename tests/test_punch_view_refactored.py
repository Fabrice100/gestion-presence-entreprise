"""
Tests pour PunchView refactorisée.

Ce module teste que PunchView utilise correctement PunchService
et que la refactorisation fonctionne comme attendu.

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, Mock

from accounts.models import EmployeeProfile, Department


class PunchViewRefactoredTest(TestCase):
    """Tests pour PunchView refactorisée."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        self.client = Client()
        
        # Créer un département
        self.dept = Department.objects.create(
            name='Test Department',
            description='Département de test'
        )
        
        # Créer un utilisateur employé
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        
        # Configurer le profil employé
        self.profile = self.user.employee_profile
        self.profile.employee_id = 'EMP001'
        self.profile.department = self.dept
        self.profile.role = 'employee'
        self.profile.can_punch = True
        self.profile.is_active = True
        self.profile.save()
        
        # Se connecter
        self.client.force_login(self.user)
    
    def test_punch_view_get(self):
        """Test que la page de pointage se charge correctement."""
        response = self.client.get(reverse('attendance:punch'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pointage')
    
    @patch('attendance.services.PunchService')
    def test_punch_view_post_success(self, mock_punch_service):
        """Test de pointage réussi avec PunchService."""
        # Mock du service
        mock_result = Mock()
        mock_result.is_success.return_value = True
        mock_result.has_warning.return_value = False
        mock_result.attendance = Mock()
        mock_result.attendance.punch_type = 'in'
        mock_result.attendance.time.strftime.return_value = '08:30'
        
        mock_service_instance = Mock()
        mock_service_instance.create_punch.return_value = mock_result
        mock_punch_service.return_value = mock_service_instance
        
        # Données de test
        data = {
            'punch_type': 'in',
            'latitude': '6.1304',
            'longitude': '1.2158',
            'accuracy': '10.0',
            'demo_mode': 'false'
        }
        
        # POST vers la vue
        response = self.client.post(reverse('attendance:punch'), data)
        
        # Vérifications
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertRedirects(response, reverse('attendance:punch'))
        
        # Vérifier que le service a été appelé
        mock_service_instance.create_punch.assert_called_once()
        
        # Vérifier les arguments passés au service
        call_args = mock_service_instance.create_punch.call_args
        self.assertEqual(call_args[1]['user'], self.user)
        self.assertEqual(call_args[1]['punch_type'], 'in')
        self.assertIn('latitude', call_args[1]['gps_data'])
        self.assertIn('ip_address', call_args[1]['request_meta'])
    
    @patch('attendance.services.PunchService')
    def test_punch_view_post_error(self, mock_punch_service):
        """Test de pointage avec erreur."""
        # Mock du service avec erreur
        mock_result = Mock()
        mock_result.is_success.return_value = False
        mock_result.has_error.return_value = True
        mock_result.error_message = "Erreur de validation GPS"
        
        mock_service_instance = Mock()
        mock_service_instance.create_punch.return_value = mock_result
        mock_punch_service.return_value = mock_service_instance
        
        # Données de test
        data = {
            'punch_type': 'in',
            'latitude': '6.1304',
            'longitude': '1.2158',
            'accuracy': '10.0',
            'demo_mode': 'false'
        }
        
        # POST vers la vue
        response = self.client.post(reverse('attendance:punch'), data)
        
        # Vérifications
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertRedirects(response, reverse('attendance:punch'))
        
        # Vérifier que le service a été appelé
        mock_service_instance.create_punch.assert_called_once()
    
    @patch('attendance.services.PunchService')
    def test_punch_view_post_with_warning(self, mock_punch_service):
        """Test de pointage avec avertissement GPS."""
        # Mock du service avec avertissement
        mock_result = Mock()
        mock_result.is_success.return_value = True
        mock_result.has_warning.return_value = True
        mock_result.warning_message = "Géolocalisation non disponible"
        mock_result.attendance = Mock()
        mock_result.attendance.punch_type = 'in'
        mock_result.attendance.time.strftime.return_value = '08:30'
        
        mock_service_instance = Mock()
        mock_service_instance.create_punch.return_value = mock_result
        mock_punch_service.return_value = mock_service_instance
        
        # Données de test
        data = {
            'punch_type': 'in',
            'latitude': '6.1304',
            'longitude': '1.2158',
            'accuracy': '10.0',
            'demo_mode': 'false'
        }
        
        # POST vers la vue
        response = self.client.post(reverse('attendance:punch'), data)
        
        # Vérifications
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertRedirects(response, reverse('attendance:punch'))
        
        # Vérifier que le service a été appelé
        mock_service_instance.create_punch.assert_called_once()
    
    def test_punch_view_form_validation_error(self):
        """Test de validation de formulaire échouée."""
        # Données invalides (punch_type manquant)
        data = {
            'latitude': '6.1304',
            'longitude': '1.2158',
            'accuracy': '10.0',
            'demo_mode': 'false'
        }
        
        # POST vers la vue
        response = self.client.post(reverse('attendance:punch'), data)
        
        # Vérifications
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertRedirects(response, reverse('attendance:punch'))
    
    def test_punch_view_requires_authentication(self):
        """Test que la vue nécessite une authentification."""
        # Se déconnecter
        self.client.logout()
        
        # Tentative d'accès
        response = self.client.get(reverse('attendance:punch'))
        
        # Doit rediriger vers la page d'authentification (dashboard intermédiaire)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            any(path in response.url for path in ['/accounts/login/', '/dashboard/']),
            msg=f"Redirection inattendue vers {response.url}",
        )


class PunchViewIntegrationTest(TestCase):
    """Tests d'intégration pour PunchView refactorisée."""
    
    def setUp(self):
        """Configuration pour les tests d'intégration."""
        self.client = Client()
        
        self.dept = Department.objects.create(name='IT')
        
        self.user = User.objects.create_user(
            username='integration_test',
            password='testpass',
            email='integration@test.com'
        )
        
        self.profile = self.user.employee_profile
        self.profile.employee_id = 'EMP999'
        self.profile.department = self.dept
        self.profile.role = 'employee'
        self.profile.can_punch = True
        self.profile.is_active = True
        self.profile.save()
        
        self.client.force_login(self.user)
    
    @patch('attendance.services.CompanySettings.load')
    def test_full_punch_workflow_integration(self, mock_settings):
        """Test d'intégration du workflow complet de pointage."""
        # Mock des settings
        mock_settings.return_value.site_center_latitude = 6.1304
        mock_settings.return_value.site_center_longitude = 1.2158
        mock_settings.return_value.allowed_radius_meters = 200
        mock_settings.return_value.gps_accuracy_max_meters = 100
        
        # 1. Pointage d'entrée
        data_in = {
            'punch_type': 'in',
            'latitude': '6.1304',
            'longitude': '1.2158',
            'accuracy': '10.0',
            'demo_mode': 'false'
        }
        
        response_in = self.client.post(reverse('attendance:punch'), data_in)
        self.assertEqual(response_in.status_code, 302)
        
        # 2. Pointage de sortie
        data_out = {
            'punch_type': 'out',
            'latitude': '6.1304',
            'longitude': '1.2158',
            'accuracy': '10.0',
            'demo_mode': 'false'
        }
        
        response_out = self.client.post(reverse('attendance:punch'), data_out)
        self.assertEqual(response_out.status_code, 302)
        
        # 3. Vérifier que les pointages ont été créés
        from attendance.models import Attendance
        attendances = Attendance.objects.filter(employee=self.user)
        self.assertEqual(attendances.count(), 2)
        
        # Vérifier les types de pointage
        punch_types = list(attendances.values_list('punch_type', flat=True))
        self.assertIn('in', punch_types)
        self.assertIn('out', punch_types)
