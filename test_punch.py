#!/usr/bin/env python3
"""
Script de test pour diagnostiquer les problèmes de pointage.
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

def test_punch_system():
    print("🔍 DIAGNOSTIC DU SYSTÈME DE POINTAGE")
    print("=" * 50)
    
    # 1. Vérifier les utilisateurs avec profils
    print("\n1️⃣ VÉRIFICATION DES UTILISATEURS :")
    users_with_profiles = []
    for user in User.objects.all():
        try:
            profile = user.employee_profile
            if profile.can_punch:
                users_with_profiles.append((user, profile))
                print(f"✅ {user.username} - {profile.employee_id} - Peut pointer: {profile.can_punch}")
            else:
                print(f"❌ {user.username} - {profile.employee_id} - NE PEUT PAS pointer")
        except:
            print(f"⚠️ {user.username} - Pas de profil employé")
    
    if not users_with_profiles:
        print("❌ AUCUN UTILISATEUR NE PEUT POINTER !")
        return
    
    # 2. Vérifier la configuration
    print("\n2️⃣ VÉRIFICATION DE LA CONFIGURATION :")
    try:
        settings = CompanySettings.load()
        print(f"✅ Configuration chargée: {settings.company_name}")
        print(f"📍 Coordonnées: {settings.site_center_latitude}, {settings.site_center_longitude}")
        print(f"📏 Rayon autorisé: {settings.allowed_radius_meters}m")
        print(f"🎯 Précision GPS max: {settings.gps_accuracy_max_meters}m")
        print(f"🕐 Heures: {settings.work_start_time} - {settings.work_end_time}")
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return
    
    # 3. Test de pointage simulé
    print("\n3️⃣ TEST DE POINTAGE SIMULÉ :")
    test_user, test_profile = users_with_profiles[0]
    
    from datetime import date, time
    from django.utils import timezone
    
    # Coordonnées de test (près du bureau)
    test_lat = 6.140766
    test_lng = 1.241907
    test_accuracy = 10.0
    
    print(f"👤 Utilisateur test: {test_user.username}")
    print(f"📍 Coordonnées test: {test_lat}, {test_lng}")
    print(f"🎯 Précision test: {test_accuracy}m")
    
    # Vérifier la distance
    from math import radians, sin, cos, sqrt, atan2
    
    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371000  # Rayon de la Terre en mètres
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    distance = calculate_distance(
        test_lat, test_lng,
        settings.site_center_latitude, settings.site_center_longitude
    )
    
    print(f"📏 Distance du bureau: {distance:.2f}m")
    
    if distance <= settings.allowed_radius_meters:
        print("✅ Distance OK")
    else:
        print(f"❌ Trop loin (max: {settings.allowed_radius_meters}m)")
    
    if test_accuracy <= settings.gps_accuracy_max_meters:
        print("✅ Précision GPS OK")
    else:
        print(f"❌ Précision trop faible (max: {settings.gps_accuracy_max_meters}m)")
    
    # 4. Créer un pointage de test
    print("\n4️⃣ CRÉATION D'UN POINTAGE DE TEST :")
    try:
        attendance = Attendance.objects.create(
            employee=test_user,
            date=date.today(),
            punch_type='in',
            time=timezone.now().time(),
            latitude=test_lat,
            longitude=test_lng,
            accuracy=test_accuracy,
            source='admin'
        )
        print(f"✅ Pointage créé: {attendance}")
        print(f"📊 Distance calculée: {attendance.distance_from_site:.2f}m")
        print(f"🔍 Statut: {attendance.status}")
        
    except Exception as e:
        print(f"❌ Erreur création pointage: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 DIAGNOSTIC TERMINÉ")

if __name__ == "__main__":
    test_punch_system()
