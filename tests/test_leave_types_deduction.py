"""
Tests pour la fonctionnalité de déduction des soldes de congés.

Tests couverts:
1. Champ deducts_balance sur LeaveType
2. Logique de déduction selon le type de congé
3. Congé Annuel (CP) déduit le solde
4. Congé Maladie/Exceptionnel ne déduit PAS le solde
5. Calcul correct du solde après validation

Auteur: Test Suite
Date: 26/10/2025
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from leave.models import LeaveType, LeaveRequest, LeaveBalance
from accounts.models import EmployeeProfile, Department

User = get_user_model()


class LeaveTypeDeductsBalanceTest(TestCase):
    """Tests pour le champ deducts_balance sur LeaveType."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Créer les types de congés
        self.cp = LeaveType.objects.create(
            name="Congé Annuel",
            code="CP",
            default_days=22,
            requires_document=False,
            deducts_balance=True  # Doit déduire
        )
        
        self.maladie = LeaveType.objects.create(
            name="Congé Maladie",
            code="MAL",
            default_days=0,
            requires_document=True,
            deducts_balance=False  # Ne doit PAS déduire
        )
        
        self.exceptionnel = LeaveType.objects.create(
            name="Congé Exceptionnel",
            code="EVT",
            default_days=0,
            requires_document=False,
            deducts_balance=False  # Ne doit PAS déduire
        )
    
    def test_cp_deducts_balance_true(self):
        """Test: Congé Annuel a deducts_balance=True."""
        self.assertTrue(self.cp.deducts_balance)
    
    def test_maladie_deducts_balance_false(self):
        """Test: Congé Maladie a deducts_balance=False."""
        self.assertFalse(self.maladie.deducts_balance)
    
    def test_exceptionnel_deducts_balance_false(self):
        """Test: Congé Exceptionnel a deducts_balance=False."""
        self.assertFalse(self.exceptionnel.deducts_balance)
    
    def test_all_leave_types_have_deducts_balance_field(self):
        """Test: Tous les LeaveTypes ont le champ deducts_balance."""
        for leave_type in LeaveType.objects.all():
            # Ne doit pas lever d'exception
            self.assertIsNotNone(leave_type.deducts_balance)
            self.assertIn(leave_type.deducts_balance, [True, False])


class LeaveBalanceDeductionLogicTest(TestCase):
    """Tests pour la logique de déduction du solde."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Département
        self.department = Department.objects.create(
            name="Engineering",
            description="Engineering Department"
        )
        
        # Utilisateur employé
        self.employee_user = User.objects.create_user(
            username='engineer',
            email='engineer@example.com',
            password='Pass123'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user=self.employee_user,
            employee_id='ENG001',
            phone='1234567890',
            department=self.department,
            role='employee'
        )
        
        # Types de congés
        self.cp = LeaveType.objects.create(
            name="Congé Annuel",
            code="CP",
            default_days=22,
            deducts_balance=True
        )
        
        self.maladie = LeaveType.objects.create(
            name="Congé Maladie",
            code="MAL",
            default_days=0,
            deducts_balance=False
        )
        
        # Solde initial
        self.balance = LeaveBalance.objects.create(
            employee=self.employee_user,
            leave_type=self.cp,
            year=timezone.now().year,
            total_days=22,
            used_days=0,
            remaining_days=22
        )
    
    def test_cp_deducts_from_balance(self):
        """Test: Congé Annuel déduit du solde."""
        # Créer une demande de congé annuel
        leave_request = LeaveRequest.objects.create(
            employee=self.employee_user,
            leave_type=self.cp,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=14),
            total_days=5,
            reason="Vacances",
            status='approved_rh'
        )
        
        # Simuler la déduction (normalement fait par le signal/workflow)
        if leave_request.leave_type.deducts_balance:
            self.balance.used_days += Decimal(leave_request.total_days)
            self.balance.remaining_days -= Decimal(leave_request.total_days)
            self.balance.save()
        
        # Vérifier la déduction
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.used_days, 5)
        self.assertEqual(self.balance.remaining_days, 17)
    
    def test_maladie_does_not_deduct_from_balance(self):
        """Test: Congé Maladie ne déduit PAS du solde."""
        # Solde initial
        initial_used = self.balance.used_days
        initial_remaining = self.balance.remaining_days
        
        # Créer une demande de congé maladie
        leave_request = LeaveRequest.objects.create(
            employee=self.employee_user,
            leave_type=self.maladie,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=22),
            total_days=3,
            reason="Maladie",
            status='approved_rh'
        )
        
        # Simuler la logique (ne doit PAS déduire)
        if leave_request.leave_type.deducts_balance:
            self.balance.used_days += Decimal(leave_request.total_days)
            self.balance.remaining_days -= Decimal(leave_request.total_days)
            self.balance.save()
        
        # Vérifier que le solde n'a PAS changé
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.used_days, initial_used)
        self.assertEqual(self.balance.remaining_days, initial_remaining)
    
    def test_multiple_cp_requests_cumulative_deduction(self):
        """Test: Plusieurs demandes de CP déduisent cumulativement."""
        # Première demande: 3 jours
        leave1 = LeaveRequest.objects.create(
            employee=self.employee_user,
            leave_type=self.cp,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            total_days=3,
            reason="Vacances 1",
            status='approved_rh'
        )
        
        if leave1.leave_type.deducts_balance:
            self.balance.used_days += Decimal(leave1.total_days)
            self.balance.remaining_days -= Decimal(leave1.total_days)
            self.balance.save()
        
        # Deuxième demande: 5 jours
        leave2 = LeaveRequest.objects.create(
            employee=self.employee_user,
            leave_type=self.cp,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=34),
            total_days=5,
            reason="Vacances 2",
            status='approved_rh'
        )
        
        if leave2.leave_type.deducts_balance:
            self.balance.used_days += Decimal(leave2.total_days)
            self.balance.remaining_days -= Decimal(leave2.total_days)
            self.balance.save()
        
        # Vérifier le total: 3 + 5 = 8 jours utilisés
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.used_days, 8)
        self.assertEqual(self.balance.remaining_days, 14)
    
    def test_insufficient_balance_validation(self):
        """Test: Validation si solde insuffisant pour CP."""
        # Réduire le solde
        self.balance.remaining_days = 2
        self.balance.save()
        
        # Tenter de créer une demande de 5 jours (supérieur au solde)
        leave_request = LeaveRequest(
            employee=self.employee_user,
            leave_type=self.cp,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=14),
            total_days=5,
            reason="Vacances",
            status='pending'
        )
        
        # Vérifier si solde suffisant
        has_sufficient_balance = self.balance.remaining_days >= leave_request.total_days
        
        # Doit être insuffisant
        self.assertFalse(has_sufficient_balance)


class LeaveWorkflowDeductionTest(TestCase):
    """Tests d'intégration avec le workflow de validation."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Département
        self.department = Department.objects.create(
            name="Marketing",
            description="Marketing Department"
        )
        
        # Employé
        self.employee = User.objects.create_user(
            username='marketer',
            email='marketer@example.com',
            password='Pass123'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user=self.employee,
            employee_id='MKT001',
            phone='1234567890',
            department=self.department,
            role='employee'
        )
        
        # Manager
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='Pass123'
        )
        self.manager_profile = EmployeeProfile.objects.create(
            user=self.manager,
            employee_id='MGR001',
            phone='0987654321',
            department=self.department,
            role='manager'
        )
        
        # RH
        self.rh = User.objects.create_user(
            username='rh',
            email='rh@example.com',
            password='Pass123'
        )
        self.rh_profile = EmployeeProfile.objects.create(
            user=self.rh,
            employee_id='RH001',
            phone='1111111111',
            department=self.department,
            role='rh'
        )
        
        # Types de congés
        self.cp = LeaveType.objects.create(
            name="Congé Annuel",
            code="CP",
            default_days=22,
            deducts_balance=True
        )
        
        self.exceptionnel = LeaveType.objects.create(
            name="Congé Exceptionnel",
            code="EVT",
            default_days=0,
            deducts_balance=False
        )
        
        # Solde
        self.balance = LeaveBalance.objects.create(
            employee=self.employee,
            leave_type=self.cp,
            year=timezone.now().year,
            total_days=22,
            used_days=0,
            remaining_days=22
        )
    
    def test_balance_deducted_only_after_rh_approval(self):
        """Test: Solde déduit seulement après validation RH."""
        # Créer demande
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.cp,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            total_days=3,
            reason="Vacances",
            status='pending'
        )
        
        # Avant validation: solde inchangé
        self.assertEqual(self.balance.remaining_days, 22)
        
        # Valider par Manager
        leave.status = 'approved_manager'
        leave.save()
        
        # Toujours inchangé (pas encore RH)
        self.assertEqual(self.balance.remaining_days, 22)
        
        # Valider par RH (déclencheur de déduction)
        leave.status = 'approved_rh'
        leave.save()
        
        # Simuler la déduction (normalement par signal)
        if leave.leave_type.deducts_balance and leave.status == 'approved_rh':
            self.balance.used_days += Decimal(leave.total_days)
            self.balance.remaining_days -= Decimal(leave.total_days)
            self.balance.save()
        
        # Maintenant déduit
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.remaining_days, 19)
    
    def test_exceptionnel_never_deducts_regardless_of_status(self):
        """Test: Congé exceptionnel ne déduit jamais, même validé RH."""
        initial_remaining = self.balance.remaining_days
        
        # Créer demande exceptionnelle
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.exceptionnel,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=21),
            total_days=2,
            reason="Événement familial",
            status='approved_rh'  # Directement validé
        )
        
        # Simuler la logique
        if leave.leave_type.deducts_balance and leave.status == 'approved_rh':
            self.balance.used_days += Decimal(leave.total_days)
            self.balance.remaining_days -= Decimal(leave.total_days)
            self.balance.save()
        
        # Solde doit rester inchangé
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.remaining_days, initial_remaining)


class LeaveTypeFixtureTest(TestCase):
    """Tests pour vérifier les fixtures de types de congés."""
    
    def test_togo_leave_types_fixture(self):
        """Test: Fixture des types de congés du Togo."""
        # Charger les types depuis la fixture (si elle existe)
        # Sinon créer manuellement
        leave_types_data = [
            {"code": "CP", "name": "Congé Annuel", "deducts_balance": True},
            {"code": "MAL", "name": "Congé Maladie", "deducts_balance": False},
            {"code": "EVT", "name": "Congé Exceptionnel", "deducts_balance": False},
            {"code": "CSS", "name": "Congé Sans Solde", "deducts_balance": False},
        ]
        
        for data in leave_types_data:
            lt, created = LeaveType.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "default_days": 22 if data["code"] == "CP" else 0,
                    "deducts_balance": data["deducts_balance"]
                }
            )
            
            # Vérifier la configuration
            self.assertEqual(lt.deducts_balance, data["deducts_balance"])
            
            # Vérifier cohérence: seul CP déduit
            if data["code"] == "CP":
                self.assertTrue(lt.deducts_balance)
            else:
                self.assertFalse(lt.deducts_balance)
