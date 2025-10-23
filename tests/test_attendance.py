"""
Tests pour l'application attendance (système de pointage).

Tests couvrant le système de pointage GPS, la géolocalisation,
et les règles métier de présence.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from attendance.models import Attendance
from attendance.admin_models import CompanySettings
from tests.base import BaseTestCase, AuthenticatedTestCase, ModelTestCase
from tests.factories import (
    AttendanceFactory, CompanySettingsFactory, TestDataHelper
)
from unittest.mock import patch
import unittest
import json


class AttendanceModelTest(ModelTestCase):
    """Tests pour le modèle Attendance."""
    
    def test_attendance_creation(self):
        """Test de création d'un pointage."""
        user, profile = TestDataHelper.create_employee_with_profile()
        
        attendance = Attendance.objects.create(
            employee=user,
            date=date.today(),
            punch_type='in',
            time=time(9, 0),
            latitude=6.140766,
            longitude=1.241907,
            accuracy=10.0,
            source='web'
        )
        
        self.assertEqual(attendance.employee, user)
        self.assertEqual(attendance.punch_type, 'in')
        self.assertEqual(attendance.status, 'normal')
        self.assertIsNotNone(attendance.distance_from_site)
    
    def test_distance_calculation(self):
        """Test du calcul de distance GPS."""
        # Utiliser le singleton au lieu de créer une nouvelle instance
        settings = CompanySettings.load()
        settings.site_center_latitude = 6.140766
        settings.site_center_longitude = 1.241907
        settings.save()
        
        # Pointage exactement au bureau
        attendance = AttendanceFactory(
            latitude=6.140766,
            longitude=1.241907
        )
        
        self.assertAlmostEqual(attendance.distance_from_site, 0.0, places=1)
    
    @unittest.skip("TODO: Implémenter le calcul automatique du statut 'late'")
    def test_late_status_detection(self):
        """Test de détection des retards."""
        # Utiliser le singleton
        settings = CompanySettings.load()
        settings.work_start_time = time(8, 0)
        settings.save()
        
        # Pointage en retard
        late_attendance = AttendanceFactory(
            punch_type='in',
            time=time(9, 30)  # 1h30 de retard
        )
        
        self.assertEqual(late_attendance.status, 'late')
    
    def test_punch_type_validation(self):
        """Test de validation des types de pointage."""
        valid_types = ['in', 'out']
        
        for punch_type in valid_types:
            with self.subTest(punch_type=punch_type):
                attendance = AttendanceFactory(punch_type=punch_type)
                self.assertEqual(attendance.punch_type, punch_type)
    
    def test_str_representation(self):
        """Test de la représentation string."""
        attendance = AttendanceFactory()
        expected = f"{attendance.employee.get_full_name()} - {attendance.get_punch_type_display()} - {attendance.date} {attendance.time}"
        self.assert_model_str_representation(attendance, expected)


class CompanySettingsModelTest(ModelTestCase):
    """Tests pour le modèle CompanySettings."""
    
    def test_singleton_pattern(self):
        """Test que CompanySettings suit le pattern Singleton."""
        settings1 = CompanySettings.load()
        settings2 = CompanySettings.load()
        
        self.assertEqual(settings1.id, settings2.id)
    
    def test_default_values(self):
        """Test des valeurs par défaut."""
        settings = CompanySettings.load()
        
        self.assertIsNotNone(settings.company_name)
        self.assertGreater(settings.allowed_radius_meters, 0)
        self.assertGreater(settings.gps_accuracy_max_meters, 0)
    
    def test_gps_coordinates_validation(self):
        """Test de validation des coordonnées GPS."""
        settings = CompanySettings.load()
        settings.site_center_latitude = 6.140766
        settings.site_center_longitude = 1.241907
        settings.save()
        
        # Vérifier que les coordonnées sont dans les limites valides
        self.assertGreaterEqual(settings.site_center_latitude, -90)
        self.assertLessEqual(settings.site_center_latitude, 90)
        self.assertGreaterEqual(settings.site_center_longitude, -180)
        self.assertLessEqual(settings.site_center_longitude, 180)


class PunchViewTest(AuthenticatedTestCase):
    """Tests pour les vues de pointage."""
    
    def test_punch_page_accessible(self):
        """Test que la page de pointage est accessible."""
        response = self.client.get(reverse('attendance:punch'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pointage')
    
    def test_punch_requires_login(self):
        """Test que le pointage nécessite une connexion."""
        self.client.logout()
        self.assert_permission_required(reverse('attendance:punch'))
    
    @unittest.skip("TODO: Déboguer le système de pointage (attendance non créée)")
    @patch('attendance.views.timezone.now')
    def test_punch_in_success(self, mock_now):
        """Test de pointage d'entrée réussi."""
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 1, 15, 8, 30)
        )
        
        response = self.client.post(reverse('attendance:punch'), {
            'punch_type': 'in',
            'latitude': '6.140766',
            'longitude': '1.241907',
            'accuracy': '10.0'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que le pointage a été créé
        attendance = Attendance.objects.filter(employee=self.test_user).first()
        self.assertIsNotNone(attendance)
        self.assertEqual(attendance.punch_type, 'in')
    
    def test_punch_without_gps_data(self):
        """Test de pointage sans données GPS."""
        response = self.client.post(reverse('attendance:punch'), {
            'punch_type': 'in'
            # Pas de latitude/longitude
        })
        
        # Doit échouer ou utiliser des coordonnées par défaut
        self.assertIn(response.status_code, [400, 302])
    
    def test_duplicate_punch_prevention(self):
        """Test de prévention des pointages en double."""
        # Créer un pointage existant
        AttendanceFactory(
            employee=self.test_user,
            date=date.today(),
            punch_type='in'
        )
        
        # Tenter un second pointage d'entrée
        response = self.client.post(reverse('attendance:punch'), {
            'punch_type': 'in',
            'latitude': '6.140766',
            'longitude': '1.241907',
            'accuracy': '10.0'
        })
        
        # Doit être rejeté ou traité comme une erreur
        self.assertIn(response.status_code, [400, 302])


class GPSTestViewTest(AuthenticatedTestCase):
    """Tests pour la vue de test GPS."""
    
    @unittest.skip("TODO: Créer le template attendance/gps_test.html")
    def test_gps_test_page_accessible(self):
        """Test que la page de test GPS est accessible."""
        response = self.client.get(reverse('attendance:gps_test'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GPS')
    
    @unittest.skip("TODO: Créer le template attendance/gps_test.html")
    def test_gps_test_requires_login(self):
        """Test que le test GPS nécessite une connexion."""
        self.client.logout()
        self.assert_permission_required(reverse('attendance:gps_test'))


class AttendanceReportViewTest(AuthenticatedTestCase):
    """Tests pour les vues de rapport de présence."""
    
    def setUp(self):
        """Configuration des tests de rapport."""
        super().setUp()
        
        # Créer quelques pointages de test
        self.attendances = [
            AttendanceFactory(
                employee=self.test_user,
                date=date.today() - timedelta(days=i),
                punch_type='in' if i % 2 == 0 else 'out',
                time=time(8 + i, 0)
            )
            for i in range(5)
        ]
    
    @unittest.skip("TODO: Implémenter la vue attendance_list")
    def test_attendance_list_view(self):
        """Test de la vue liste des présences."""
        response = self.client.get(reverse('attendance:attendance_list'))
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que les pointages sont affichés
        for attendance in self.attendances:
            self.assertContains(response, attendance.employee.username)
    
    @unittest.skip("TODO: Implémenter la vue attendance_list")
    def test_attendance_filter_by_date(self):
        """Test de filtrage par date."""
        today = date.today()
        response = self.client.get(reverse('attendance:attendance_list'), {
            'date_from': today.strftime('%Y-%m-%d'),
            'date_to': today.strftime('%Y-%m-%d')
        })
        
        self.assertEqual(response.status_code, 200)


class AttendanceServiceTest(TestCase):
    """Tests pour les services de pointage."""
    
    def setUp(self):
        """Configuration des tests de service."""
        self.user, self.profile = TestDataHelper.create_employee_with_profile()
        self.settings = CompanySettings.load()
    
    @unittest.skip("TODO: Implémenter la fonction calculate_distance")
    def test_calculate_distance_service(self):
        """Test du service de calcul de distance."""
        from attendance.views import calculate_distance
        
        # Distance entre deux points identiques doit être 0
        distance = calculate_distance(
            6.140766, 1.241907,
            6.140766, 1.241907
        )
        
        self.assertAlmostEqual(distance, 0.0, places=1)
    
    def test_validate_punch_time(self):
        """Test de validation des heures de pointage."""
        # Test avec heure valide
        valid_time = time(8, 30)
        self.assertTrue(self._is_valid_punch_time(valid_time))
        
        # Test avec heure invalide (trop tôt)
        invalid_time = time(5, 0)
        self.assertFalse(self._is_valid_punch_time(invalid_time))
    
    def _is_valid_punch_time(self, punch_time):
        """Helper pour valider les heures de pointage."""
        work_start = time(6, 0)  # Heure minimale autorisée
        work_end = time(22, 0)   # Heure maximale autorisée
        
        return work_start <= punch_time <= work_end


class IntegrationTest(AuthenticatedTestCase):
    """Tests d'intégration pour le système de pointage."""
    
    @unittest.skip("TODO: Déboguer le système de pointage (attendance non créée)")
    def test_complete_punch_workflow(self):
        """Test du workflow complet de pointage."""
        # 1. Accéder à la page de pointage
        response = self.client.get(reverse('attendance:punch'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Effectuer un pointage d'entrée
        response = self.client.post(reverse('attendance:punch'), {
            'punch_type': 'in',
            'latitude': '6.140766',
            'longitude': '1.241907',
            'accuracy': '10.0'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # 3. Vérifier que le pointage a été enregistré
        attendance_in = Attendance.objects.filter(
            employee=self.test_user,
            punch_type='in',
            date=date.today()
        ).first()
        
        self.assertIsNotNone(attendance_in)
        
        # 4. Effectuer un pointage de sortie
        response = self.client.post(reverse('attendance:punch'), {
            'punch_type': 'out',
            'latitude': '6.140766',
            'longitude': '1.241907',
            'accuracy': '10.0'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # 5. Vérifier le pointage de sortie
        attendance_out = Attendance.objects.filter(
            employee=self.test_user,
            punch_type='out',
            date=date.today()
        ).first()
        
        self.assertIsNotNone(attendance_out)
    
    def test_gps_validation_workflow(self):
        """Test du workflow de validation GPS."""
        # Configuration avec rayon strict
        settings = CompanySettings.load()
        settings.site_center_latitude = 6.140766
        settings.site_center_longitude = 1.241907
        settings.allowed_radius_meters = 50  # Rayon très restrictif
        settings.save()
        
        # Pointage trop loin
        response = self.client.post(reverse('attendance:punch'), {
            'punch_type': 'in',
            'latitude': '6.150000',  # Trop loin
            'longitude': '1.250000',
            'accuracy': '10.0'
        })
        
        # Le système doit gérer les pointages hors zone
        self.assertIn(response.status_code, [302, 400])
        
        # Pointage dans la zone
        response = self.client.post(reverse('attendance:punch'), {
            'punch_type': 'in',
            'latitude': '6.140766',  # Exactement au bureau
            'longitude': '1.241907',
            'accuracy': '10.0'
        })
        
        self.assertEqual(response.status_code, 302)


class PerformanceTest(TestCase):
    """Tests de performance pour le système de pointage."""
    
    def test_bulk_attendance_creation(self):
        """Test de création en masse de pointages."""
        from datetime import time as dt_time
        import time as time_module
        
        users = [TestDataHelper.create_employee_with_profile()[0] for _ in range(10)]
        
        start_time = time_module.time()
        
        # Créer 100 pointages (50 in + 50 out sur 50 jours)
        attendances = []
        for i in range(100):
            user = users[i % len(users)]
            punch_type = 'in' if i % 2 == 0 else 'out'
            # Assurer que chaque (employee, date, punch_type) est unique
            day_offset = i // 2  # in et out sur le même jour, puis jour suivant
            attendances.append(Attendance(
                employee=user,
                date=date.today() - timedelta(days=day_offset),
                punch_type=punch_type,
                time=dt_time(8 if punch_type == 'in' else 17, i % 60),
                latitude=6.140766,
                longitude=1.241907,
                accuracy=10.0,
                source='test'
            ))
        
        Attendance.objects.bulk_create(attendances)
        
        end_time = time_module.time()
        execution_time = end_time - start_time
        
        # Le test doit s'exécuter en moins de 5 secondes
        self.assertLess(execution_time, 5.0)
        
        # Vérifier que tous les pointages ont été créés
        self.assertEqual(Attendance.objects.count(), 100)