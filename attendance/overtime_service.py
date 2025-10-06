"""
Service pour le calcul automatique des heures supplémentaires.

Ce module contient la logique métier pour :
- Calculer automatiquement les heures supplémentaires à partir des pointages
- Créer les enregistrements OvertimeRecord
- Classifier les types d'heures supplémentaires

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date, timedelta, time
from decimal import Decimal

from .models import Attendance, OvertimeRecord, OvertimeConfiguration
from accounts.models import EmployeeProfile


class OvertimeCalculationService:
    """
    Service pour le calcul automatique des heures supplémentaires.
    """
    
    @staticmethod
    def calculate_daily_overtime(employee, target_date):
        """
        Calcule les heures supplémentaires quotidiennes pour un employé.
        """
        # Récupérer les pointages de la journée
        attendances = Attendance.objects.filter(
            employee=employee,
            date=target_date
        ).order_by('time')
        
        if not attendances.exists():
            return None
        
        # Calculer les heures travaillées
        total_hours = Decimal('0.00')
        punch_in = None
        
        for attendance in attendances:
            if attendance.punch_type == 'in':
                punch_in = attendance.time
            elif attendance.punch_type == 'out' and punch_in:
                # Calculer la durée
                duration = attendance.time - punch_in
                hours = Decimal(duration.total_seconds() / 3600).quantize(Decimal('0.01'))
                total_hours += hours
                punch_in = None
        
        # Vérifier s'il y a des heures supplémentaires
        config = OvertimeConfiguration.objects.filter(
            config_type='daily',
            is_active=True
        ).first()
        
        if not config:
            return None
        
        daily_limit = config.daily_hours_limit
        
        if total_hours > daily_limit:
            overtime_hours = total_hours - daily_limit
            normal_hours = daily_limit
            
            return {
                'total_hours': total_hours,
                'normal_hours': normal_hours,
                'overtime_hours': overtime_hours,
                'overtime_type': 'daily',
                'attendance_records': attendances
            }
        
        return None
    
    @staticmethod
    def calculate_weekly_overtime(employee, week_start_date):
        """
        Calcule les heures supplémentaires hebdomadaires pour un employé.
        """
        week_end_date = week_start_date + timedelta(days=6)
        
        # Récupérer tous les pointages de la semaine
        attendances = Attendance.objects.filter(
            employee=employee,
            punch_date__range=[week_start_date, week_end_date]
        ).order_by('date', 'time')
        
        if not attendances.exists():
            return None
        
        # Calculer les heures travaillées par jour
        daily_hours = {}
        punch_in = None
        current_date = None
        
        for attendance in attendances:
            if attendance.date != current_date:
                if punch_in and current_date:
                    # Il manque un punch out
                    pass
                punch_in = None
                current_date = attendance.date
                daily_hours[current_date] = Decimal('0.00')
            
            if attendance.punch_type == 'in':
                punch_in = attendance.time
            elif attendance.punch_type == 'out' and punch_in:
                duration = attendance.time - punch_in
                hours = Decimal(duration.total_seconds() / 3600).quantize(Decimal('0.01'))
                daily_hours[current_date] += hours
                punch_in = None
        
        # Calculer le total de la semaine
        total_hours = sum(daily_hours.values())
        
        # Vérifier s'il y a des heures supplémentaires hebdomadaires
        config = OvertimeConfiguration.objects.filter(
            config_type='weekly',
            is_active=True
        ).first()
        
        if not config:
            return None
        
        weekly_limit = config.weekly_hours_limit
        
        if total_hours > weekly_limit:
            overtime_hours = total_hours - weekly_limit
            normal_hours = weekly_limit
            
            return {
                'total_hours': total_hours,
                'normal_hours': normal_hours,
                'overtime_hours': overtime_hours,
                'overtime_type': 'weekly',
                'attendance_records': attendances
            }
        
        return None
    
    @staticmethod
    def calculate_weekend_overtime(employee, target_date):
        """
        Calcule les heures supplémentaires du weekend pour un employé.
        """
        if target_date.weekday() < 5:  # Pas un weekend
            return None
        
        # Récupérer les pointages du weekend
        attendances = Attendance.objects.filter(
            employee=employee,
            date=target_date
        ).order_by('time')
        
        if not attendances.exists():
            return None
        
        # Calculer les heures travaillées
        total_hours = Decimal('0.00')
        punch_in = None
        
        for attendance in attendances:
            if attendance.punch_type == 'in':
                punch_in = attendance.time
            elif attendance.punch_type == 'out' and punch_in:
                duration = attendance.time - punch_in
                hours = Decimal(duration.total_seconds() / 3600).quantize(Decimal('0.01'))
                total_hours += hours
                punch_in = None
        
        if total_hours > 0:
            return {
                'total_hours': total_hours,
                'normal_hours': Decimal('0.00'),
                'overtime_hours': total_hours,
                'overtime_type': 'weekend',
                'attendance_records': attendances
            }
        
        return None
    
    @staticmethod
    def calculate_night_overtime(employee, target_date):
        """
        Calcule les heures supplémentaires de nuit pour un employé.
        """
        # Récupérer les pointages de la journée
        attendances = Attendance.objects.filter(
            employee=employee,
            date=target_date
        ).order_by('time')
        
        if not attendances.exists():
            return None
        
        # Récupérer la configuration des heures de nuit
        config = OvertimeConfiguration.objects.filter(
            config_type='night',
            is_active=True
        ).first()
        
        if not config or not config.night_start_hour or not config.night_end_hour:
            return None
        
        night_start = config.night_start_hour
        night_end = config.night_end_hour
        
        # Calculer les heures de nuit travaillées
        night_hours = Decimal('0.00')
        punch_in = None
        
        for attendance in attendances:
            if attendance.punch_type == 'in':
                punch_in = attendance.time
            elif attendance.punch_type == 'out' and punch_in:
                start_time = punch_in.time()
                end_time = attendance.time.time()
                
                # Vérifier si cette période chevauche avec les heures de nuit
                if OvertimeCalculationService._is_night_time(start_time, end_time, night_start, night_end):
                    duration = attendance.time - punch_in
                    hours = Decimal(duration.total_seconds() / 3600).quantize(Decimal('0.01'))
                    night_hours += hours
                
                punch_in = None
        
        if night_hours > 0:
            return {
                'total_hours': night_hours,
                'normal_hours': Decimal('0.00'),
                'overtime_hours': night_hours,
                'overtime_type': 'night',
                'attendance_records': attendances
            }
        
        return None
    
    @staticmethod
    def _is_night_time(start_time, end_time, night_start, night_end):
        """
        Vérifie si une période de temps chevauche avec les heures de nuit.
        """
        # Cas simple : période de nuit dans la même journée
        if night_start < night_end:
            return (start_time >= night_start and start_time < night_end) or \
                   (end_time > night_start and end_time <= night_end) or \
                   (start_time <= night_start and end_time >= night_end)
        
        # Cas complexe : période de nuit sur deux jours (ex: 22h-06h)
        return start_time >= night_start or end_time <= night_end
    
    @staticmethod
    def create_overtime_record(employee, target_date, calculation_result):
        """
        Crée un enregistrement OvertimeRecord à partir des résultats de calcul.
        """
        # Récupérer le manager de l'employé
        try:
            profile = employee.employee_profile
            manager = profile.manager
        except EmployeeProfile.DoesNotExist:
            manager = None
        
        # Vérifier si un enregistrement existe déjà
        existing_record = OvertimeRecord.objects.filter(
            employee=employee,
            date=target_date,
            overtime_type=calculation_result['overtime_type']
        ).first()
        
        if existing_record:
            # Mettre à jour l'enregistrement existant
            existing_record.normal_hours = calculation_result['normal_hours']
            existing_record.overtime_hours = calculation_result['overtime_hours']
            existing_record.total_hours = calculation_result['total_hours']
            existing_record.save()
            
            # Mettre à jour les pointages associés
            existing_record.attendance_records.set(calculation_result['attendance_records'])
            
            return existing_record
        
        # Créer un nouvel enregistrement
        record = OvertimeRecord.objects.create(
            employee=employee,
            manager=manager,
            overtime_type=calculation_result['overtime_type'],
            date=target_date,
            normal_hours=calculation_result['normal_hours'],
            overtime_hours=calculation_result['overtime_hours'],
            total_hours=calculation_result['total_hours'],
            status='detected'
        )
        
        # Associer les pointages
        record.attendance_records.set(calculation_result['attendance_records'])
        
        return record
    
    @staticmethod
    def process_daily_overtime_for_date(target_date=None):
        """
        Traite les heures supplémentaires pour tous les employés actifs pour une date donnée.
        """
        if target_date is None:
            target_date = date.today()
        
        active_employees = User.objects.filter(
            employee_profile__is_active=True,
            employee_profile__can_punch=True
        )
        
        created_records = []
        
        for employee in active_employees:
            with transaction.atomic():
                # Calculer les heures supplémentaires quotidiennes
                daily_result = OvertimeCalculationService.calculate_daily_overtime(employee, target_date)
                if daily_result:
                    record = OvertimeCalculationService.create_overtime_record(
                        employee, target_date, daily_result
                    )
                    created_records.append(record)
                
                # Calculer les heures supplémentaires weekend
                weekend_result = OvertimeCalculationService.calculate_weekend_overtime(employee, target_date)
                if weekend_result:
                    record = OvertimeCalculationService.create_overtime_record(
                        employee, target_date, weekend_result
                    )
                    created_records.append(record)
                
                # Calculer les heures supplémentaires de nuit
                night_result = OvertimeCalculationService.calculate_night_overtime(employee, target_date)
                if night_result:
                    record = OvertimeCalculationService.create_overtime_record(
                        employee, target_date, night_result
                    )
                    created_records.append(record)
        
        return created_records
    
    @staticmethod
    def process_weekly_overtime_for_week(week_start_date=None):
        """
        Traite les heures supplémentaires hebdomadaires pour tous les employés actifs.
        """
        if week_start_date is None:
            # Calculer le lundi de la semaine courante
            today = date.today()
            days_since_monday = today.weekday()
            week_start_date = today - timedelta(days=days_since_monday)
        
        active_employees = User.objects.filter(
            employee_profile__is_active=True,
            employee_profile__can_punch=True
        )
        
        created_records = []
        
        for employee in active_employees:
            with transaction.atomic():
                # Calculer les heures supplémentaires hebdomadaires
                weekly_result = OvertimeCalculationService.calculate_weekly_overtime(employee, week_start_date)
                if weekly_result:
                    # Créer un enregistrement pour le vendredi de la semaine
                    friday_date = week_start_date + timedelta(days=4)
                    record = OvertimeCalculationService.create_overtime_record(
                        employee, friday_date, weekly_result
                    )
                    created_records.append(record)
        
        return created_records
