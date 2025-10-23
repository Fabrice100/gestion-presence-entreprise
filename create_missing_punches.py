"""
Script simple pour créer des pointages avec oubli de sortie.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile
from attendance.models import Attendance, AttendanceAnomaly
from datetime import datetime, date, time, timedelta
from decimal import Decimal

print("=" * 70)
print("CRÉATION DE POINTAGES AVEC OUBLI DE SORTIE")
print("=" * 70)

# Récupérer des employés existants
employees = EmployeeProfile.objects.filter(can_punch=True)[:3]

if not employees:
    print("\n❌ Aucun employé trouvé avec can_punch=True")
    print("Veuillez créer des employés d'abord.")
    exit(1)

print(f"\n✓ {employees.count()} employés trouvés")

# Créer des pointages d'entrée sans sortie (hier et avant-hier)
dates_to_test = [
    date.today() - timedelta(days=1),  # Hier
    date.today() - timedelta(days=2),  # Avant-hier
]

times_in = ['08:00', '08:30', '09:00']
created_count = 0

for test_date in dates_to_test:
    print(f"\n📅 Date: {test_date.strftime('%d/%m/%Y')}")
    
    for i, employee_profile in enumerate(employees):
        # Récupérer l'utilisateur (car Attendance.employee est un ForeignKey vers User)
        user = employee_profile.user
        
        # Vérifier si un pointage existe déjà
        existing = Attendance.objects.filter(
            employee=user,
            date=test_date
        ).first()
        
        if existing:
            print(f"   → {user.get_full_name()}: pointage existe déjà")
            continue
        
        # Créer un pointage d'entrée SANS sortie
        time_in = datetime.strptime(times_in[i % len(times_in)], '%H:%M').time()
        
        attendance = Attendance.objects.create(
            employee=user,  # Utiliser user au lieu de employee_profile
            date=test_date,
            punch_type='in',
            time=time_in,  # Le champ s'appelle 'time', pas 'punch_in_time'
            latitude=Decimal('6.3703'),  # Cotonou
            longitude=Decimal('2.3912'),
            accuracy=Decimal('15.00'),
            status='missing_out'
        )
        
        print(f"   ✓ {user.get_full_name()}: Entrée à {time_in.strftime('%H:%M')} (sortie manquante)")
        created_count += 1

print(f"\n{'='*70}")
print(f"✅ {created_count} pointages créés avec oubli de sortie")
print(f"{'='*70}")

print("\n🔍 ÉTAPE SUIVANTE: Lancer la détection")
print("   python manage.py detect_missing_punches --days=7 --verbose")
print(f"{'='*70}")
