"""
Test rapide du calcul des heures avec profils horaires.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from datetime import time, date
from accounts.models import EmployeeProfile, WorkSchedule
from attendance.hours_calculation_service import HoursCalculationService

# Récupérer un employé de test
employee = EmployeeProfile.objects.first()
schedule = employee.current_work_schedule

print("=" * 70)
print("🧪 TEST CALCUL HEURES AVEC PROFIL HORAIRE")
print("=" * 70)
print()
print(f"Employé: {employee}")
print(f"Profil horaire: {schedule}")
print(f"Horaires contractuels: {schedule.start_time.strftime('%H:%M')} - {schedule.end_time.strftime('%H:%M')}")
print(f"Pause: {schedule.pause_start.strftime('%H:%M')} - {schedule.pause_end.strftime('%H:%M')}")
print()

# Tests de différents scénarios
scenarios = [
    ("Horaires normaux", time(8, 0), time(18, 0)),
    ("Arrivée avant HDC", time(7, 0), time(18, 0)),
    ("Départ après HFC", time(8, 0), time(19, 0)),
    ("Arrivée avant + Départ après", time(7, 0), time(19, 0)),
    ("Demi-journée matin", time(8, 0), time(12, 0)),
    ("Demi-journée après-midi", time(14, 0), time(18, 0)),
    ("Arrivée tardive", time(10, 0), time(18, 0)),
    ("Départ anticipé", time(8, 0), time(16, 0)),
]

print("📊 SCÉNARIOS DE TEST:")
print("-" * 70)
print(f"{'Scénario':<30} | {'Pointage':<15} | {'Heures calculées':>15}")
print("-" * 70)

for scenario_name, in_time, out_time in scenarios:
    hours = HoursCalculationService.calculate_worked_hours(
        in_time, 
        out_time,
        employee_profile=employee,
        attendance_date=date.today()
    )
    
    pointage = f"{in_time.strftime('%H:%M')} → {out_time.strftime('%H:%M')}"
    print(f"{scenario_name:<30} | {pointage:<15} | {hours:>15} heures")

print("-" * 70)
print()
print("✅ TESTS TERMINÉS")
print("=" * 70)
