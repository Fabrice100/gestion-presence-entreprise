"""
Tests pour le workflow de résolution des anomalies de pointage.

Tests couverts:
1. Manager peut résoudre anomalies de son département
2. RH peut résoudre toutes les anomalies
3. Actions: justified, resolved, ignored
4. Traçabilité: resolved_by, resolved_at, justification
5. Permissions et filtrage par département

Auteur: Test Suite
Date: 26/10/2025
"""

import unittest

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, time

from attendance.models import Attendance
from accounts.models import EmployeeProfile, Department

User = get_user_model()


@unittest.skip("Le module d'anomalies de pointage n'est plus actif dans l'application actuelle.")
class AnomalyResolutionPermissionsTest(TestCase):
    """Tests pour les permissions de résolution d'anomalies."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Départements
        self.dept_it = Department.objects.create(name="IT", description="IT Dept")
        self.dept_hr = Department.objects.create(name="HR", description="HR Dept")
        
        # Manager IT
        self.manager_it = User.objects.create_user(
            username='manager_it', email='manager_it@example.com', password='Pass123'
        )
        self.manager_it_profile = EmployeeProfile.objects.create(
            user=self.manager_it, employee_id='MGR_IT',
            department=self.dept_it, role='manager', force_password_change=False
        )
        
        # RH
        self.rh = User.objects.create_user(
            username='rh', email='rh@example.com', password='Pass123'
        )
        self.rh_profile = EmployeeProfile.objects.create(
            user=self.rh, employee_id='RH001',
            department=self.dept_hr, role='rh', force_password_change=False
        )
        
        # Employé IT
        self.emp_it = User.objects.create_user(
            username='emp_it', email='emp_it@example.com', password='Pass123'
        )
        self.emp_it_profile = EmployeeProfile.objects.create(
            user=self.emp_it, employee_id='EMP_IT',
            department=self.dept_it, role='employee', force_password_change=False
        )
        
        # Employé HR
        self.emp_hr = User.objects.create_user(
            username='emp_hr', email='emp_hr@example.com', password='Pass123'
        )
        self.emp_hr_profile = EmployeeProfile.objects.create(
            user=self.emp_hr, employee_id='EMP_HR',
            department=self.dept_hr, role='employee', force_password_change=False
        )
        
        # Pointages avec anomalies
        self.attendance_it = Attendance.objects.create(
            employee=self.emp_it,
            date=date.today(),
            check_in=timezone.now().replace(hour=9, minute=30),  # Retard
            check_out=None,
            status='present'
        )
        
        self.anomaly_it = AttendanceAnomaly.objects.create(
            attendance=self.attendance_it,
            anomaly_type='late_arrival',
            description='Arrivée en retard de 30 minutes',
            status='pending'
        )
        
        self.attendance_hr = Attendance.objects.create(
            employee=self.emp_hr,
            date=date.today(),
            check_in=timezone.now().replace(hour=9, minute=0),
            check_out=None,
            status='present'
        )
        
        self.anomaly_hr = AttendanceAnomaly.objects.create(
            attendance=self.attendance_hr,
            anomaly_type='missing_punch_out',
            description='Oubli de pointage de sortie',
            status='pending'
        )
        
        self.client = Client()
    
    def test_manager_can_resolve_own_department_anomaly(self):
        """Test: Manager peut résoudre anomalie de son département."""
        self.client.login(username='manager_it', password='Pass123')
        
        # Résoudre l'anomalie IT
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly_it.id]),
            {
                'action': 'justified',
                'justification': 'Retard justifié - problème transport'
            }
        )
        
        # Vérifier la redirection (succès)
        self.assertEqual(response.status_code, 302)
        
        # Vérifier l'anomalie mise à jour
        self.anomaly_it.refresh_from_db()
        self.assertEqual(self.anomaly_it.status, 'justified')
        self.assertEqual(self.anomaly_it.justification, 'Retard justifié - problème transport')
        self.assertEqual(self.anomaly_it.resolved_by, self.manager_it)
        self.assertIsNotNone(self.anomaly_it.resolved_at)
    
    def test_manager_cannot_resolve_other_department_anomaly(self):
        """Test: Manager ne peut PAS résoudre anomalie d'autre département."""
        self.client.login(username='manager_it', password='Pass123')
        
        # Tenter de résoudre l'anomalie HR
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly_hr.id]),
            {
                'action': 'resolved',
                'justification': 'Tentative non autorisée'
            }
        )
        
        # Doit être refusé
        # La vue doit rediriger avec message d'erreur
        
        # Vérifier que l'anomalie n'a PAS été modifiée
        self.anomaly_hr.refresh_from_db()
        self.assertEqual(self.anomaly_hr.status, 'pending')
        self.assertIsNone(self.anomaly_hr.resolved_by)
    
    def test_rh_can_resolve_any_anomaly(self):
        """Test: RH peut résoudre n'importe quelle anomalie."""
        self.client.login(username='rh', password='Pass123')
        
        # Résoudre anomalie IT
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly_it.id]),
            {
                'action': 'resolved',
                'justification': 'Corrigé par RH'
            }
        )
        
        self.assertEqual(response.status_code, 302)
        self.anomaly_it.refresh_from_db()
        self.assertEqual(self.anomaly_it.status, 'resolved')
        self.assertEqual(self.anomaly_it.resolved_by, self.rh)
        
        # Résoudre anomalie HR
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly_hr.id]),
            {
                'action': 'ignored',
                'justification': 'Sans importance'
            }
        )
        
        self.assertEqual(response.status_code, 302)
        self.anomaly_hr.refresh_from_db()
        self.assertEqual(self.anomaly_hr.status, 'ignored')
        self.assertEqual(self.anomaly_hr.resolved_by, self.rh)
    
    def test_employee_cannot_resolve_anomalies(self):
        """Test: Employé ne peut PAS résoudre d'anomalies."""
        self.client.login(username='emp_it', password='Pass123')
        
        # Tenter de résoudre sa propre anomalie
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly_it.id]),
            {
                'action': 'justified',
                'justification': 'Tentative employé'
            }
        )
        
        # Doit être refusé (403 ou redirection)
        # Vérifier que l'anomalie n'a pas changé
        self.anomaly_it.refresh_from_db()
        self.assertEqual(self.anomaly_it.status, 'pending')


@unittest.skip("Le module d'anomalies de pointage n'est plus actif dans l'application actuelle.")
class AnomalyResolutionActionsTest(TestCase):
    """Tests pour les différentes actions de résolution."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.dept = Department.objects.create(name="Sales", description="Sales")
        
        self.manager = User.objects.create_user(
            username='manager', email='manager@example.com', password='Pass123'
        )
        self.manager_profile = EmployeeProfile.objects.create(
            user=self.manager, employee_id='MGR001',
            department=self.dept, role='manager', force_password_change=False
        )
        
        self.employee = User.objects.create_user(
            username='employee', email='employee@example.com', password='Pass123'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user=self.employee, employee_id='EMP001',
            department=self.dept, role='employee', force_password_change=False
        )
        
        self.attendance = Attendance.objects.create(
            employee=self.employee,
            date=date.today(),
            check_in=timezone.now().replace(hour=9, minute=30),
            check_out=None,
            status='present'
        )
        
        self.anomaly = AttendanceAnomaly.objects.create(
            attendance=self.attendance,
            anomaly_type='late_arrival',
            description='Retard',
            status='pending'
        )
        
        self.client = Client()
    
    def test_action_justified(self):
        """Test: Action 'justified' met le statut à justifié."""
        self.client.login(username='manager', password='Pass123')
        
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly.id]),
            {
                'action': 'justified',
                'justification': 'Employé a expliqué la situation'
            }
        )
        
        self.anomaly.refresh_from_db()
        self.assertEqual(self.anomaly.status, 'justified')
        self.assertIn('expliqué', self.anomaly.justification)
    
    def test_action_resolved(self):
        """Test: Action 'resolved' met le statut à résolu."""
        self.client.login(username='manager', password='Pass123')
        
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly.id]),
            {
                'action': 'resolved',
                'justification': 'Anomalie corrigée manuellement'
            }
        )
        
        self.anomaly.refresh_from_db()
        self.assertEqual(self.anomaly.status, 'resolved')
        self.assertIn('corrigée', self.anomaly.justification)
    
    def test_action_ignored(self):
        """Test: Action 'ignored' met le statut à ignoré."""
        self.client.login(username='manager', password='Pass123')
        
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly.id]),
            {
                'action': 'ignored',
                'justification': 'Anomalie sans importance'
            }
        )
        
        self.anomaly.refresh_from_db()
        self.assertEqual(self.anomaly.status, 'ignored')
        self.assertIn('sans importance', self.anomaly.justification)
    
    def test_invalid_action_rejected(self):
        """Test: Action invalide est rejetée."""
        self.client.login(username='manager', password='Pass123')
        
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly.id]),
            {
                'action': 'invalid_action',
                'justification': 'Test'
            }
        )
        
        # Anomalie ne doit pas changer
        self.anomaly.refresh_from_db()
        self.assertEqual(self.anomaly.status, 'pending')
    
    def test_empty_justification_rejected(self):
        """Test: Justification vide est rejetée."""
        self.client.login(username='manager', password='Pass123')
        
        response = self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly.id]),
            {
                'action': 'justified',
                'justification': ''
            }
        )
        
        # Anomalie ne doit pas changer
        self.anomaly.refresh_from_db()
        self.assertEqual(self.anomaly.status, 'pending')


@unittest.skip("Le module d'anomalies de pointage n'est plus actif dans l'application actuelle.")
class AnomalyListViewFilteringTest(TestCase):
    """Tests pour le filtrage des listes d'anomalies."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.dept_a = Department.objects.create(name="Dept A", description="A")
        self.dept_b = Department.objects.create(name="Dept B", description="B")
        
        # Manager A
        self.manager_a = User.objects.create_user(
            username='manager_a', email='manager_a@example.com', password='Pass123'
        )
        self.manager_a_profile = EmployeeProfile.objects.create(
            user=self.manager_a, employee_id='MGR_A',
            department=self.dept_a, role='manager', force_password_change=False
        )
        
        # RH
        self.rh = User.objects.create_user(
            username='rh', email='rh@example.com', password='Pass123'
        )
        self.rh_profile = EmployeeProfile.objects.create(
            user=self.rh, employee_id='RH001',
            department=self.dept_a, role='rh', force_password_change=False
        )
        
        # Employés
        self.emp_a = User.objects.create_user(username='emp_a', email='emp_a@example.com', password='Pass123')
        EmployeeProfile.objects.create(
            user=self.emp_a, employee_id='EMP_A',
            department=self.dept_a, role='employee', force_password_change=False
        )
        
        self.emp_b = User.objects.create_user(username='emp_b', email='emp_b@example.com', password='Pass123')
        EmployeeProfile.objects.create(
            user=self.emp_b, employee_id='EMP_B',
            department=self.dept_b, role='employee', force_password_change=False
        )
        
        # Anomalies
        att_a = Attendance.objects.create(
            employee=self.emp_a, date=date.today(),
            check_in=timezone.now().replace(hour=9, minute=0), status='present'
        )
        self.anomaly_a = AttendanceAnomaly.objects.create(
            attendance=att_a, anomaly_type='late_arrival',
            description='Retard A', status='pending'
        )
        
        att_b = Attendance.objects.create(
            employee=self.emp_b, date=date.today(),
            check_in=timezone.now().replace(hour=9, minute=0), status='present'
        )
        self.anomaly_b = AttendanceAnomaly.objects.create(
            attendance=att_b, anomaly_type='missing_punch_out',
            description='Oubli B', status='pending'
        )
        
        self.client = Client()
    
    def test_manager_list_filtered_by_department(self):
        """Test: Liste Manager filtrée par département."""
        self.client.login(username='manager_a', password='Pass123')
        
        response = self.client.get(reverse('attendance:manager_anomaly_list'))
        
        self.assertEqual(response.status_code, 200)
        
        if 'anomalies' in response.context or 'object_list' in response.context:
            anomalies = response.context.get('anomalies') or response.context.get('object_list')
            anomaly_ids = [a.id for a in anomalies]
            
            # Doit contenir anomalie A
            self.assertIn(self.anomaly_a.id, anomaly_ids)
            
            # Ne doit PAS contenir anomalie B
            self.assertNotIn(self.anomaly_b.id, anomaly_ids)
    
    def test_rh_list_shows_all_anomalies(self):
        """Test: Liste RH montre toutes les anomalies."""
        self.client.login(username='rh', password='Pass123')
        
        response = self.client.get(reverse('attendance:rh_anomaly_list'))
        
        self.assertEqual(response.status_code, 200)
        
        if 'anomalies' in response.context or 'object_list' in response.context:
            anomalies = response.context.get('anomalies') or response.context.get('object_list')
            anomaly_ids = [a.id for a in anomalies]
            
            # Doit contenir les deux anomalies
            self.assertIn(self.anomaly_a.id, anomaly_ids)
            self.assertIn(self.anomaly_b.id, anomaly_ids)
    
    def test_anomaly_list_statistics(self):
        """Test: Statistiques des anomalies correctes."""
        self.client.login(username='rh', password='Pass123')
        
        # Résoudre une anomalie
        self.anomaly_a.status = 'resolved'
        self.anomaly_a.save()
        
        response = self.client.get(reverse('attendance:rh_anomaly_list'))
        
        if 'stats' in response.context:
            stats = response.context['stats']
            
            # Vérifier les compteurs
            self.assertEqual(stats.get('pending', 0), 1)  # anomaly_b
            self.assertEqual(stats.get('resolved', 0), 1)  # anomaly_a
            self.assertEqual(stats.get('total', 0), 2)


@unittest.skip("Le module d'anomalies de pointage n'est plus actif dans l'application actuelle.")
class AnomalyTraceabilityTest(TestCase):
    """Tests pour la traçabilité des résolutions."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.dept = Department.objects.create(name="Test", description="Test")
        
        self.manager = User.objects.create_user(
            username='manager', email='manager@example.com', password='Pass123'
        )
        self.manager_profile = EmployeeProfile.objects.create(
            user=self.manager, employee_id='MGR',
            department=self.dept, role='manager', force_password_change=False
        )
        
        self.employee = User.objects.create_user(
            username='employee', email='employee@example.com', password='Pass123'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user=self.employee, employee_id='EMP',
            department=self.dept, role='employee', force_password_change=False
        )
        
        att = Attendance.objects.create(
            employee=self.employee, date=date.today(),
            check_in=timezone.now().replace(hour=9, minute=0), status='present'
        )
        self.anomaly = AttendanceAnomaly.objects.create(
            attendance=att, anomaly_type='late_arrival',
            description='Test', status='pending'
        )
        
        self.client = Client()
    
    def test_resolved_by_tracked(self):
        """Test: Utilisateur ayant résolu est tracké."""
        self.client.login(username='manager', password='Pass123')
        
        self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly.id]),
            {'action': 'justified', 'justification': 'OK'}
        )
        
        self.anomaly.refresh_from_db()
        self.assertEqual(self.anomaly.resolved_by, self.manager)
    
    def test_resolved_at_tracked(self):
        """Test: Date/heure de résolution est trackée."""
        self.client.login(username='manager', password='Pass123')
        
        before = timezone.now()
        
        self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly.id]),
            {'action': 'justified', 'justification': 'OK'}
        )
        
        after = timezone.now()
        
        self.anomaly.refresh_from_db()
        self.assertIsNotNone(self.anomaly.resolved_at)
        self.assertGreaterEqual(self.anomaly.resolved_at, before)
        self.assertLessEqual(self.anomaly.resolved_at, after)
    
    def test_justification_saved(self):
        """Test: Justification est sauvegardée."""
        self.client.login(username='manager', password='Pass123')
        
        justification_text = "Retard dû à un accident de circulation sur l'autoroute"
        
        self.client.post(
            reverse('attendance:resolve_anomaly', args=[self.anomaly.id]),
            {'action': 'justified', 'justification': justification_text}
        )
        
        self.anomaly.refresh_from_db()
        self.assertEqual(self.anomaly.justification, justification_text)
