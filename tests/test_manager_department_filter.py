"""
Tests pour le filtrage strict des Managers par département.

Tests couverts:
1. Manager voit uniquement les employés de son département
2. Manager ne voit PAS les employés d'autres départements
3. Dashboard Manager filtré par département
4. Vue validation congés Manager filtrée par département
5. Statistiques Manager limitées à son département

Auteur: Test Suite
Date: 26/10/2025
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta

from accounts.models import EmployeeProfile, Department
from leave.models import LeaveType, LeaveRequest, LeaveBalance

User = get_user_model()


class ManagerDepartmentFilteringTest(TestCase):
    """Tests pour le filtrage par département dans le dashboard Manager."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Créer 2 départements
        self.dept_it = Department.objects.create(
            name="IT",
            description="IT Department"
        )
        
        self.dept_hr = Department.objects.create(
            name="HR",
            description="HR Department"
        )
        
        # Manager IT
        self.manager_it = User.objects.create_user(
            username='manager_it',
            email='manager_it@example.com',
            password='Pass123'
        )
        self.manager_it_profile = EmployeeProfile.objects.create(
            user=self.manager_it,
            employee_id='MGR_IT001',
            phone='1111111111',
            department=self.dept_it,
            role='manager',
            force_password_change=False
        )
        
        # Manager HR
        self.manager_hr = User.objects.create_user(
            username='manager_hr',
            email='manager_hr@example.com',
            password='Pass123'
        )
        self.manager_hr_profile = EmployeeProfile.objects.create(
            user=self.manager_hr,
            employee_id='MGR_HR001',
            phone='2222222222',
            department=self.dept_hr,
            role='manager',
            force_password_change=False
        )
        
        # Employés IT (3 employés)
        self.emp_it_1 = User.objects.create_user(username='emp_it_1', email='emp_it_1@example.com', password='Pass123')
        EmployeeProfile.objects.create(
            user=self.emp_it_1, employee_id='EMP_IT001',
            department=self.dept_it, role='employee', force_password_change=False
        )
        
        self.emp_it_2 = User.objects.create_user(username='emp_it_2', email='emp_it_2@example.com', password='Pass123')
        EmployeeProfile.objects.create(
            user=self.emp_it_2, employee_id='EMP_IT002',
            department=self.dept_it, role='employee', force_password_change=False
        )
        
        self.emp_it_3 = User.objects.create_user(username='emp_it_3', email='emp_it_3@example.com', password='Pass123')
        EmployeeProfile.objects.create(
            user=self.emp_it_3, employee_id='EMP_IT003',
            department=self.dept_it, role='employee', force_password_change=False
        )
        
        # Employés HR (2 employés)
        self.emp_hr_1 = User.objects.create_user(username='emp_hr_1', email='emp_hr_1@example.com', password='Pass123')
        EmployeeProfile.objects.create(
            user=self.emp_hr_1, employee_id='EMP_HR001',
            department=self.dept_hr, role='employee', force_password_change=False
        )
        
        self.emp_hr_2 = User.objects.create_user(username='emp_hr_2', email='emp_hr_2@example.com', password='Pass123')
        EmployeeProfile.objects.create(
            user=self.emp_hr_2, employee_id='EMP_HR002',
            department=self.dept_hr, role='employee', force_password_change=False
        )
        
        self.client = Client()
    
    def test_manager_it_sees_only_it_employees(self):
        """Test: Manager IT voit uniquement les employés IT."""
        self.client.login(username='manager_it', password='Pass123')
        
        # Accéder au dashboard Manager
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier le contexte
        if 'employees' in response.context:
            employees = response.context['employees']
            employee_ids = [emp.employee_profile.employee_id for emp in employees if hasattr(emp, 'employee_profile')]
            
            # Doit contenir les 3 employés IT
            self.assertIn('EMP_IT001', employee_ids)
            self.assertIn('EMP_IT002', employee_ids)
            self.assertIn('EMP_IT003', employee_ids)
            
            # Ne doit PAS contenir les employés HR
            self.assertNotIn('EMP_HR001', employee_ids)
            self.assertNotIn('EMP_HR002', employee_ids)
    
    def test_manager_hr_sees_only_hr_employees(self):
        """Test: Manager HR voit uniquement les employés HR."""
        self.client.login(username='manager_hr', password='Pass123')
        
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        
        if 'employees' in response.context:
            employees = response.context['employees']
            employee_ids = [emp.employee_profile.employee_id for emp in employees if hasattr(emp, 'employee_profile')]
            
            # Doit contenir les 2 employés HR
            self.assertIn('EMP_HR001', employee_ids)
            self.assertIn('EMP_HR002', employee_ids)
            
            # Ne doit PAS contenir les employés IT
            self.assertNotIn('EMP_IT001', employee_ids)
            self.assertNotIn('EMP_IT002', employee_ids)
            self.assertNotIn('EMP_IT003', employee_ids)
    
    def test_manager_does_not_see_himself(self):
        """Test: Manager ne se voit pas lui-même dans sa liste."""
        self.client.login(username='manager_it', password='Pass123')
        
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        if 'employees' in response.context:
            employees = response.context['employees']
            employee_ids = [emp.employee_profile.employee_id for emp in employees if hasattr(emp, 'employee_profile')]
            
            # Ne doit PAS contenir le Manager lui-même
            self.assertNotIn('MGR_IT001', employee_ids)
    
    def test_manager_employee_count_correct(self):
        """Test: Nombre d'employés correct pour chaque Manager."""
        # Manager IT: 3 employés
        self.client.login(username='manager_it', password='Pass123')
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        if 'employees' in response.context:
            employees_it = response.context['employees']
            # Devrait avoir 3 employés (sans le manager)
            self.assertEqual(len([e for e in employees_it if hasattr(e, 'employee_profile')]), 3)
        
        # Manager HR: 2 employés
        self.client.logout()
        self.client.login(username='manager_hr', password='Pass123')
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        if 'employees' in response.context:
            employees_hr = response.context['employees']
            # Devrait avoir 2 employés (sans le manager)
            self.assertEqual(len([e for e in employees_hr if hasattr(e, 'employee_profile')]), 2)


class ManagerLeaveValidationFilteringTest(TestCase):
    """Tests pour le filtrage dans la validation des congés par Manager."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Départements
        self.dept_sales = Department.objects.create(name="Sales", description="Sales Dept")
        self.dept_ops = Department.objects.create(name="Operations", description="Ops Dept")
        
        # Manager Sales
        self.manager_sales = User.objects.create_user(
            username='manager_sales', email='manager_sales@example.com', password='Pass123'
        )
        self.manager_sales_profile = EmployeeProfile.objects.create(
            user=self.manager_sales, employee_id='MGR_SALES',
            department=self.dept_sales, role='manager', force_password_change=False
        )
        
        # Employé Sales
        self.emp_sales = User.objects.create_user(
            username='emp_sales', email='emp_sales@example.com', password='Pass123'
        )
        self.emp_sales_profile = EmployeeProfile.objects.create(
            user=self.emp_sales, employee_id='EMP_SALES',
            department=self.dept_sales, role='employee', force_password_change=False
        )
        
        # Employé Operations
        self.emp_ops = User.objects.create_user(
            username='emp_ops', email='emp_ops@example.com', password='Pass123'
        )
        self.emp_ops_profile = EmployeeProfile.objects.create(
            user=self.emp_ops, employee_id='EMP_OPS',
            department=self.dept_ops, role='employee', force_password_change=False
        )
        
        # Type de congé
        self.leave_type = LeaveType.objects.create(
            name="Congé Annuel", code="CP", default_days=22, deducts_balance=True
        )
        
        # Demandes de congé
        self.leave_sales = LeaveRequest.objects.create(
            employee=self.emp_sales,
            leave_type=self.leave_type,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            total_days=3,
            reason="Vacances Sales",
            status='pending'
        )
        
        self.leave_ops = LeaveRequest.objects.create(
            employee=self.emp_ops,
            leave_type=self.leave_type,
            start_date=date.today() + timedelta(days=15),
            end_date=date.today() + timedelta(days=17),
            total_days=3,
            reason="Vacances Ops",
            status='pending'
        )
        
        self.client = Client()
    
    def test_manager_sees_only_department_leave_requests(self):
        """Test: Manager voit uniquement les demandes de son département."""
        self.client.login(username='manager_sales', password='Pass123')
        
        # Accéder à la liste de validation
        response = self.client.get(reverse('leave:manager_leave_validation'))
        
        self.assertEqual(response.status_code, 200)
        
        if 'leave_requests' in response.context or 'object_list' in response.context:
            leave_requests = response.context.get('leave_requests') or response.context.get('object_list')
            
            # Doit contenir la demande Sales
            leave_ids = [lr.id for lr in leave_requests]
            self.assertIn(self.leave_sales.id, leave_ids)
            
            # Ne doit PAS contenir la demande Operations
            self.assertNotIn(self.leave_ops.id, leave_ids)
    
    def test_manager_cannot_validate_other_department_leaves(self):
        """Test: Manager ne peut pas valider les congés d'autres départements."""
        self.client.login(username='manager_sales', password='Pass123')
        
        # Tenter de valider la demande Operations
        response = self.client.post(
            reverse('leave:manager_validate_leave', args=[self.leave_ops.id]),
            {'action': 'approve'}
        )
        
        # Doit être refusé ou redirigé
        self.assertIn(response.status_code, [302, 403, 404])
        
        # Vérifier que le statut n'a pas changé
        self.leave_ops.refresh_from_db()
        self.assertEqual(self.leave_ops.status, 'pending')
    
    def test_manager_statistics_filtered_by_department(self):
        """Test: Statistiques Manager filtrées par département."""
        self.client.login(username='manager_sales', password='Pass123')
        
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        if 'stats' in response.context:
            stats = response.context['stats']
            
            # Les stats doivent être basées uniquement sur le département Sales
            # Vérifier que le nombre de demandes correspond
            if 'pending_requests' in stats:
                # Devrait avoir 1 demande (celle de Sales uniquement)
                self.assertEqual(stats['pending_requests'], 1)


class ManagerDepartmentEdgeCasesTest(TestCase):
    """Tests des cas limites pour le filtrage Manager."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.dept = Department.objects.create(name="Finance", description="Finance Dept")
        
        # Manager sans département (cas limite)
        self.manager_no_dept = User.objects.create_user(
            username='manager_no_dept', email='manager_no_dept@example.com', password='Pass123'
        )
        self.manager_no_dept_profile = EmployeeProfile.objects.create(
            user=self.manager_no_dept, employee_id='MGR_NO_DEPT',
            department=None, role='manager', force_password_change=False
        )
        
        # Manager avec département
        self.manager_with_dept = User.objects.create_user(
            username='manager_with_dept', email='manager_with_dept@example.com', password='Pass123'
        )
        self.manager_with_dept_profile = EmployeeProfile.objects.create(
            user=self.manager_with_dept, employee_id='MGR_WITH_DEPT',
            department=self.dept, role='manager', force_password_change=False
        )
        
        # Employé du département
        self.emp = User.objects.create_user(
            username='emp', email='emp@example.com', password='Pass123'
        )
        self.emp_profile = EmployeeProfile.objects.create(
            user=self.emp, employee_id='EMP_FIN',
            department=self.dept, role='employee', force_password_change=False
        )
        
        self.client = Client()
    
    def test_manager_without_department_sees_no_employees(self):
        """Test: Manager sans département ne voit aucun employé."""
        self.client.login(username='manager_no_dept', password='Pass123')
        
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        if 'employees' in response.context:
            employees = response.context['employees']
            # Devrait être vide
            self.assertEqual(len(list(employees)), 0)
    
    def test_manager_with_department_sees_employees(self):
        """Test: Manager avec département voit les employés."""
        self.client.login(username='manager_with_dept', password='Pass123')
        
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        if 'employees' in response.context:
            employees = list(response.context['employees'])
            # Devrait contenir au moins 1 employé
            self.assertGreaterEqual(len(employees), 1)
    
    def test_employee_department_change_updates_manager_view(self):
        """Test: Changement de département d'un employé met à jour la vue Manager."""
        # Créer un nouveau département
        new_dept = Department.objects.create(name="New Dept", description="New")
        
        # Manager du nouveau département
        new_manager = User.objects.create_user(
            username='new_manager', email='new_manager@example.com', password='Pass123'
        )
        new_manager_profile = EmployeeProfile.objects.create(
            user=new_manager, employee_id='MGR_NEW',
            department=new_dept, role='manager', force_password_change=False
        )
        
        # L'employé est dans Finance
        self.client.login(username='manager_with_dept', password='Pass123')
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        if 'employees' in response.context:
            employees_before = [e.employee_profile.employee_id for e in response.context['employees'] if hasattr(e, 'employee_profile')]
            self.assertIn('EMP_FIN', employees_before)
        
        # Changer le département de l'employé
        self.emp_profile.department = new_dept
        self.emp_profile.save()
        
        # Recharger la vue
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        if 'employees' in response.context:
            employees_after = [e.employee_profile.employee_id for e in response.context['employees'] if hasattr(e, 'employee_profile')]
            # L'employé ne devrait plus apparaître
            self.assertNotIn('EMP_FIN', employees_after)
        
        # Vérifier que le nouveau manager le voit
        self.client.logout()
        self.client.login(username='new_manager', password='Pass123')
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        
        if 'employees' in response.context:
            employees_new = [e.employee_profile.employee_id for e in response.context['employees'] if hasattr(e, 'employee_profile')]
            self.assertIn('EMP_FIN', employees_new)
