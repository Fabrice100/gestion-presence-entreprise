#!/usr/bin/env python3
"""
Test simple du pointage sans GPS pour diagnostiquer les problèmes.
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

def test_simple():
    print("🔍 TEST SIMPLE DU POINTAGE")
    print("=" * 40)
    
    # 1. Trouver un utilisateur qui peut pointer
    try:
        user = User.objects.get(username='test_user')
        profile = user.employee_profile
        print(f"✅ Utilisateur trouvé: {user.username}")
        print(f"✅ Peut pointer: {profile.can_punch}")
        print(f"✅ ID Employé: {profile.employee_id}")
    except:
        print("❌ Utilisateur test_user non trouvé")
        return
    
    # 2. Vérifier la configuration
    try:
        settings = CompanySettings.load()
        print(f"✅ Configuration: {settings.company_name}")
        print(f"✅ Coordonnées: {settings.site_center_latitude}, {settings.site_center_longitude}")
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return
    
    # 3. Créer un pointage de test
    try:
        attendance = Attendance.objects.create(
            employee=user,
            date=date.today(),
            punch_type='in',
            time=timezone.now().time(),
            latitude=6.140766,  # Coordonnées exactes du bureau
            longitude=1.241907,
            accuracy=5.0,  # Précision excellente
            source='admin',
            user_agent='Test Script',
            ip_address='127.0.0.1'
        )
        
        print(f"✅ Pointage créé avec succès!")
        print(f"   ID: {attendance.id}")
        print(f"   Employé: {attendance.employee.username}")
        print(f"   Type: {attendance.get_punch_type_display()}")
        print(f"   Date: {attendance.date}")
        print(f"   Heure: {attendance.time}")
        print(f"   Distance: {attendance.distance_from_site:.2f}m")
        print(f"   Statut: {attendance.status}")
        
        # Vérifier les règles
        if attendance.distance_from_site <= settings.allowed_radius_meters:
            print("✅ Distance OK")
        else:
            print(f"❌ Trop loin: {attendance.distance_from_site:.2f}m > {settings.allowed_radius_meters}m")
            
        if attendance.accuracy <= settings.gps_accuracy_max_meters:
            print("✅ Précision OK")
        else:
            print(f"❌ Précision faible: {attendance.accuracy}m > {settings.gps_accuracy_max_meters}m")
        
    except Exception as e:
        print(f"❌ Erreur création pointage: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 40)
    print("🏁 TEST TERMINÉ")

if __name__ == "__main__":
    test_simple()
