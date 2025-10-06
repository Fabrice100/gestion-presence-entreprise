"""
Signals pour le calcul automatique des heures supplémentaires.

Ce module contient les signaux Django pour :
- Calculer automatiquement les heures supplémentaires après chaque pointage
- Traiter les heures supplémentaires à la fin de la journée

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import date, timedelta
import logging

from .models import Attendance, OvertimeRecord
from .overtime_service import OvertimeCalculationService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Attendance)
def calculate_overtime_on_attendance_change(sender, instance, created, **kwargs):
    """
    Calcule les heures supplémentaires après chaque modification de pointage.
    """
    try:
        # Ne traiter que les pointages de sortie (pour avoir une session complète)
        if instance.punch_type == 'out':
            target_date = instance.date
            
            # Calculer les heures supplémentaires pour cet employé et cette date
            with OvertimeCalculationService:
                # Heures supplémentaires quotidiennes
                daily_result = OvertimeCalculationService.calculate_daily_overtime(
                    instance.employee, target_date
                )
                if daily_result:
                    OvertimeCalculationService.create_overtime_record(
                        instance.employee, target_date, daily_result
                    )
                
                # Heures supplémentaires weekend
                weekend_result = OvertimeCalculationService.calculate_weekend_overtime(
                    instance.employee, target_date
                )
                if weekend_result:
                    OvertimeCalculationService.create_overtime_record(
                        instance.employee, target_date, weekend_result
                    )
                
                # Heures supplémentaires de nuit
                night_result = OvertimeCalculationService.calculate_night_overtime(
                    instance.employee, target_date
                )
                if night_result:
                    OvertimeCalculationService.create_overtime_record(
                        instance.employee, target_date, night_result
                    )
        
        logger.info(f"Heures supplémentaires calculées pour {instance.employee.username} le {instance.date}")
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des heures supplémentaires: {e}")


@receiver(post_delete, sender=Attendance)
def recalculate_overtime_on_attendance_delete(sender, instance, **kwargs):
    """
    Recalcule les heures supplémentaires après suppression d'un pointage.
    """
    try:
        target_date = instance.date
        
        # Supprimer les enregistrements d'heures supplémentaires existants pour cette date
        OvertimeRecord.objects.filter(
            employee=instance.employee,
            date=target_date
        ).delete()
        
        # Recalculer les heures supplémentaires pour cette date
        with OvertimeCalculationService:
            # Heures supplémentaires quotidiennes
            daily_result = OvertimeCalculationService.calculate_daily_overtime(
                instance.employee, target_date
            )
            if daily_result:
                OvertimeCalculationService.create_overtime_record(
                    instance.employee, target_date, daily_result
                )
            
            # Heures supplémentaires weekend
            weekend_result = OvertimeCalculationService.calculate_weekend_overtime(
                instance.employee, target_date
            )
            if weekend_result:
                OvertimeCalculationService.create_overtime_record(
                    instance.employee, target_date, weekend_result
                )
            
            # Heures supplémentaires de nuit
            night_result = OvertimeCalculationService.calculate_night_overtime(
                instance.employee, target_date
            )
            if night_result:
                OvertimeCalculationService.create_overtime_record(
                    instance.employee, target_date, night_result
                )
        
        logger.info(f"Heures supplémentaires recalculées après suppression pour {instance.employee.username} le {instance.date}")
        
    except Exception as e:
        logger.error(f"Erreur lors du recalcul des heures supplémentaires: {e}")
