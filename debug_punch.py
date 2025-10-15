"""
Script de debug pour surveiller les pointages en temps réel
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.models import Attendance
from django.contrib.auth.models import User
import logging

# Configuration du logging pour capturer les erreurs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("=== SIMULATEUR DE POINTAGE POUR DEBUG ===")
print()

def test_punch_simulation():
    """Simule un pointage complet pour identifier les problèmes"""
    
    try:
        # Utiliser l'utilisateur admin
        user = User.objects.get(username='admin')
        print(f"Utilisateur: {user.username}")
        
        # Vérifier le profil employé
        try:
            profile = user.employee_profile
            print(f"Profil: {profile.role}")
            print(f"Peut pointer: {profile.can_punch}")
            
            if not profile.can_punch:
                print("❌ PROBLÈME: L'utilisateur ne peut pas pointer!")
                return False
                
        except Exception as e:
            print(f"❌ PROBLÈME PROFIL: {e}")
            return False
        
        # Vérifier les pointages existants aujourd'hui
        from datetime import date
        today = date.today()
        
        existing_in = Attendance.objects.filter(
            employee=user,
            date=today,
            punch_type='in'
        ).exists()
        
        existing_out = Attendance.objects.filter(
            employee=user,
            date=today,
            punch_type='out'
        ).exists()
        
        print(f"Pointages existants aujourd'hui:")
        print(f"  Entrée: {'Oui' if existing_in else 'Non'}")
        print(f"  Sortie: {'Oui' if existing_out else 'Non'}")
        
        # Déterminer le type de pointage à tester
        if not existing_in:
            punch_type = 'in'
            print(f"→ Test pointage ENTRÉE")
        elif not existing_out:
            punch_type = 'out'
            print(f"→ Test pointage SORTIE")
        else:
            print("❌ Tous les pointages déjà effectués aujourd'hui")
            return False
        
        # Simuler la création
        print("\n=== SIMULATION CRÉATION ===")
        
        from django.utils import timezone
        from attendance.admin_models import CompanySettings
        
        settings = CompanySettings.load()
        current_time = timezone.now().time()
        
        # Coordonnées bureau
        latitude = settings.site_center_latitude
        longitude = settings.site_center_longitude
        accuracy = 15.0
        
        print(f"GPS: {latitude}, {longitude}")
        print(f"Précision: {accuracy}m")
        
        # Tenter la création
        attendance = Attendance.objects.create(
            employee=user,
            date=today,
            time=current_time,
            punch_type=punch_type,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            status='normal',
            source='debug-test'
        )
        
        print(f"✅ SUCCÈS: Enregistrement créé!")
        print(f"   ID: {attendance.id}")
        print(f"   Distance: {attendance.distance_from_site}m")
        print(f"   Status: {attendance.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR CRÉATION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_punch_simulation()