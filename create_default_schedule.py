"""
Script pour créer le profil horaire par défaut et l'affecter aux employés existants.
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from datetime import time, date
from accounts.models import WorkSchedule, EmployeeProfile, EmployeeScheduleHistory
from django.contrib.auth.models import User

def create_default_schedule():
    """Crée le profil horaire par défaut 'Bureau Standard'."""
    
    # Vérifier si le profil existe déjà
    schedule, created = WorkSchedule.objects.get_or_create(
        name="Bureau Standard",
        defaults={
            'description': "Profil horaire standard pour employés de bureau (8h-18h avec pause 12h-14h)",
            'start_time': time(8, 0),
            'end_time': time(18, 0),
            'pause_start': time(12, 0),
            'pause_end': time(14, 0),
            'is_default': True,
        }
    )
    
    if created:
        print(f"✅ Profil '{schedule.name}' créé avec succès")
    else:
        print(f"ℹ️  Profil '{schedule.name}' existe déjà")
    
    return schedule


def assign_to_existing_employees(schedule):
    """Affecte le profil par défaut à tous les employés existants."""
    
    # Récupérer tous les employés sans profil horaire
    employees_without_schedule = EmployeeProfile.objects.filter(
        current_work_schedule__isnull=True
    )
    
    count = 0
    today = date.today()
    
    # Récupérer le premier superuser (ou créer un user système)
    system_user = User.objects.filter(is_superuser=True).first()
    
    for employee in employees_without_schedule:
        # Affecter le profil
        employee.current_work_schedule = schedule
        employee.save()
        
        # Créer l'historique
        EmployeeScheduleHistory.objects.create(
            employee=employee,
            work_schedule=schedule,
            assigned_date=today,
            assigned_by=system_user
        )
        
        count += 1
        print(f"  ✅ {employee.employee_id} - {employee.user.get_full_name()}")
    
    if count > 0:
        print(f"\n✅ {count} employés affectés au profil '{schedule.name}'")
    else:
        print(f"\nℹ️  Tous les employés ont déjà un profil horaire")


def main():
    """Fonction principale."""
    print("=" * 60)
    print("🕐 CRÉATION DU PROFIL HORAIRE PAR DÉFAUT")
    print("=" * 60)
    print()
    
    # 1. Créer le profil par défaut
    schedule = create_default_schedule()
    print()
    
    # 2. Afficher les détails
    print(f"📋 Détails du profil:")
    print(f"  - Nom: {schedule.name}")
    print(f"  - Horaires: {schedule.start_time.strftime('%H:%M')} - {schedule.end_time.strftime('%H:%M')}")
    print(f"  - Pause: {schedule.pause_start.strftime('%H:%M')} - {schedule.pause_end.strftime('%H:%M')}")
    print(f"  - Durée pause: {schedule.get_pause_duration_hours()}h")
    print(f"  - Durée travail: {schedule.get_contractual_duration_hours()}h/jour")
    print()
    
    # 3. Affecter aux employés existants
    print("📌 Affectation aux employés existants:")
    assign_to_existing_employees(schedule)
    print()
    
    print("=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)


if __name__ == '__main__':
    main()
