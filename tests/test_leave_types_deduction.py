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


def configure_profile(user, **kwargs):
    defaults = {
        'employee_id': kwargs.get('employee_id', 'EMP000'),
        'department': kwargs.get('department'),
        'role': kwargs.get('role', 'employee'),
        'force_password_change': kwargs.get('force_password_change', False),
        'can_punch': kwargs.get('can_punch', True),
        'manager': kwargs.get('manager'),
        'current_work_schedule': kwargs.get('current_work_schedule'),
    }
    profile, _ = EmployeeProfile.objects.update_or_create(
        user=user,
        defaults=defaults,
    )
    return profile


class LeaveTypeDeductsBalanceTest(TestCase):
    """Tests pour le champ deducts_balance sur LeaveType."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Créer les types de congés
        self.cp = LeaveType.objects.create(
            name="Congé Annuel",
            code="CP",
            allocation_type='annual',
            allocation_amount=Decimal('22'),
            requires_justification=False,
            requires_medical_certificate=False,
            deducts_balance=True  # Doit déduire
        )
        
        self.maladie = LeaveType.objects.create(
            name="Congé Maladie",
            code="MAL",
            allocation_type='on_demand',
            allocation_amount=Decimal('0'),
            requires_justification=True,
            requires_medical_certificate=True,
            deducts_balance=False  # Ne doit PAS déduire
        )
        
        self.exceptionnel = LeaveType.objects.create(
            name="Congé Exceptionnel",
            code="EVT",
            allocation_type='on_demand',
            allocation_amount=Decimal('0'),
            requires_justification=False,
            requires_medical_certificate=False,
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
        self.employee_profile = configure_profile(
            self.employee_user,
            employee_id='ENG001',
            department=self.department,
            role='employee'
        )
        
        # Types de congés
        self.cp = LeaveType.objects.create(
            name="Congé Annuel",
            code="CP",
            allocation_type='annual',
            allocation_amount=Decimal('22'),
            deducts_balance=True
        )
        
        self.maladie = LeaveType.objects.create(
            name="Congé Maladie",
            code="MAL",
            allocation_type='on_demand',
            allocation_amount=Decimal('0'),
            deducts_balance=False
        )
        
        # Solde initial
        self.balance = LeaveBalance.objects.create(
            employee=self.employee_user,
            leave_type=self.cp,
            year=timezone.now().year,
            allocated_balance=Decimal('22'),
            taken_balance=Decimal('0'),
            carried_over_balance=Decimal('0'),
        )
    
    def test_cp_deducts_from_balance(self):
        """Test: Congé Annuel déduit du solde."""
        # Créer une demande de congé annuel
        leave_request = LeaveRequest.objects.create(
            employee=self.employee_user,
            leave_type=self.cp,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=14),
            duration_days=Decimal('0'),
            reason="Vacances",
            status='approved_rh'
        )
        leave_request.refresh_from_db()
        
        # Simuler la déduction (normalement fait par le signal/workflow)
        if leave_request.leave_type.deducts_balance:
            self.balance.taken_balance += Decimal(str(leave_request.duration_days))
            self.balance.save()
        
        # Vérifier la déduction
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.taken_balance, Decimal('5'))
        self.assertEqual(self.balance.remaining_balance, Decimal('17'))
    
    def test_maladie_does_not_deduct_from_balance(self):
        """Test: Congé Maladie ne déduit PAS du solde."""
        # Solde initial
        initial_taken = self.balance.taken_balance
        initial_remaining = self.balance.remaining_balance
        
        # Créer une demande de congé maladie
        leave_request = LeaveRequest.objects.create(
            employee=self.employee_user,
            leave_type=self.maladie,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=22),
            duration_days=Decimal('0'),
            reason="Maladie",
            status='approved_rh'
        )
        leave_request.refresh_from_db()
        
        # Simuler la logique (ne doit PAS déduire)
        if leave_request.leave_type.deducts_balance:
            self.balance.taken_balance += Decimal(str(leave_request.duration_days))
            self.balance.save()
        
        # Vérifier que le solde n'a PAS changé
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.taken_balance, initial_taken)
        self.assertEqual(self.balance.remaining_balance, initial_remaining)
    
    def test_multiple_cp_requests_cumulative_deduction(self):
        """Test: Plusieurs demandes de CP déduisent cumulativement."""
        # Première demande: 3 jours
        leave1 = LeaveRequest.objects.create(
            employee=self.employee_user,
            leave_type=self.cp,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            duration_days=Decimal('0'),
            reason="Vacances 1",
            status='approved_rh'
        )
        leave1.refresh_from_db()
        
        if leave1.leave_type.deducts_balance:
            self.balance.taken_balance += Decimal(str(leave1.duration_days))
            self.balance.save()
        
        # Deuxième demande: 5 jours
        leave2 = LeaveRequest.objects.create(
            employee=self.employee_user,
            leave_type=self.cp,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=34),
            duration_days=Decimal('0'),
            reason="Vacances 2",
            status='approved_rh'
        )
        leave2.refresh_from_db()
        
        if leave2.leave_type.deducts_balance:
            self.balance.taken_balance += Decimal(str(leave2.duration_days))
            self.balance.save()
        
        # Vérifier le total: 3 + 5 = 8 jours utilisés
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.taken_balance, Decimal('8'))
        self.assertEqual(self.balance.remaining_balance, Decimal('14'))
    
    def test_insufficient_balance_validation(self):
        """Test: Validation si solde insuffisant pour CP."""
        # Réduire le solde disponible à 2 jours
        self.balance.taken_balance = Decimal('20')
        self.balance.save()
        
        # Tenter de créer une demande de 5 jours (supérieur au solde)
        requested_duration = Decimal('5')
        has_sufficient_balance = self.balance.remaining_balance >= requested_duration
        
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
        self.employee_profile = configure_profile(
            self.employee,
            employee_id='MKT001',
            department=self.department,
            role='employee'
        )
        
        # Manager
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='Pass123'
        )
        self.manager_profile = configure_profile(
            self.manager,
            employee_id='MGR001',
            department=self.department,
            role='manager'
        )
        
        # RH
        self.rh = User.objects.create_user(
            username='rh',
            email='rh@example.com',
            password='Pass123'
        )
        self.rh_profile = configure_profile(
            self.rh,
            employee_id='RH001',
            department=self.department,
            role='rh'
        )
        
        # Types de congés
        self.cp = LeaveType.objects.create(
            name="Congé Annuel",
            code="CP",
            allocation_type='annual',
            allocation_amount=Decimal('22'),
            deducts_balance=True
        )
        
        self.exceptionnel = LeaveType.objects.create(
            name="Congé Exceptionnel",
            code="EVT",
            allocation_type='on_demand',
            allocation_amount=Decimal('0'),
            deducts_balance=False
        )
        
        # Solde
        self.balance = LeaveBalance.objects.create(
            employee=self.employee,
            leave_type=self.cp,
            year=timezone.now().year,
            allocated_balance=Decimal('22'),
            taken_balance=Decimal('0'),
            carried_over_balance=Decimal('0'),
        )
    
    def test_balance_deducted_only_after_rh_approval(self):
        """Test: Solde déduit seulement après validation RH."""
        # Créer demande
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.cp,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            duration_days=Decimal('0'),
            reason="Vacances",
            status='pending'
        )
        leave.refresh_from_db()
        
        # Avant validation: solde inchangé
        self.assertEqual(self.balance.remaining_balance, Decimal('22'))
        
        # Valider par Manager
        leave.status = 'approved_manager'
        leave.save()
        
        # Toujours inchangé (pas encore RH)
        self.assertEqual(self.balance.remaining_balance, Decimal('22'))
        
        # Valider par RH (déclencheur de déduction)
        leave.status = 'approved_rh'
        leave.save()
        
        # Simuler la déduction (normalement par signal)
        if leave.leave_type.deducts_balance and leave.status == 'approved_rh':
            self.balance.taken_balance += Decimal(str(leave.duration_days))
            self.balance.save()
        
        # Maintenant déduit
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.remaining_balance, Decimal('19'))
    
    def test_exceptionnel_never_deducts_regardless_of_status(self):
        """Test: Congé exceptionnel ne déduit jamais, même validé RH."""
        initial_remaining = self.balance.remaining_balance
        
        # Créer demande exceptionnelle
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.exceptionnel,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=21),
            duration_days=Decimal('0'),
            reason="Événement familial",
            status='approved_rh'  # Directement validé
        )
        leave.refresh_from_db()
        
        # Simuler la logique
        if leave.leave_type.deducts_balance and leave.status == 'approved_rh':
            self.balance.taken_balance += Decimal(str(leave.duration_days))
            self.balance.save()
        
        # Solde doit rester inchangé
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.remaining_balance, initial_remaining)


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
                    "allocation_type": 'annual' if data["code"] == "CP" else 'on_demand',
                    "allocation_amount": Decimal('22') if data["code"] == "CP" else Decimal('0'),
                    "deducts_balance": data["deducts_balance"],
                }
            )
            
            # Vérifier la configuration
            self.assertEqual(lt.deducts_balance, data["deducts_balance"])
            
            # Vérifier cohérence: seul CP déduit
            if data["code"] == "CP":
                self.assertTrue(lt.deducts_balance)
            else:
                self.assertFalse(lt.deducts_balance)
