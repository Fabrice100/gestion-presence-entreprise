"""
Fabriques de données de test respectant les principes SOLID.

Factory Pattern pour créer des objets de test cohérents
et maintenables suivant le principe de responsabilité unique.
"""

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile, Department
from attendance.models import Attendance
from attendance.admin_models import CompanySettings
from leave.models import LeaveType, LeaveRequest
from datetime import date, time, timedelta
from django.utils import timezone
import factory
import factory.fuzzy


class DepartmentFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des départements de test."""
    
    class Meta:
        model = Department
    
    name = factory.Sequence(lambda n: f"Département {n}")
    description = factory.LazyAttribute(lambda obj: f"Description du {obj.name}")
    is_active = True


class UserFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des utilisateurs de test."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")
    is_active = True


class EmployeeProfileFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des profils employés de test."""
    
    class Meta:
        model = EmployeeProfile
    
    user = factory.SubFactory(UserFactory)
    employee_id = factory.Sequence(lambda n: f"EMP{n:03d}")
    department = factory.SubFactory(DepartmentFactory)
    can_punch = True
    phone = factory.Faker('phone_number')
    position = factory.Faker('job')
    hire_date = factory.LazyFunction(lambda: date.today() - timedelta(days=30))


class ManagerProfileFactory(EmployeeProfileFactory):
    """Factory spécialisée pour créer des managers."""
    
    can_approve_leave = True
    can_view_reports = True


class CompanySettingsFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des paramètres d'entreprise de test."""
    
    class Meta:
        model = CompanySettings
    
    company_name = "Entreprise Test"
    site_center_latitude = 6.140766
    site_center_longitude = 1.241907
    allowed_radius_meters = 200
    gps_accuracy_max_meters = 50
    work_start_time = time(8, 0)
    work_end_time = time(17, 0)


class AttendanceFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des pointages de test."""
    
    class Meta:
        model = Attendance
    
    employee = factory.SubFactory(UserFactory)
    date = factory.LazyFunction(date.today)
    punch_type = 'in'
    time = factory.LazyFunction(lambda: timezone.now().time())
    latitude = 6.140766  # Coordonnées bureau par défaut
    longitude = 1.241907
    accuracy = 10.0
    distance_from_site = 0.0
    status = 'normal'
    source = 'test'


class LeaveTypeFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des types de congés."""
    
    class Meta:
        model = LeaveType
    
    name = factory.Sequence(lambda n: f"Congé Type {n}")
    description = factory.LazyAttribute(lambda obj: f"Description de {obj.name}")
    days_allocated_per_year = 25
    requires_approval = True
    is_active = True


class LeaveRequestFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des demandes de congés."""
    
    class Meta:
        model = LeaveRequest
    
    employee = factory.SubFactory(UserFactory)
    leave_type = factory.SubFactory(LeaveTypeFactory)
    start_date = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(days=2))
    reason = factory.Faker('text', max_nb_chars=100)
    status = 'pending'


# Utilitaires pour tests rapides
class TestDataHelper:
    """
    Helper class respectant le principe de responsabilité unique.
    Se concentre uniquement sur la création de données de test communes.
    """
    
    @staticmethod
    def create_employee_with_profile(**kwargs) -> tuple[User, EmployeeProfile]:
        """
        Crée un employé avec son profil en une fois.
        
        Returns:
            tuple: (User, EmployeeProfile)
        """
        user = UserFactory(**kwargs.get('user_kwargs', {}))
        profile_kwargs = kwargs.get('profile_kwargs', {})
        profile_kwargs['user'] = user
        profile = EmployeeProfileFactory(**profile_kwargs)
        return user, profile
    
    @staticmethod
    def create_manager_with_department() -> tuple[User, EmployeeProfile, Department]:
        """
        Crée un manager avec son département.
        
        Returns:
            tuple: (User, EmployeeProfile, Department)
        """
        department = DepartmentFactory()
        user = UserFactory()
        profile = ManagerProfileFactory(user=user, department=department)
        return user, profile, department
    
    @staticmethod
    def create_test_attendance(employee: User = None, **kwargs) -> Attendance:
        """
        Crée un pointage de test avec validation GPS.
        
        Args:
            employee: Utilisateur (créé automatiquement si None)
            **kwargs: Paramètres supplémentaires pour le pointage
            
        Returns:
            Attendance: Instance de pointage créée
        """
        if employee is None:
            employee, _ = TestDataHelper.create_employee_with_profile()
        
        # Assurer une configuration d'entreprise
        if not CompanySettings.objects.exists():
            CompanySettingsFactory()
        
        return AttendanceFactory(employee=employee, **kwargs)
    
    @staticmethod
    def setup_basic_leave_system() -> dict:
        """
        Configure un système de congés de base pour les tests.
        
        Returns:
            dict: {'leave_types': List[LeaveType], 'employees': List[User]}
        """
        # Créer types de congés standards
        annual_leave = LeaveTypeFactory(
            name="Congés Annuels",
            days_allocated_per_year=25
        )
        sick_leave = LeaveTypeFactory(
            name="Congés Maladie", 
            days_allocated_per_year=10
        )
        
        # Créer quelques employés
        employees = []
        for i in range(3):
            user, profile = TestDataHelper.create_employee_with_profile()
            employees.append(user)
        
        return {
            'leave_types': [annual_leave, sick_leave],
            'employees': employees
        }