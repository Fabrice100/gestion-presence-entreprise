#!/usr/bin/env python3
"""
Script d'initialisation de la base de données SQLite avec les 4 rôles.

Ce script crée :
1. Base de données SQLite
2. Les 4 comptes utilisateurs (Admin, RH, Manager, Employé)
3. La configuration CompanySettings
4. Un département de test

Usage:
    python init_database.py
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile, Department
from attendance.admin_models import CompanySettings
from django.db import connection

def init_database():
    print("=" * 70)
    print("🗄️  INITIALISATION BASE DE DONNÉES SQLite")
    print("=" * 70)
    
    # Vérifier que nous sommes bien en SQLite
    db_engine = connection.settings_dict['ENGINE']
    if 'sqlite3' not in db_engine:
        print(f"⚠️  ATTENTION: Base de données actuelle = {db_engine}")
        print("    Ce script est conçu pour SQLite.")
        response = input("Continuer quand même ? (oui/non): ")
        if response.lower() not in ['oui', 'o', 'yes', 'y']:
            print("❌ Annulé.")
            return
    
    print(f"\n✅ Base de données: SQLite")
    print(f"   Fichier: {connection.settings_dict.get('NAME', 'db.sqlite3')}")
    
    # 1. Créer le département
    print("\n" + "─" * 70)
    print("1️⃣  CRÉATION DU DÉPARTEMENT")
    print("─" * 70)
    
    dept, created = Department.objects.get_or_create(
        name='Direction Générale',
        defaults={
            'description': 'Département principal de l\'entreprise',
            'is_active': True
        }
    )
    status = "✅ Créé" if created else "ℹ️  Existant"
    print(f"{status} Département: {dept.name}")
    
    # 2. Créer les 4 comptes utilisateurs
    print("\n" + "─" * 70)
    print("2️⃣  CRÉATION DES 4 COMPTES UTILISATEURS")
    print("─" * 70)
    
    # Import du service pour générer les IDs
    from accounts.user_services import UserService
    
    users_data = [
        {
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'Système',
            'email': 'admin@example.com',
            'password': 'admin123',
            'employee_id': None,  # Admin n'a PAS d'employee_id
            'role': 'admin',
            'is_superuser': True,  # Admin Django = superuser
            'can_punch': False,    # Admin technique ne pointe pas
            'description': 'Administrateur technique (configuration système)'
        },
        {
            'username': 'rh.dg',
            'first_name': 'RH',
            'last_name': 'Direction',
            'email': 'rh@example.com',
            'password': 'password123',
            'employee_id': 'auto',  # Génération automatique EMPXXX
            'role': 'rh_dg',
            'is_superuser': False,
            'can_punch': False,    # RH ne peut PAS pointer
            'description': 'Ressources Humaines / Direction Générale'
        },
        {
            'username': 'manager.it',
            'first_name': 'Manager',
            'last_name': 'IT',
            'email': 'manager@example.com',
            'password': 'password123',
            'employee_id': 'auto',  # Génération automatique EMPXXX
            'role': 'manager',
            'is_superuser': False,
            'can_punch': True,     # Manager peut pointer
            'description': 'Manager IT'
        },
        {
            'username': 'employe.test',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'email': 'jean.dupont@example.com',
            'password': 'password123',
            'employee_id': 'auto',  # Génération automatique EMPXXX
            'role': 'employee',
            'is_superuser': False,
            'can_punch': True,     # Employé peut pointer
            'description': 'Employé standard'
        }
    ]
    
    created_users = []
    
    for user_data in users_data:
        # Créer ou récupérer l'utilisateur
        user, user_created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'email': user_data['email'],
                'is_superuser': user_data['is_superuser'],
                'is_staff': True  # Tous les comptes peuvent accéder au backend
            }
        )
        
        if user_created:
            user.set_password(user_data['password'])
            user.save()
        
        # L'admin (superuser) n'a PAS de EmployeeProfile
        # Seulement RH, Manager, Employé ont un employee_id
        if user.is_superuser:
            # Admin : seulement username + password
            status = "✅ Créé" if user_created else "ℹ️  Existant"
            print(f"\n{status} ADMIN (SUPERUSER)")
            print(f"   Username: {user.username}")
            print(f"   Mot de passe: {user_data['password']}")
            print(f"   ID Employé: AUCUN (admin technique)")
            print(f"   Description: {user_data['description']}")
            created_users.append((user, None))
        else:
            # RH, Manager, Employé : username + password + employee_id
            
            # Générer l'employee_id si nécessaire
            if user_data['employee_id'] == 'auto':
                # Vérifier si l'utilisateur existe déjà avec un profil
                existing_profile = EmployeeProfile.objects.filter(user=user).first()
                if existing_profile:
                    employee_id = existing_profile.employee_id
                else:
                    employee_id = UserService.generate_employee_id()
            else:
                employee_id = user_data['employee_id']
            
            profile, profile_created = EmployeeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': employee_id,
                    'department': dept,
                    'role': user_data['role'],
                    'can_punch': user_data['can_punch'],
                    'is_active': True
                }
            )
            
            status = "✅ Créé" if (user_created or profile_created) else "ℹ️  Existant"
            punch_badge = "📍 Pointage" if profile.can_punch else "⚙️  Config seule"
            
            print(f"\n{status} {user_data['role'].upper()}")
            print(f"   Username: {user.username}")
            print(f"   ID Employé: {profile.employee_id}")
            print(f"   Mot de passe: {user_data['password']}")
            print(f"   Rôle: {profile.get_role_display()}")
            print(f"   Badges: {punch_badge}")
            print(f"   Description: {user_data['description']}")
            
            created_users.append((user, profile))
    
    # 3. Configurer le manager du département
    print("\n" + "─" * 70)
    print("3️⃣  CONFIGURATION DU DÉPARTEMENT")
    print("─" * 70)
    
    manager_user = created_users[2][0]  # manager.it
    employee_user = created_users[3][0]  # employe.test
    employee_profile = created_users[3][1]
    
    dept.manager = manager_user
    dept.save()
    
    employee_profile.manager = manager_user
    employee_profile.save()
    
    print(f"✅ Manager du département: {manager_user.username}")
    print(f"✅ Employé assigné au manager: {employee_user.username}")
    
    # 4. Configuration CompanySettings
    print("\n" + "─" * 70)
    print("4️⃣  CONFIGURATION SYSTÈME (GPS & HORAIRES)")
    print("─" * 70)
    
    settings = CompanySettings.load()
    settings.company_name = "Entreprise Demo"
    settings.site_center_latitude = 6.1304
    settings.site_center_longitude = 1.2158
    settings.allowed_radius_meters = 200
    settings.gps_accuracy_max_meters = 50
    settings.gps_required = True
    settings.save()
    
    print(f"✅ Nom entreprise: {settings.company_name}")
    print(f"✅ Coordonnées GPS: {settings.site_center_latitude}, {settings.site_center_longitude}")
    print(f"✅ Rayon autorisé: {settings.allowed_radius_meters}m")
    print(f"✅ Horaires: {settings.work_start_time} - {settings.work_end_time}")
    
    # 5. Résumé final
    print("\n" + "=" * 70)
    print("🎉 BASE DE DONNÉES INITIALISÉE AVEC SUCCÈS !")
    print("=" * 70)
    
    print("\n📊 RÉSUMÉ DES RÔLES:")
    print("\n1. 🔴 ADMIN (Administrateur technique)")
    print("   - Rôle: Configuration système uniquement")
    print("   - Superuser Django: OUI")
    print("   - Peut pointer: NON")
    print("   - Accès: /admin/ (Django Admin), configuration GPS/horaires")
    
    print("\n2. 🟠 RH/DG (Ressources Humaines)")
    print("   - Rôle: Gestion employés, validation finale congés")
    print("   - Superuser Django: NON")
    print("   - Peut pointer: OUI")
    print("   - Accès: Configuration horaires (pas GPS), rapports, gestion employés")
    
    print("\n3. 🟡 MANAGER (Chef d'équipe)")
    print("   - Rôle: Validation congés niveau 1, suivi équipe")
    print("   - Superuser Django: NON")
    print("   - Peut pointer: OUI")
    print("   - Accès: Dashboard manager, validation congés équipe")
    
    print("\n4. 🟢 EMPLOYÉ (Utilisateur standard)")
    print("   - Rôle: Pointage, demande congés")
    print("   - Superuser Django: NON")
    print("   - Peut pointer: OUI")
    print("   - Accès: Dashboard employé, pointage, demandes congés")
    
    print("\n🔐 COMPTES DE CONNEXION:")
    print("┌─────────────────┬──────────────┬──────────────┐")
    print("│ Rôle            │ Username     │ Mot de passe │")
    print("├─────────────────┼──────────────┼──────────────┤")
    print("│ Admin           │ admin        │ admin123     │")
    print("│ RH/DG           │ rh.dg        │ password123  │")
    print("│ Manager         │ manager.it   │ password123  │")
    print("│ Employé         │ employe.test │ password123  │")
    print("└─────────────────┴──────────────┴──────────────┘")
    
    print("\n🌐 URLs UTILES:")
    print("• Page d'accueil: http://127.0.0.1:8000/")
    print("• Connexion: http://127.0.0.1:8000/accounts/login/")
    print("• Django Admin: http://127.0.0.1:8000/admin/")
    print("• Pointage: http://127.0.0.1:8000/attendance/punch/")
    
    print("\n💡 PROCHAINES ÉTAPES:")
    print("1. python manage.py init_togo_setup    # Charger types congés + jours fériés")
    print("2. python manage.py runserver          # Démarrer le serveur")
    print("3. Connectez-vous avec l'un des comptes ci-dessus")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
