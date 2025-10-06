"""
Script d'initialisation des configurations d'heures supplémentaires.

Ce script crée les configurations par défaut pour les heures supplémentaires
selon les standards togolais et les bonnes pratiques.

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.models import OvertimeConfiguration

def create_default_overtime_configurations():
    """
    Crée les configurations par défaut pour les heures supplémentaires.
    """
    
    configurations_data = [
        {
            'name': 'Heures supplémentaires quotidiennes',
            'config_type': 'daily',
            'daily_hours_limit': 8.00,
            'weekly_hours_limit': 40.00,
            'is_active': True
        },
        {
            'name': 'Heures supplémentaires weekend',
            'config_type': 'weekend',
            'daily_hours_limit': 8.00,
            'weekly_hours_limit': 40.00,
            'is_active': True
        },
        {
            'name': 'Heures supplémentaires jours fériés',
            'config_type': 'holiday',
            'daily_hours_limit': 8.00,
            'weekly_hours_limit': 40.00,
            'is_active': True
        },
        {
            'name': 'Heures supplémentaires de nuit',
            'config_type': 'night',
            'daily_hours_limit': 8.00,
            'weekly_hours_limit': 40.00,
            'night_start_hour': '22:00',
            'night_end_hour': '06:00',
            'is_active': True
        },
        {
            'name': 'Heures supplémentaires hebdomadaires',
            'config_type': 'weekly',
            'daily_hours_limit': 8.00,
            'weekly_hours_limit': 40.00,
            'is_active': True
        }
    ]
    
    print("INITIALISATION DES CONFIGURATIONS D'HEURES SUPPLÉMENTAIRES")
    print("==========================================================")
    
    created_count = 0
    for config_data in configurations_data:
        config, created = OvertimeConfiguration.objects.get_or_create(
            name=config_data['name'],
            defaults=config_data
        )
        
        if created:
            created_count += 1
            print(f"[OK] Configuration creee : {config.name}")
        else:
            print(f"[INFO] Configuration existante : {config.name}")
    
    print(f"\nConfigurations d'heures supplementaires creees : {created_count}")
    print("\nCONFIGURATIONS PAR DEFAUT :")
    print("=" * 50)
    print("Quotidiennes : Limite 8h/jour")
    print("Weekend : Suivi des heures samedi/dimanche")
    print("Jours feries : Suivi des heures jours feries")
    print("Nuit : Suivi des heures 22h-06h")
    print("Hebdomadaires : Limite 40h/semaine")
    print("\nCes configurations permettent le suivi des heures supplementaires.")
    print("Pas de calculs financiers - focus sur la gestion de presence.")

if __name__ == '__main__':
    with transaction.atomic():
        create_default_overtime_configurations()
    
    print("\n[SUCCESS] INITIALISATION TERMINEE AVEC SUCCES !")
    print("===============================================")
