"""
Script pour créer des données de test pour le système de gestion de présence.

Ce script crée des départements, types de congés, et utilisateurs de test.
"""

import os
import django
from django.utils import timezone
from datetime import date, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Department, EmployeeProfile
from leave.models import LeaveType, Holiday

def create_test_data():
    """Crée les données de test pour le système."""
    
    print("Création des données de test...")
    
    # 1. Créer des départements
    print("\n1. Création des départements...")
    
    dept_it = Department.objects.get_or_create(
        name="Informatique",
        defaults={
            'description': "Département informatique et développement",
            'is_active': True
        }
    )[0]
    
    dept_rh = Department.objects.get_or_create(
        name="Ressources Humaines",
        defaults={
            'description': "Département des ressources humaines",
            'is_active': True
        }
    )[0]
    
    dept_commercial = Department.objects.get_or_create(
        name="Commercial",
        defaults={
            'description': "Département commercial et ventes",
            'is_active': True
        }
    )[0]
    
    print(f"+ Département créé: {dept_it.name}")
    print(f"+ Département créé: {dept_rh.name}")
    print(f"+ Département créé: {dept_commercial.name}")
    
    # 2. Créer des types de congés
    print("\n2. Création des types de congés...")
    
    conges_payes = LeaveType.objects.get_or_create(
        name="Congés payés",
        defaults={
            'code': 'CP',
            'description': 'Congés payés annuels',
            'unit': 'days',
            'allocation_type': 'annual',
            'allocation_amount': 25,
            'max_consecutive_days': 15,
            'requires_justification': False,
            'requires_medical_certificate': False,
            'advance_notice_days': 7,
            'is_paid': True,
            'is_active': True,
            'color': '#28a745'
        }
    )[0]
    
    maladie = LeaveType.objects.get_or_create(
        name="Maladie",
        defaults={
            'code': 'MAL',
            'description': 'Congé maladie',
            'unit': 'days',
            'allocation_type': 'on_demand',
            'allocation_amount': 0,
            'max_consecutive_days': 30,
            'requires_justification': True,
            'requires_medical_certificate': True,
            'advance_notice_days': 0,
            'is_paid': True,
            'is_active': True,
            'color': '#dc3545'
        }
    )[0]
    
    maternite = LeaveType.objects.get_or_create(
        name="Congé maternité",
        defaults={
            'code': 'MAT',
            'description': 'Congé maternité',
            'unit': 'days',
            'allocation_type': 'on_demand',
            'allocation_amount': 0,
            'max_consecutive_days': 98,
            'requires_justification': True,
            'requires_medical_certificate': True,
            'advance_notice_days': 30,
            'is_paid': True,
            'is_active': True,
            'color': '#6f42c1'
        }
    )[0]
    
    print(f"+ Type de congé créé: {conges_payes.name}")
    print(f"+ Type de congé créé: {maladie.name}")
    print(f"+ Type de congé créé: {maternite.name}")
    
    # 3. Créer des jours fériés
    print("\n3. Création des jours fériés...")
    
    # Jours fériés du Togo 2024
    holidays_data = [
        ('Jour de l\'An', date(2024, 1, 1), 'national', True),
        ('Jour de l\'Indépendance', date(2024, 4, 27), 'national', True),
        ('Fête du Travail', date(2024, 5, 1), 'national', True),
        ('Ascension', date(2024, 5, 9), 'religious', False),
        ('Lundi de Pentecôte', date(2024, 5, 20), 'religious', False),
        ('Assomption', date(2024, 8, 15), 'religious', False),
        ('Fête de la République', date(2024, 9, 21), 'national', True),
        ('Toussaint', date(2024, 11, 1), 'religious', False),
        ('Noël', date(2024, 12, 25), 'religious', False),
    ]
    
    for name, holiday_date, holiday_type, is_recurring in holidays_data:
        holiday = Holiday.objects.get_or_create(
            name=name,
            date=holiday_date,
            defaults={
                'holiday_type': holiday_type,
                'description': f'Jour férié: {name}',
                'is_recurring': is_recurring,
                'is_active': True
            }
        )[0]
        print(f"+ Jour férié créé: {holiday.name} ({holiday.date})")
    
    # 4. Créer des utilisateurs de test
    print("\n4. Création des utilisateurs de test...")
    
    # Manager IT
    manager_it = User.objects.get_or_create(
        username='manager.it',
        defaults={
            'first_name': 'Koffi',
            'last_name': 'AGBEGNENOU',
            'email': 'manager.it@example.com',
            'is_staff': True,
            'is_active': True
        }
    )[0]
    manager_it.set_password('password123')
    manager_it.save()
    
    profile_manager = manager_it.employee_profile
    profile_manager.role = 'manager'
    profile_manager.employee_id = 'MGR001'
    profile_manager.department = dept_it
    profile_manager.can_punch = True
    profile_manager.save()
    
    # Assigner comme manager du département IT
    dept_it.manager = manager_it
    dept_it.save()
    
    print(f"+ Manager IT créé: {manager_it.get_full_name()} ({profile_manager.employee_id})")
    
    # RH/DG
    rh_dg = User.objects.get_or_create(
        username='rh.dg',
        defaults={
            'first_name': 'Aminata',
            'last_name': 'TRAORE',
            'email': 'rh.dg@example.com',
            'is_staff': True,
            'is_active': True
        }
    )[0]
    rh_dg.set_password('password123')
    rh_dg.save()
    
    profile_rh = rh_dg.employee_profile
    profile_rh.role = 'rh_dg'
    profile_rh.employee_id = 'RH001'
    profile_rh.department = dept_rh
    profile_rh.can_punch = False  # RH/DG ne pointe pas
    profile_rh.save()
    
    # Assigner comme manager du département RH
    dept_rh.manager = rh_dg
    dept_rh.save()
    
    print(f"+ RH/DG créé: {rh_dg.get_full_name()} ({profile_rh.employee_id})")
    
    # Employés
    employees_data = [
        ('dev1', 'Jean', 'DOSSOU', 'dev1@example.com', 'EMP001', dept_it, manager_it),
        ('dev2', 'Marie', 'KOUMASSI', 'dev2@example.com', 'EMP002', dept_it, manager_it),
        ('com1', 'Pierre', 'ADJOVI', 'com1@example.com', 'EMP003', dept_commercial, None),
        ('com2', 'Fatou', 'SOW', 'com2@example.com', 'EMP004', dept_commercial, None),
    ]
    
    for username, first_name, last_name, email, emp_id, department, manager in employees_data:
        user = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'is_staff': False,
                'is_active': True
            }
        )[0]
        user.set_password('password123')
        user.save()
        
        profile = user.employee_profile
        profile.role = 'employee'
        profile.employee_id = emp_id
        profile.department = department
        profile.manager = manager
        profile.can_punch = True
        profile.save()
        
        print(f"+ Employé créé: {user.get_full_name()} ({profile.employee_id})")
    
    # 5. Créer des paramètres système
    print("\n5. Création des paramètres système...")
    
    from reports.models import SystemSettings
    
    settings_data = [
        ('company_name', 'Entreprise Demo Togo', 'general', 'Nom de l\'entreprise'),
        ('working_hours_start', '08:00', 'attendance', 'Heure de début de travail'),
        ('working_hours_end', '17:00', 'attendance', 'Heure de fin de travail'),
        ('lunch_break_duration', '60', 'attendance', 'Durée de pause déjeuner (minutes)'),
        ('max_late_minutes', '15', 'attendance', 'Minutes de retard tolérées'),
        ('leave_approval_required', 'true', 'leave', 'Appro having required for congés'),
        ('notification_enabled', 'true', 'notification', 'Notifications activées'),
    ]
    
    for key, value, setting_type, description in settings_data:
        SystemSettings.objects.get_or_create(
            key=key,
            defaults={
                'value': value,
                'setting_type': setting_type,
                'description': description,
                'is_active': True
            }
        )
        print(f"+ Paramètre créé: {key} = {value}")
    
    print("\n[SUCCES] Données de test créées avec succès !")
    print("\nUtilisateurs créés:")
    print("  - admin / admin123 (Administrateur)")
    print("  - manager.it / password123 (Manager IT)")
    print("  - rh.dg / password123 (RH/DG)")
    print("  - dev1 / password123 (Développeur 1)")
    print("  - dev2 / password123 (Développeur 2)")
    print("  - com1 / password123 (Commercial 1)")
    print("  - com2 / password123 (Commercial 2)")

if __name__ == "__main__":
    create_test_data()
