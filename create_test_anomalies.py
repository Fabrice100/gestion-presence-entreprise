"""
Script pour créer des anomalies de test (oublis de sortie).

Simule des employés qui ont pointé l'entrée mais ont oublié de pointer la sortie.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile
from attendance.models import Attendance
from datetime import datetime, date, time, timedelta
from decimal import Decimal

def create_test_anomalies():
    """Crée des pointages sans sortie pour tester l'interface RH."""
    
    print("=" * 70)
    print("CRÉATION D'ANOMALIES DE TEST")
    print("=" * 70)
    
    # Récupérer des employés existants
    employees = EmployeeProfile.objects.filter(can_punch=True)[:3]
    
    if not employees.exists():
        print("\n❌ Aucun employé trouvé avec can_punch=True")
        print("Créez d'abord des employés avec le profil EmployeeProfile")
        return
    
    print(f"\n✓ {employees.count()} employés trouvés")
    
    # Dates pour les tests : hier et avant-hier
    yesterday = date.today() - timedelta(days=1)
    day_before = date.today() - timedelta(days=2)
    
    test_dates = [
        (yesterday, '08:00'),
        (yesterday, '09:15'),
        (day_before, '08:30'),
    ]
    
    created_count = 0
    
    for i, employee in enumerate(employees):
        if i >= len(test_dates):
            break
            
        test_date, in_time = test_dates[i]
        
        # Vérifier si un pointage existe déjà
        existing = Attendance.objects.filter(
            employee=employee,
            date=test_date,
            punch_type='in'
        ).exists()
        
        if existing:
            print(f"\n⏭️  Pointage existe déjà pour {employee.user.get_full_name()} le {test_date}")
            continue
        
        # Créer un pointage d'entrée sans sortie
        attendance = Attendance.objects.create(
            employee=employee,
            date=test_date,
            punch_type='in',
            punch_in_time=datetime.strptime(in_time, '%H:%M').time(),
            latitude=Decimal('48.8566'),
            longitude=Decimal('2.3522'),
            accuracy=Decimal('15.00'),
            status='missing_out'
        )
        
        print(f"\n✓ Oubli de sortie créé:")
        print(f"   Employé: {employee.user.get_full_name()}")
        print(f"   Date: {test_date.strftime('%d/%m/%Y (%A)')}")
        print(f"   Entrée: {in_time}")
        print(f"   Sortie: MANQUANTE")
        
        created_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ {created_count} anomalie(s) créée(s)")
    print("=" * 70)
    
    if created_count > 0:
        print("\n📝 PROCHAINE ÉTAPE:")
        print("   Lancez: python manage.py detect_missing_punches")
        print("   Pour créer les objets AttendanceAnomaly correspondants")
    
    return created_count

if __name__ == '__main__':
    create_test_anomalies()
