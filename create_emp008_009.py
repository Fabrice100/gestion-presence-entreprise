#!/usr/bin/env python3
"""
Script pour créer EMP008 et EMP009 avec mot de passe connu
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile, Department

def create_emp008_009():
    print("=" * 70)
    print("🆕 CRÉATION DES COMPTES EMP008 et EMP009")
    print("=" * 70)
    
    # Récupérer le département
    dept = Department.objects.first()
    if not dept:
        print("❌ Aucun département trouvé. Exécutez d'abord init_database.py")
        return
    
    # Récupérer un manager
    manager_profile = EmployeeProfile.objects.filter(role='manager').first()
    manager = manager_profile.user if manager_profile else None
    
    employees = [
        {
            'username': 'emp8',
            'first_name': 'Employé',
            'last_name': 'Huit',
            'email': 'emp8@example.com',
            'password': 'password123',  # Mot de passe CONNU
            'employee_id': 'EMP008',
            'role': 'employee'
        },
        {
            'username': 'emp9',
            'first_name': 'Employé',
            'last_name': 'Neuf',
            'email': 'emp9@example.com',
            'password': 'password123',  # Mot de passe CONNU
            'employee_id': 'EMP009',
            'role': 'employee'
        }
    ]
    
    for emp_data in employees:
        # Vérifier si l'employee_id existe déjà
        if EmployeeProfile.objects.filter(employee_id=emp_data['employee_id']).exists():
            print(f"⚠️  {emp_data['employee_id']} existe déjà, ignoré")
            continue
        
        # Créer l'utilisateur
        user, created = User.objects.get_or_create(
            username=emp_data['username'],
            defaults={
                'first_name': emp_data['first_name'],
                'last_name': emp_data['last_name'],
                'email': emp_data['email']
            }
        )
        
        if created:
            user.set_password(emp_data['password'])
            user.save()
            print(f"✅ User créé: {user.username}")
        else:
            print(f"ℹ️  User existant: {user.username}")
        
        # Créer ou mettre à jour le profil
        profile, created = EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'employee_id': emp_data['employee_id'],
                'department': dept,
                'role': emp_data['role'],
                'manager': manager,
                'can_punch': True,
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Profil créé: {profile.employee_id}")
        else:
            # Mettre à jour l'employee_id si différent
            if profile.employee_id != emp_data['employee_id']:
                profile.employee_id = emp_data['employee_id']
                profile.save()
                print(f"✅ Profil mis à jour: {profile.employee_id}")
            else:
                print(f"ℹ️  Profil existant: {profile.employee_id}")
        
        print(f"\n📋 COMPTE CRÉÉ:")
        print(f"   Employee ID: {profile.employee_id}")
        print(f"   Username: {user.username}")
        print(f"   Mot de passe: {emp_data['password']}")
        print(f"   Email: {user.email}")
        print(f"   Rôle: {profile.role}")
        print(f"   Manager: {manager.username if manager else 'Aucun'}")
        print("-" * 70)
    
    print("\n✅ TERMINÉ !")
    print("\nVous pouvez maintenant vous connecter avec:")
    print("  Username: emp8    | Password: password123")
    print("  Username: emp9    | Password: password123")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        create_emp008_009()
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
