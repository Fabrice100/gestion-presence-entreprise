"""
Service de gestion des jours fériés du Togo.

Ce module contient la logique métier pour :
- Initialisation des jours fériés du Togo
- Gestion des jours fériés récurrents
- Vérification des conflits avec les congés
- Calendrier des congés

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.utils import timezone
from datetime import date, timedelta
from typing import List, Dict, Optional
import calendar

from .models import Holiday, LeaveRequest
from common.structured_logging import structured_logger


class HolidayService:
    """
    Service centralisé pour la gestion des jours fériés du Togo.
    """
    
    # Jours fériés fixes du Togo
    TOGO_FIXED_HOLIDAYS = [
        {'name': 'Jour de l\'An', 'date': '01-01', 'type': 'national'},
        {'name': 'Fête du Travail', 'date': '05-01', 'type': 'national'},
        {'name': 'Fête Nationale', 'date': '04-27', 'type': 'national'},
        {'name': 'Fête de l\'Indépendance', 'date': '04-27', 'type': 'national'},
        {'name': 'Noël', 'date': '12-25', 'type': 'religious'},
    ]
    
    # Jours fériés variables (calculés chaque année)
    TOGO_VARIABLE_HOLIDAYS = [
        {'name': 'Lundi de Pâques', 'type': 'religious', 'calculation': 'easter_monday'},
        {'name': 'Ascension', 'type': 'religious', 'calculation': 'ascension'},
        {'name': 'Lundi de Pentecôte', 'type': 'religious', 'calculation': 'pentecost_monday'},
        {'name': 'Assomption', 'date': '08-15', 'type': 'religious'},
        {'name': 'Toussaint', 'date': '11-01', 'type': 'religious'},
    ]
    
    def __init__(self):
        self.logger = structured_logger.attendance_logger
    
    def initialize_togo_holidays(self, year: int = None) -> Dict[str, int]:
        """
        Initialise les jours fériés du Togo pour une année.
        
        Args:
            year: Année (défaut: année courante)
            
        Returns:
            Dict avec le nombre de jours fériés créés
        """
        if year is None:
            year = timezone.now().year
        
        created_count = 0
        updated_count = 0
        
        # Créer les jours fériés fixes
        for holiday_data in self.TOGO_FIXED_HOLIDAYS:
            holiday_date = date(year, int(holiday_data['date'][:2]), int(holiday_data['date'][3:]))
            
            holiday, created = Holiday.objects.get_or_create(
                name=holiday_data['name'],
                date=holiday_date,
                defaults={
                    'holiday_type': holiday_data['type'],
                    'is_recurring': True,
                    'is_active': True,
                    'description': f"Jour férié {holiday_data['type']} du Togo"
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        # Créer les jours fériés variables
        for holiday_data in self.TOGO_VARIABLE_HOLIDAYS:
            if 'date' in holiday_data:
                # Jours fériés avec date fixe
                holiday_date = date(year, int(holiday_data['date'][:2]), int(holiday_data['date'][3:]))
            else:
                # Jours fériés calculés
                holiday_date = self._calculate_variable_holiday(holiday_data['calculation'], year)
            
            if holiday_date:
                holiday, created = Holiday.objects.get_or_create(
                    name=holiday_data['name'],
                    date=holiday_date,
                    defaults={
                        'holiday_type': holiday_data['type'],
                        'is_recurring': True,
                        'is_active': True,
                        'description': f"Jour férié {holiday_data['type']} du Togo"
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        
        self.logger.info(
            "Jours fériés du Togo initialisés",
            year=year,
            created_count=created_count,
            updated_count=updated_count,
            event_type="togo_holidays_initialized"
        )
        
        return {
            'created': created_count,
            'updated': updated_count,
            'total': created_count + updated_count
        }
    
    def _calculate_variable_holiday(self, calculation_type: str, year: int) -> Optional[date]:
        """
        Calcule la date d'un jour férié variable.
        
        Args:
            calculation_type: Type de calcul
            year: Année
            
        Returns:
            Date du jour férié ou None
        """
        if calculation_type == 'easter_monday':
            return self._calculate_easter_monday(year)
        elif calculation_type == 'ascension':
            return self._calculate_ascension(year)
        elif calculation_type == 'pentecost_monday':
            return self._calculate_pentecost_monday(year)
        
        return None
    
    def _calculate_easter_monday(self, year: int) -> date:
        """Calcule le lundi de Pâques."""
        easter = self._calculate_easter(year)
        return easter + timedelta(days=1)
    
    def _calculate_ascension(self, year: int) -> date:
        """Calcule l'Ascension (39 jours après Pâques)."""
        easter = self._calculate_easter(year)
        return easter + timedelta(days=39)
    
    def _calculate_pentecost_monday(self, year: int) -> date:
        """Calcule le lundi de Pentecôte (50 jours après Pâques)."""
        easter = self._calculate_easter(year)
        return easter + timedelta(days=50)
    
    def _calculate_easter(self, year: int) -> date:
        """
        Calcule la date de Pâques pour une année donnée.
        Utilise l'algorithme de Gauss.
        """
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        n = (h + l - 7 * m + 114) // 31
        p = (h + l - 7 * m + 114) % 31
        
        return date(year, n, p + 1)
    
    def get_holidays_in_period(self, start_date: date, end_date: date) -> List[Dict[str, any]]:
        """
        Récupère les jours fériés dans une période.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Liste des jours fériés avec leurs informations
        """
        holidays = Holiday.objects.filter(
            date__range=[start_date, end_date],
            is_active=True
        ).order_by('date')
        
        return [
            {
                'id': holiday.id,
                'name': holiday.name,
                'date': holiday.date,
                'type': holiday.holiday_type,
                'description': holiday.description,
                'is_recurring': holiday.is_recurring
            }
            for holiday in holidays
        ]
    
    def is_holiday(self, check_date: date) -> bool:
        """
        Vérifie si une date est un jour férié.
        
        Args:
            check_date: Date à vérifier
            
        Returns:
            True si c'est un jour férié
        """
        return Holiday.objects.filter(
            date=check_date,
            is_active=True
        ).exists()
    
    def get_working_days_in_period(self, start_date: date, end_date: date) -> int:
        """
        Calcule le nombre de jours ouvrables dans une période.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Nombre de jours ouvrables
        """
        current_date = start_date
        working_days = 0
        
        while current_date <= end_date:
            # Exclure les weekends (samedi=5, dimanche=6)
            if current_date.weekday() < 5:
                # Exclure les jours fériés
                if not self.is_holiday(current_date):
                    working_days += 1
            
            current_date += timedelta(days=1)
        
        return working_days
    
    def get_leave_calendar(self, year: int = None, month: int = None) -> Dict[str, any]:
        """
        Génère un calendrier des congés et jours fériés.
        
        Args:
            year: Année (défaut: année courante)
            month: Mois (défaut: mois courant)
            
        Returns:
            Dict avec les données du calendrier
        """
        if year is None:
            year = timezone.now().year
        if month is None:
            month = timezone.now().month
        
        # Initialiser les jours fériés si nécessaire
        self.initialize_togo_holidays(year)
        
        # Récupérer les jours fériés du mois
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        holidays = self.get_holidays_in_period(month_start, month_end)
        
        # Récupérer les congés approuvés du mois
        approved_leaves = LeaveRequest.objects.filter(
            status='approved',
            start_date__lte=month_end,
            end_date__gte=month_start
        ).select_related('employee', 'leave_type')
        
        # Construire le calendrier
        calendar_data = []
        current_date = month_start
        
        while current_date <= month_end:
            day_info = {
                'date': current_date,
                'is_holiday': self.is_holiday(current_date),
                'is_weekend': current_date.weekday() >= 5,
                'holiday_name': None,
                'leaves': []
            }
            
            # Ajouter les informations de jour férié
            for holiday in holidays:
                if holiday['date'] == current_date:
                    day_info['holiday_name'] = holiday['name']
                    break
            
            # Ajouter les congés
            for leave in approved_leaves:
                if leave.start_date <= current_date <= leave.end_date:
                    day_info['leaves'].append({
                        'employee': leave.employee.get_full_name() or leave.employee.username,
                        'leave_type': leave.leave_type.name,
                        'leave_type_color': leave.leave_type.color
                    })
            
            calendar_data.append(day_info)
            current_date += timedelta(days=1)
        
        return {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'days': calendar_data,
            'holidays': holidays,
            'total_holidays': len(holidays),
            'total_working_days': self.get_working_days_in_period(month_start, month_end)
        }
    
    def check_leave_conflicts(self, start_date: date, end_date: date, 
                            exclude_request_id: int = None) -> List[Dict[str, any]]:
        """
        Vérifie les conflits de congés dans une période.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            exclude_request_id: ID de demande à exclure
            
        Returns:
            Liste des conflits détectés
        """
        conflicts = []
        
        # Vérifier les jours fériés
        holidays = self.get_holidays_in_period(start_date, end_date)
        if holidays:
            conflicts.append({
                'type': 'holiday',
                'message': 'Période contient des jours fériés',
                'details': holidays
            })
        
        # Vérifier les weekends
        current_date = start_date
        weekend_days = []
        while current_date <= end_date:
            if current_date.weekday() >= 5:
                weekend_days.append(current_date)
            current_date += timedelta(days=1)
        
        if weekend_days:
            conflicts.append({
                'type': 'weekend',
                'message': 'Période contient des weekends',
                'details': weekend_days
            })
        
        # Vérifier les congés existants
        existing_leaves = LeaveRequest.objects.filter(
            status__in=['pending', 'approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        if exclude_request_id:
            existing_leaves = existing_leaves.exclude(id=exclude_request_id)
        
        if existing_leaves.exists():
            conflicts.append({
                'type': 'leave_conflict',
                'message': 'Conflit avec des congés existants',
                'details': [
                    {
                        'employee': leave.employee.get_full_name() or leave.employee.username,
                        'start_date': leave.start_date,
                        'end_date': leave.end_date,
                        'leave_type': leave.leave_type.name
                    }
                    for leave in existing_leaves
                ]
            })
        
        return conflicts


# Instance globale du service
holiday_service = HolidayService()
