#!/usr/bin/env python3
"""
Test pour vérifier que le pointage fonctionne pour tous les utilisateurs créés.
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile
from attendance.models import Attendance
from attendance.admin_models import CompanySettings
from datetime import date, time
from django.utils import timezone

def test_all_users():
    print("🔍 TEST DE TOUS LES UTILISATEURS - SYSTÈME DE POINTAGE")
    print("=" * 60)
    
    # 1. Lister tous les utilisateurs
    print("\n1️⃣ UTILISATEURS EXISTANTS :")
    all_users = User.objects.all()
    users_with_profiles = []
    users_without_profiles = []
    
    for user in all_users:
        try:
            profile = user.employee_profile
            users_with_profiles.append((user, profile))
            
            status = "✅ Peut pointer" if profile.can_punch else "❌ Ne peut pas pointer"
            print(f"• {user.username} - {profile.employee_id} - {status}")
            
        except:
            users_without_profiles.append(user)
            print(f"• {user.username} - ⚠️ Pas de profil employé")
    
    print(f"\n📊 RÉSUMÉ :")
    print(f"   Utilisateurs avec profil: {len(users_with_profiles)}")
    print(f"   Utilisateurs sans profil: {len(users_without_profiles)}")
    
    # 2. Créer des profils manquants
    if users_without_profiles:
        print(f"\n2️⃣ CRÉATION DES PROFILS MANQUANTS :")
        
        # Créer un département par défaut
        from accounts.models import Department
        default_dept, created = Department.objects.get_or_create(
            name='Département Général',
            defaults={'description': 'Département par défaut'}
        )
        
        for user in users_without_profiles:
            # Générer un ID employé
            import random
            prefix = 'EMP'
            existing_ids = set(
                EmployeeProfile.objects.filter(
                    employee_id__startswith=prefix
                ).values_list('employee_id', flat=True)
            )
            
            # Trouver un ID libre
            new_id = None
            for i in range(100, 999):
                candidate_id = f'{prefix}{i}'
                if candidate_id not in existing_ids:
                    new_id = candidate_id
                    break
            
            if not new_id:
                new_id = f'{prefix}{random.randint(1000, 9999)}'
            
            # Créer le profil
            profile = EmployeeProfile.objects.create(
                user=user,
                employee_id=new_id,
                department=default_dept,
                role='employee',
                can_punch=True,
                is_active=True
            )
            
            users_with_profiles.append((user, profile))
            print(f"✅ Profil créé pour {user.username}: {new_id}")
    
    # 3. Tester le pointage pour chaque utilisateur
    print(f"\n3️⃣ TEST DE POINTAGE POUR CHAQUE UTILISATEUR :")
    
    # Coordonnées de test
    test_lat = 6.140766
    test_lng = 1.241907
    test_accuracy = 10.0
    
    successful_punches = 0
    failed_punches = 0
    
    for user, profile in users_with_profiles:
        if not profile.can_punch:
            print(f"⏭️ {user.username}: Ne peut pas pointer (can_punch=False)")
            continue
        
        try:
            # Créer un pointage de test
            attendance = Attendance.objects.create(
                employee=user,
                date=date.today(),
                punch_type='in',
                time=timezone.now().time(),
                latitude=test_lat,
                longitude=test_lng,
                accuracy=test_accuracy,
                distance_from_site=0.0,
                status='normal',
                source='test',
                user_agent='Test Script'
            )
            
            print(f"✅ {user.username} ({profile.employee_id}): Pointage créé")
            successful_punches += 1
            
            # Supprimer le pointage de test
            attendance.delete()
            
        except Exception as e:
            print(f"❌ {user.username} ({profile.employee_id}): Erreur - {e}")
            failed_punches += 1
    
    # 4. Vérifier la configuration
    print(f"\n4️⃣ VÉRIFICATION DE LA CONFIGURATION :")
    
    try:
        settings = CompanySettings.load()
        print(f"✅ Configuration chargée: {settings.company_name}")
        print(f"✅ Coordonnées: {settings.site_center_latitude}, {settings.site_center_longitude}")
        print(f"✅ Rayon autorisé: {settings.allowed_radius_meters}m")
        print(f"✅ Précision GPS max: {settings.gps_accuracy_max_meters}m")
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return
    
    # 5. Résumé final
    print(f"\n" + "=" * 60)
    print(f"📊 RÉSUMÉ FINAL :")
    print(f"   Utilisateurs testés: {len(users_with_profiles)}")
    print(f"   Pointages réussis: {successful_punches}")
    print(f"   Pointages échoués: {failed_punches}")
    
    if successful_punches == len([u for u in users_with_profiles if u[1].can_punch]):
        print(f"\n🎉 SUCCÈS : Tous les utilisateurs peuvent pointer !")
    else:
        print(f"\n⚠️ ATTENTION : Certains utilisateurs ont des problèmes")
    
    # 6. Instructions pour la présentation
    print(f"\n🎬 POUR LA PRÉSENTATION :")
    print(f"   URL de connexion: http://127.0.0.1:8000/accounts/login/")
    print(f"   URL de pointage: http://127.0.0.1:8000/attendance/punch/")
    print(f"   Utilisateurs prêts: {successful_punches}")
    
    if successful_punches > 0:
        print(f"\n👥 UTILISATEURS DISPONIBLES POUR LA DÉMO :")
        for user, profile in users_with_profiles:
            if profile.can_punch:
                print(f"   • {user.username} / mot_de_passe (ID: {profile.employee_id})")

if __name__ == "__main__":
    test_all_users()
