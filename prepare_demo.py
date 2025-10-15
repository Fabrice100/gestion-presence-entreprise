#!/usr/bin/env python3
"""
Script pour préparer la démo du système de présence.
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile, Department
from attendance.admin_models import CompanySettings
from attendance.models import Attendance
from datetime import date, time, timedelta
from django.utils import timezone

def prepare_demo():
    print("🎬 PRÉPARATION DE LA DÉMO - SYSTÈME DE PRÉSENCE")
    print("=" * 60)
    
    # 1. Créer un département de démo
    print("\n1️⃣ CRÉATION DU DÉPARTEMENT DÉMO :")
    dept, created = Department.objects.get_or_create(
        name='Département IT',
        defaults={
            'description': 'Département Informatique - Démo',
            'is_active': True
        }
    )
    print(f"✅ Département: {dept.name}")
    
    # 2. Créer des utilisateurs de démo
    print("\n2️⃣ CRÉATION DES UTILISATEURS DÉMO :")
    
    demo_users = [
        {
            'username': 'demo_employee',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'email': 'jean.dupont@demo.com',
            'employee_id': 'EMP001',
            'role': 'employee'
        },
        {
            'username': 'demo_manager',
            'first_name': 'Marie',
            'last_name': 'Martin',
            'email': 'marie.martin@demo.com',
            'employee_id': 'MGR001',
            'role': 'manager'
        },
        {
            'username': 'demo_hr',
            'first_name': 'Pierre',
            'last_name': 'Durand',
            'email': 'pierre.durand@demo.com',
            'employee_id': 'RH001',
            'role': 'rh_dg'
        }
    ]
    
    created_users = []
    for user_data in demo_users:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'email': user_data['email']
            }
        )
        
        if created:
            user.set_password('demo123')
            user.save()
        
        profile, created = EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'employee_id': user_data['employee_id'],
                'department': dept,
                'role': user_data['role'],
                'can_punch': True,
                'is_active': True
            }
        )
        
        created_users.append((user, profile))
        print(f"✅ {user_data['role'].upper()}: {user.username} ({profile.employee_id})")
    
    # 3. Configurer le manager du département
    manager_user, manager_profile = created_users[1]  # demo_manager
    dept.manager = manager_user
    dept.save()
    
    # Assigner les employés au manager
    employee_user, employee_profile = created_users[0]  # demo_employee
    employee_profile.manager = manager_user
    employee_profile.save()
    
    print(f"✅ Manager assigné: {manager_user.username} gère {employee_user.username}")
    
    # 4. Créer des pointages de démo pour les derniers jours
    print("\n3️⃣ CRÉATION DES POINTAGES DÉMO :")
    
    demo_employee = created_users[0][0]  # demo_employee
    
    # Coordonnées du bureau
    office_lat = 6.140766
    office_lng = 1.241907
    
    # Créer des pointages pour les 7 derniers jours
    for days_ago in range(7):
        punch_date = date.today() - timedelta(days=days_ago)
        
        # Ne pas créer de pointages pour le week-end
        if punch_date.weekday() >= 5:  # Samedi = 5, Dimanche = 6
            continue
        
        # Pointage d'entrée
        punch_in = Attendance.objects.create(
            employee=demo_employee,
            date=punch_date,
            punch_type='in',
            time=time(8, 15 + days_ago),  # Légèrement variable
            latitude=office_lat,
            longitude=office_lng,
            accuracy=5.0,
            distance_from_site=0.0,
            status='normal',
            source='web',
            user_agent='Demo Browser'
        )
        
        # Pointage de sortie
        punch_out = Attendance.objects.create(
            employee=demo_employee,
            date=punch_date,
            punch_type='out',
            time=time(17, 30 + days_ago),  # Légèrement variable
            latitude=office_lat,
            longitude=office_lng,
            accuracy=5.0,
            distance_from_site=0.0,
            status='normal',
            source='web',
            user_agent='Demo Browser'
        )
        
        print(f"✅ {punch_date.strftime('%d/%m')}: Entrée {punch_in.time} - Sortie {punch_out.time}")
    
    # 5. Configuration finale
    print("\n4️⃣ CONFIGURATION FINALE :")
    
    settings = CompanySettings.load()
    settings.company_name = "Entreprise Démo"
    settings.site_center_latitude = office_lat
    settings.site_center_longitude = office_lng
    settings.allowed_radius_meters = 200
    settings.gps_accuracy_max_meters = 50
    settings.save()
    
    print(f"✅ Entreprise: {settings.company_name}")
    print(f"✅ Coordonnées: {settings.site_center_latitude}, {settings.site_center_longitude}")
    
    # 6. Résumé pour la démo
    print("\n" + "=" * 60)
    print("🎬 DÉMO PRÊTE !")
    print("=" * 60)
    
    print("\n👥 UTILISATEURS DE DÉMO :")
    print("1. Employé: demo_employee / demo123")
    print("2. Manager: demo_manager / demo123") 
    print("3. RH/DG: demo_hr / demo123")
    
    print("\n🌐 URLs POUR LA DÉMO :")
    print("• Connexion: http://127.0.0.1:8000/accounts/login/")
    print("• Pointage normal: http://127.0.0.1:8000/attendance/punch/")
    print("• Pointage démo: http://127.0.0.1:8000/attendance/punch/demo/")
    print("• Mes présences: http://127.0.0.1:8000/attendance/my-attendance/")
    print("• Administration: http://127.0.0.1:8000/admin/")
    
    print("\n💡 CONSEILS POUR LA PRÉSENTATION :")
    print("• Utilisez le mode démo (/punch/demo/) pour éviter les problèmes GPS")
    print("• Connectez-vous avec demo_employee pour montrer le pointage")
    print("• Connectez-vous avec demo_manager pour montrer la validation")
    print("• Connectez-vous avec demo_hr pour montrer les rapports")
    
    print("\n🚀 DÉMARRAGE DU SERVEUR :")
    print("python manage.py runserver")

if __name__ == "__main__":
    prepare_demo()
