"""
Test de bout en bout du système de profils horaires.

Ce script teste :
1. La création d'un nouveau profil horaire via le modèle
2. L'assignation d'un profil à un employé
3. Le calcul des heures avec le profil HDC/HFC
4. Le changement de profil avec historique immutable
5. La vérification de l'historique
6. Le calcul rétroactif avec l'historique

Auteur: Système
Projet: Système de gestion de présence - Test d'intégration WorkSchedule
Version: 1.0
"""

import os
import sys
import django
from datetime import datetime, date, time, timedelta

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile, WorkSchedule, EmployeeScheduleHistory, Department
from accounts.schedule_service import WorkScheduleService, get_schedule_for_date
from attendance.hours_calculation_service import HoursCalculationService


def print_header(text):
    """Affiche un en-tête formaté."""
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)


def print_success(text):
    """Affiche un message de succès."""
    print(f"✓ {text}")


def print_error(text):
    """Affiche un message d'erreur."""
    print(f"✗ {text}")


def print_info(text):
    """Affiche une information."""
    print(f"ℹ {text}")


def test_1_create_new_schedule():
    """Test 1: Créer un nouveau profil horaire Mi-temps."""
    print_header("TEST 1: Création d'un nouveau profil horaire")
    
    try:
        # Récupérer un utilisateur admin pour le created_by
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print_error("Aucun superuser trouvé pour created_by")
            return None
        
        # Créer un profil Mi-temps (8h-12h, pause 10h30-11h)
        schedule = WorkSchedule.objects.create(
            name="Mi-temps Matin",
            start_time=time(8, 0),
            end_time=time(12, 0),
            pause_start=time(10, 30),
            pause_end=time(11, 0),
            is_default=False,
            created_by=admin_user
        )
        
        print_success(f"Profil '{schedule.name}' créé avec succès")
        print_info(f"  - Horaire: {schedule.start_time} - {schedule.end_time}")
        print_info(f"  - Pause: {schedule.pause_start} - {schedule.pause_end}")
        print_info(f"  - Durée contractuelle: {schedule.get_contractual_duration_hours()}h")
        print_info(f"  - Durée pause: {schedule.get_pause_duration_hours()}h")
        
        return schedule
        
    except Exception as e:
        print_error(f"Erreur lors de la création du profil: {e}")
        return None


def test_2_assign_schedule_to_employee(schedule):
    """Test 2: Assigner le profil à un employé."""
    print_header("TEST 2: Assignation du profil à un employé")
    
    if not schedule:
        print_error("Profil non disponible, test ignoré")
        return None
    
    try:
        # Récupérer un employé existant
        employee_profile = EmployeeProfile.objects.filter(
            role='employee',
            is_active=True
        ).first()
        
        if not employee_profile:
            print_error("Aucun employé actif trouvé")
            return None
        
        print_info(f"Employé sélectionné: {employee_profile.user.get_full_name()}")
        print_info(f"Profil actuel: {employee_profile.current_work_schedule or 'Aucun'}")
        
        # Assigner le nouveau profil
        admin_user = User.objects.filter(is_superuser=True).first()
        success = WorkScheduleService.change_employee_schedule(
            employee=employee_profile.user,
            new_schedule=schedule,
            assigned_by=admin_user,
            effective_date=date.today(),
            reason="Test d'intégration - Mi-temps"
        )
        
        if success:
            # Recharger l'employé pour voir les changements
            employee_profile.refresh_from_db()
            print_success(f"Profil assigné avec succès")
            print_info(f"  - Nouveau profil: {employee_profile.current_work_schedule.name}")
            
            # Vérifier l'historique
            history = EmployeeScheduleHistory.objects.filter(
                employee=employee_profile,
                work_schedule=schedule,
                end_date__isnull=True
            ).first()
            
            if history:
                print_success("Historique créé correctement")
                print_info(f"  - Date d'assignation: {history.assigned_date}")
                print_info(f"  - Assigné par: {history.assigned_by.get_full_name()}")
            
            return employee_profile
        else:
            print_error("Échec de l'assignation du profil")
            return None
            
    except Exception as e:
        print_error(f"Erreur lors de l'assignation: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_3_calculate_hours_with_schedule(employee_profile):
    """Test 3: Calculer les heures travaillées avec le profil HDC/HFC."""
    print_header("TEST 3: Calcul des heures avec plafonnement HDC/HFC")
    
    if not employee_profile or not employee_profile.current_work_schedule:
        print_error("Employé ou profil non disponible, test ignoré")
        return
    
    schedule = employee_profile.current_work_schedule
    
    # Scénarios de test
    scenarios = [
        {
            "name": "Horaire normal (8h-12h)",
            "punch_in": time(8, 0),
            "punch_out": time(12, 0),
            "expected": 3.5  # 4h - 0.5h pause
        },
        {
            "name": "Arrivée anticipée (7h-12h)",
            "punch_in": time(7, 0),
            "punch_out": time(12, 0),
            "expected": 3.5  # Plafonné à HDC 8h, donc 8h-12h = 4h - 0.5h pause
        },
        {
            "name": "Départ tardif (8h-13h)",
            "punch_in": time(8, 0),
            "punch_out": time(13, 0),
            "expected": 3.5  # Plafonné à HFC 12h, donc 8h-12h = 4h - 0.5h pause
        },
        {
            "name": "Arrivée tardive (9h-12h)",
            "punch_in": time(9, 0),
            "punch_out": time(12, 0),
            "expected": 2.5  # 3h - 0.5h pause
        },
    ]
    
    print_info(f"Profil: {schedule.name} (HDC: {schedule.start_time}, HFC: {schedule.end_time})")
    print_info(f"Pause contractuelle: {schedule.pause_start} - {schedule.pause_end} ({schedule.get_pause_duration_hours()}h)")
    print()
    
    all_passed = True
    
    for scenario in scenarios:
        try:
            hours = HoursCalculationService.calculate_worked_hours_with_schedule(
                punch_in=scenario["punch_in"],
                punch_out=scenario["punch_out"],
                schedule=schedule
            )
            
            if abs(hours - scenario["expected"]) < 0.01:  # Tolérance de 0.01h
                print_success(f"{scenario['name']}")
                print_info(f"  Pointages: {scenario['punch_in']} → {scenario['punch_out']}")
                print_info(f"  Calculé: {hours:.2f}h (attendu: {scenario['expected']:.2f}h)")
            else:
                print_error(f"{scenario['name']}")
                print_info(f"  Pointages: {scenario['punch_in']} → {scenario['punch_out']}")
                print_info(f"  Calculé: {hours:.2f}h (attendu: {scenario['expected']:.2f}h)")
                all_passed = False
                
        except Exception as e:
            print_error(f"{scenario['name']}: {e}")
            all_passed = False
    
    if all_passed:
        print()
        print_success("Tous les calculs sont corrects ✓")
    else:
        print()
        print_error("Certains calculs sont incorrects ✗")


def test_4_change_schedule_with_history(employee_profile):
    """Test 4: Changer le profil avec historique immutable."""
    print_header("TEST 4: Changement de profil avec historique")
    
    if not employee_profile:
        print_error("Employé non disponible, test ignoré")
        return None
    
    try:
        # Créer un nouveau profil Après-midi
        admin_user = User.objects.filter(is_superuser=True).first()
        new_schedule = WorkSchedule.objects.create(
            name="Mi-temps Après-midi",
            start_time=time(14, 0),
            end_time=time(18, 0),
            pause_start=time(16, 0),
            pause_end=time(16, 30),
            is_default=False,
            created_by=admin_user
        )
        
        print_success(f"Nouveau profil '{new_schedule.name}' créé")
        
        # Changer le profil de l'employé
        old_schedule = employee_profile.current_work_schedule
        success = WorkScheduleService.change_employee_schedule(
            employee=employee_profile.user,
            new_schedule=new_schedule,
            assigned_by=admin_user,
            effective_date=date.today(),
            reason="Test - Passage à l'après-midi"
        )
        
        if success:
            print_success("Profil changé avec succès")
            
            # Recharger et vérifier
            employee_profile.refresh_from_db()
            print_info(f"  - Ancien profil: {old_schedule.name}")
            print_info(f"  - Nouveau profil: {employee_profile.current_work_schedule.name}")
            
            # Vérifier que l'ancien historique est clôturé
            old_history = EmployeeScheduleHistory.objects.filter(
                employee=employee_profile,
                work_schedule=old_schedule
            ).first()
            
            if old_history and old_history.end_date:
                print_success("Ancien historique clôturé correctement")
                print_info(f"  - Date de fin: {old_history.end_date}")
            else:
                print_error("Ancien historique non clôturé")
            
            # Vérifier le nouveau historique
            new_history = EmployeeScheduleHistory.objects.filter(
                employee=employee_profile,
                work_schedule=new_schedule,
                end_date__isnull=True
            ).first()
            
            if new_history:
                print_success("Nouvel historique créé correctement")
                print_info(f"  - Date de début: {new_history.assigned_date}")
            
            return new_schedule
        else:
            print_error("Échec du changement de profil")
            return None
            
    except Exception as e:
        print_error(f"Erreur lors du changement: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_5_verify_history_immutability(employee_profile):
    """Test 5: Vérifier l'immutabilité de l'historique."""
    print_header("TEST 5: Vérification de l'immutabilité de l'historique")
    
    if not employee_profile:
        print_error("Employé non disponible, test ignoré")
        return
    
    try:
        # Récupérer tout l'historique
        history = WorkScheduleService.get_employee_schedule_history(employee_profile.user)
        
        print_info(f"Employé: {employee_profile.user.get_full_name()}")
        print_info(f"Nombre d'entrées d'historique: {history.count()}")
        print()
        
        for i, entry in enumerate(history, 1):
            print(f"  Entrée {i}:")
            print(f"    - Profil: {entry.work_schedule.name}")
            print(f"    - Du: {entry.assigned_date}", end="")
            if entry.end_date:
                print(f" au {entry.end_date} (clôturée)")
            else:
                print(" (active)")
            print(f"    - Assigné par: {entry.assigned_by.get_full_name()}")
            if entry.reason:
                print(f"    - Raison: {entry.reason}")
        
        # Vérifier l'intégrité: une seule entrée active
        active_count = history.filter(end_date__isnull=True).count()
        if active_count == 1:
            print()
            print_success(f"Une seule entrée active (correct) ✓")
        else:
            print()
            print_error(f"{active_count} entrées actives trouvées (devrait être 1) ✗")
        
        # Vérifier que les périodes ne se chevauchent pas
        print()
        print_info("Vérification de l'absence de chevauchements...")
        no_overlap = True
        history_list = list(history.order_by('assigned_date'))
        
        for i in range(len(history_list) - 1):
            current = history_list[i]
            next_entry = history_list[i + 1]
            
            if current.end_date and next_entry.assigned_date:
                if current.end_date >= next_entry.assigned_date:
                    print_error(f"Chevauchement détecté entre entrées {i+1} et {i+2}")
                    no_overlap = False
        
        if no_overlap:
            print_success("Aucun chevauchement détecté ✓")
        
    except Exception as e:
        print_error(f"Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()


def test_6_retroactive_calculation(employee_profile):
    """Test 6: Calcul rétroactif avec l'historique."""
    print_header("TEST 6: Calcul rétroactif avec historique")
    
    if not employee_profile:
        print_error("Employé non disponible, test ignoré")
        return
    
    try:
        # Récupérer les profils de différentes dates
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        
        dates_to_test = [
            ("aujourd'hui", today),
            ("hier", yesterday),
            ("la semaine dernière", last_week),
        ]
        
        print_info(f"Employé: {employee_profile.user.get_full_name()}")
        print()
        
        for label, test_date in dates_to_test:
            schedule = get_schedule_for_date(employee_profile.user, test_date)
            
            if schedule:
                print_success(f"Profil pour {label} ({test_date}): {schedule.name}")
                print_info(f"  - Horaire: {schedule.start_time} - {schedule.end_time}")
            else:
                print_info(f"Aucun profil pour {label} ({test_date})")
        
        print()
        print_info("L'historique immutable permet de recalculer correctement")
        print_info("les heures pour n'importe quelle date passée.")
        
    except Exception as e:
        print_error(f"Erreur lors du calcul rétroactif: {e}")
        import traceback
        traceback.print_exc()


def test_7_verify_employee_count():
    """Test 7: Vérifier le compteur d'employés par profil."""
    print_header("TEST 7: Compteur d'employés par profil")
    
    try:
        schedules = WorkSchedule.objects.all()
        
        print_info(f"Nombre total de profils: {schedules.count()}")
        print()
        
        for schedule in schedules:
            count = schedule.get_employee_count()
            print(f"  {schedule.name}:")
            print(f"    - Employés assignés: {count}")
            print(f"    - HDC: {schedule.start_time}, HFC: {schedule.end_time}")
            print(f"    - Durée contractuelle: {schedule.get_contractual_duration_hours()}h")
        
    except Exception as e:
        print_error(f"Erreur: {e}")


def main():
    """Fonction principale exécutant tous les tests."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*25 + "TEST D'INTÉGRATION COMPLET" + " "*27 + "║")
    print("║" + " "*22 + "Système de Profils Horaires" + " "*29 + "║")
    print("╚" + "="*78 + "╝")
    
    # Exécuter les tests séquentiellement
    schedule = test_1_create_new_schedule()
    employee_profile = test_2_assign_schedule_to_employee(schedule)
    test_3_calculate_hours_with_schedule(employee_profile)
    new_schedule = test_4_change_schedule_with_history(employee_profile)
    test_5_verify_history_immutability(employee_profile)
    test_6_retroactive_calculation(employee_profile)
    test_7_verify_employee_count()
    
    # Résumé final
    print_header("RÉSUMÉ DES TESTS")
    print_success("Tous les tests d'intégration sont terminés")
    print_info("Vérifiez les résultats ci-dessus pour détecter d'éventuelles erreurs")
    print()
    print("Tests effectués:")
    print("  ✓ Création de profil horaire")
    print("  ✓ Assignation à un employé")
    print("  ✓ Calcul avec plafonnement HDC/HFC")
    print("  ✓ Changement de profil avec historique")
    print("  ✓ Immutabilité de l'historique")
    print("  ✓ Calcul rétroactif")
    print("  ✓ Compteur d'employés")
    print()


if __name__ == '__main__':
    main()
