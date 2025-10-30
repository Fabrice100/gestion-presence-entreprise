"""
Tests unitaires pour PunchService.

Ce module teste le service unifié de pointage pour s'assurer
qu'il respecte les principes SOLID et fonctionne correctement.

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time
from unittest.mock import Mock, patch

from accounts.models import EmployeeProfile, Department
from attendance.services import PunchService, PunchResult
from attendance.models import Attendance


class PunchServiceTest(TestCase):
    """Tests pour le PunchService unifié."""
    
    def setUp(self):
        """Configuration initiale des tests."""
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
    
    def test_punch_result_success(self):
        """Test du résultat de pointage réussi."""
        attendance = Mock()
        result = PunchResult(
            success=True,
            attendance=attendance,
            warning_message=None
        )
        
        self.assertTrue(result.is_success())
        self.assertFalse(result.has_error())
        self.assertFalse(result.has_warning())
        self.assertEqual(result.attendance, attendance)
    
    def test_punch_result_error(self):
        """Test du résultat de pointage avec erreur."""
        result = PunchResult(
            success=False,
            error_message="Erreur de validation"
        )
        
        self.assertFalse(result.is_success())
        self.assertTrue(result.has_error())
        self.assertEqual(result.error_message, "Erreur de validation")
    
    def test_punch_result_warning(self):
        """Test du résultat de pointage avec avertissement."""
        attendance = Mock()
        result = PunchResult(
            success=True,
            attendance=attendance,
            warning_message="GPS imprécis"
        )
        
        self.assertTrue(result.is_success())
        self.assertFalse(result.has_error())
        self.assertTrue(result.has_warning())
        self.assertEqual(result.warning_message, "GPS imprécis")
    
    @patch('attendance.services.CompanySettings.load')
    def test_create_punch_success(self, mock_settings):
        """Test de création de pointage réussie."""
        # Mock des settings
        mock_settings.return_value.site_center_latitude = 6.1304
        mock_settings.return_value.site_center_longitude = 1.2158
        mock_settings.return_value.allowed_radius_meters = 200
        mock_settings.return_value.gps_accuracy_max_meters = 100
        
        # Données GPS valides
        gps_data = {
            'latitude': 6.1304,
            'longitude': 1.2158,
            'accuracy': 10.0,
            'demo_mode': False
        }
        
        # Créer le service
        service = PunchService()
        
        # Exécuter le pointage
        result = service.create_punch(
            user=self.user,
            punch_type='in',
            gps_data=gps_data
        )
        
        # Vérifications
        self.assertTrue(result.is_success())
        self.assertIsNotNone(result.attendance)
        self.assertEqual(result.attendance.employee, self.user)
        self.assertEqual(result.attendance.punch_type, 'in')
        self.assertEqual(result.attendance.date, date.today())
    
    def test_create_punch_permission_denied(self):
        """Test de pointage refusé pour permissions insuffisantes."""
        # Désactiver le pointage pour cet utilisateur
        self.profile.can_punch = False
        self.profile.save()
        
        service = PunchService()
        gps_data = {'latitude': 6.1304, 'longitude': 1.2158, 'accuracy': 10.0}
        
        result = service.create_punch(
            user=self.user,
            punch_type='in',
            gps_data=gps_data
        )
        
        self.assertFalse(result.is_success())
        self.assertTrue(result.has_error())
        self.assertIn("pas autorisé", result.error_message)
    
    def test_create_punch_duplicate(self):
        """Test de pointage en doublon."""
        # Créer un pointage existant
        Attendance.objects.create(
            employee=self.user,
            date=date.today(),
            time=time(8, 0),
            punch_type='in',
            latitude=6.1304,
            longitude=1.2158,
            accuracy=10.0
        )
        
        service = PunchService()
        gps_data = {'latitude': 6.1304, 'longitude': 1.2158, 'accuracy': 10.0}
        
        result = service.create_punch(
            user=self.user,
            punch_type='in',
            gps_data=gps_data
        )
        
        self.assertFalse(result.is_success())
        self.assertTrue(result.has_error())
        self.assertIn("déjà effectué", result.error_message)
    
    def test_create_punch_out_without_in(self):
        """Test de pointage de sortie sans entrée."""
        service = PunchService()
        gps_data = {'latitude': 6.1304, 'longitude': 1.2158, 'accuracy': 10.0}
        
        result = service.create_punch(
            user=self.user,
            punch_type='out',
            gps_data=gps_data
        )
        
        self.assertFalse(result.is_success())
        self.assertTrue(result.has_error())
        self.assertIn("d'abord pointer l'entrée", result.error_message)
    
    def test_get_next_punch_type_first_punch(self):
        """Test du prochain type de pointage (premier pointage)."""
        service = PunchService()
        next_type = service.get_next_punch_type(self.user)
        self.assertEqual(next_type, 'in')
    
    def test_get_next_punch_type_after_in(self):
        """Test du prochain type de pointage après entrée."""
        # Créer un pointage d'entrée
        Attendance.objects.create(
            employee=self.user,
            date=date.today(),
            time=time(8, 0),
            punch_type='in',
            latitude=6.1304,
            longitude=1.2158,
            accuracy=10.0
        )
        
        service = PunchService()
        next_type = service.get_next_punch_type(self.user)
        self.assertEqual(next_type, 'out')
    
    def test_get_today_attendances(self):
        """Test de récupération des pointages du jour."""
        # Créer des pointages
        Attendance.objects.create(
            employee=self.user,
            date=date.today(),
            time=time(8, 0),
            punch_type='in',
            latitude=6.1304,
            longitude=1.2158,
            accuracy=10.0
        )
        
        Attendance.objects.create(
            employee=self.user,
            date=date.today(),
            time=time(17, 0),
            punch_type='out',
            latitude=6.1304,
            longitude=1.2158,
            accuracy=10.0
        )
        
        service = PunchService()
        attendances = service.get_today_attendances(self.user)
        
        self.assertEqual(attendances.count(), 2)
        self.assertEqual(attendances.first().punch_type, 'in')
        self.assertEqual(attendances.last().punch_type, 'out')
    
    def test_can_user_punch(self):
        """Test de vérification des permissions de pointage."""
        service = PunchService()
        can_punch, error = service.can_user_punch(self.user)
        
        self.assertTrue(can_punch)
        self.assertIsNone(error)
    
    def test_can_user_punch_denied(self):
        """Test de vérification des permissions refusées."""
        self.profile.can_punch = False
        self.profile.save()
        
        service = PunchService()
        can_punch, error = service.can_user_punch(self.user)
        
        self.assertFalse(can_punch)
        self.assertIsNotNone(error)


class PunchServiceIntegrationTest(TestCase):
    """Tests d'intégration pour PunchService."""
    
    def setUp(self):
        """Configuration pour les tests d'intégration."""
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
    
    @patch('attendance.services.CompanySettings.load')
    def test_full_punch_workflow(self, mock_settings):
        """Test du workflow complet de pointage."""
        # Mock des settings
        mock_settings.return_value.site_center_latitude = 6.1304
        mock_settings.return_value.site_center_longitude = 1.2158
        mock_settings.return_value.allowed_radius_meters = 200
        mock_settings.return_value.gps_accuracy_max_meters = 100
        
        service = PunchService()
        gps_data = {
            'latitude': 6.1304,
            'longitude': 1.2158,
            'accuracy': 10.0,
            'demo_mode': False
        }
        
        # 1. Pointage d'entrée
        result_in = service.create_punch(
            user=self.user,
            punch_type='in',
            gps_data=gps_data
        )
        
        self.assertTrue(result_in.is_success())
        self.assertEqual(result_in.attendance.punch_type, 'in')
        
        # 2. Vérifier le prochain type
        next_type = service.get_next_punch_type(self.user)
        self.assertEqual(next_type, 'out')
        
        # 3. Pointage de sortie
        result_out = service.create_punch(
            user=self.user,
            punch_type='out',
            gps_data=gps_data
        )
        
        self.assertTrue(result_out.is_success())
        self.assertEqual(result_out.attendance.punch_type, 'out')
        
        # 4. Vérifier les pointages du jour
        attendances = service.get_today_attendances(self.user)
        self.assertEqual(attendances.count(), 2)



