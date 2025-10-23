"""
Service pour le calcul des heures de travail.

Implémente les règles métier pour:
- Calcul des heures travaillées avec pause de 1h
- Plafonnement à 8h maximum par jour
- Gestion des oublis de sortie (worked_hours = NULL)
- Validation des séquences de pointage
"""

from datetime import datetime, time, timedelta, date
from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from attendance.models import Attendance, AttendanceAnomaly


class HoursCalculationService:
    """
    Service principal pour le calcul des heures travaillées.
    
    Règles métier:
    - Pause: 1h automatique déduite
    - Plafond: 8h maximum par jour
    - Oubli sortie: worked_hours = NULL
    - Validation: Bloquer sortie sans entrée
    """
    
    # Constantes
    PAUSE_DURATION_HOURS = Decimal('1.00')  # 1h de pause fixe
    MAX_DAILY_HOURS = Decimal('8.00')  # Plafond de 8h
    
    @staticmethod
    def calculate_duration_hours(in_time, out_time):
        """
        Calcule la durée brute entre entrée et sortie en heures.
        
        Args:
            in_time (time): Heure d'entrée
            out_time (time): Heure de sortie
            
        Returns:
            Decimal: Durée en heures (2 décimales)
        """
        # Convertir en datetime pour calcul
        today = date.today()
        in_datetime = datetime.combine(today, in_time)
        out_datetime = datetime.combine(today, out_time)
        
        # Si sortie avant entrée, c'est le lendemain
        if out_datetime < in_datetime:
            out_datetime += timedelta(days=1)
        
        # Calculer la différence
        duration_seconds = (out_datetime - in_datetime).total_seconds()
        duration_hours = Decimal(str(duration_seconds / 3600))
        
        # Arrondir à 2 décimales
        return duration_hours.quantize(Decimal('0.01'))
    
    @classmethod
    def calculate_worked_hours(cls, in_time, out_time):
        """
        Calcule les heures travaillées avec pause déduite et plafonnement.
        
        Règles:
        1. Calcul durée brute: sortie - entrée
        2. Déduire pause fixe: durée - 1h
        3. Plafonner à 8h: min(résultat, 8h)
        
        Args:
            in_time (time): Heure d'entrée
            out_time (time): Heure de sortie
            
        Returns:
            Decimal: Heures travaillées (2 décimales), plafonné à 8h
            
        Exemples:
            >>> calculate_worked_hours(time(9,0), time(17,0))
            Decimal('7.00')  # 8h - 1h = 7h
            
            >>> calculate_worked_hours(time(8,0), time(18,0))
            Decimal('8.00')  # 10h - 1h = 9h → plafonné à 8h
            
            >>> calculate_worked_hours(time(9,0), time(12,0))
            Decimal('2.00')  # 3h - 1h = 2h
        """
        # Durée brute
        duration = cls.calculate_duration_hours(in_time, out_time)
        
        # Déduire la pause
        worked = duration - cls.PAUSE_DURATION_HOURS
        
        # Éviter les valeurs négatives
        if worked < Decimal('0.00'):
            worked = Decimal('0.00')
        
        # Plafonner à 8h
        if worked > cls.MAX_DAILY_HOURS:
            worked = cls.MAX_DAILY_HOURS
        
        return worked.quantize(Decimal('0.01'))
    
    @staticmethod
    def validate_punch_sequence(employee, date, punch_type):
        """
        Valide qu'un pointage respecte la séquence IN → OUT → IN.
        
        Règle: Ne peut pas pointer SORTIE sans avoir pointé ENTRÉE.
        
        Args:
            employee (User): L'employé
            date (date): Date du pointage
            punch_type (str): Type de pointage ('in' ou 'out')
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
            
        Exemples:
            - Premier pointage du jour DOIT être 'in'
            - Si dernier pointage était 'in', prochain doit être 'out'
            - Si dernier pointage était 'out', prochain doit être 'in'
        """
        # Dernier pointage du jour
        last_punch = Attendance.objects.filter(
            employee=employee,
            date=date
        ).order_by('-time').first()
        
        # Premier pointage du jour
        if not last_punch:
            if punch_type == 'out':
                return False, "Impossible de pointer SORTIE sans avoir pointé ENTRÉE"
            return True, None
        
        # Vérifier la séquence
        if last_punch.punch_type == punch_type:
            if punch_type == 'in':
                return False, "Vous avez déjà pointé une ENTRÉE. Veuillez pointer la SORTIE."
            else:
                return False, "Vous avez déjà pointé une SORTIE. Veuillez pointer l'ENTRÉE (nouveau jour)."
        
        return True, None
    
    @classmethod
    def update_worked_hours_on_punch_out(cls, attendance_out):
        """
        Met à jour les heures travaillées quand l'employé pointe la sortie.
        
        Processus:
        1. Trouver le pointage d'entrée correspondant
        2. Calculer les heures travaillées
        3. Mettre à jour le champ worked_hours du pointage de sortie
        
        Args:
            attendance_out (Attendance): Pointage de sortie
            
        Returns:
            Decimal or None: Heures calculées, ou None si pas d'entrée trouvée
        """
        if attendance_out.punch_type != 'out':
            return None
        
        # Trouver l'entrée correspondante (même jour, type 'in')
        attendance_in = Attendance.objects.filter(
            employee=attendance_out.employee,
            date=attendance_out.date,
            punch_type='in'
        ).first()
        
        if not attendance_in:
            # Pas d'entrée trouvée → anomalie
            attendance_out.worked_hours = None
            attendance_out.save()
            
            # Créer anomalie
            AttendanceAnomaly.objects.get_or_create(
                attendance=attendance_out,
                anomaly_type='missing_punch_in',
                defaults={
                    'description': f"Sortie pointée sans entrée correspondante le {attendance_out.date}",
                    'status': 'pending'
                }
            )
            return None
        
        # Calculer les heures
        worked_hours = cls.calculate_worked_hours(
            attendance_in.time,
            attendance_out.time
        )
        
        # Mettre à jour le pointage de sortie
        attendance_out.worked_hours = worked_hours
        attendance_out.save()
        
        # Aussi mettre à jour l'entrée (pour cohérence)
        attendance_in.worked_hours = worked_hours
        attendance_in.save()
        
        return worked_hours
    
    @staticmethod
    def detect_missing_punch_outs(target_date=None):
        """
        Détecte les entrées sans sortie pour une date donnée.
        
        À exécuter chaque jour pour détecter les oublis de sortie de la veille.
        
        Args:
            target_date (date): Date à vérifier (défaut: hier)
            
        Returns:
            list: Liste des anomalies créées
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        # Trouver toutes les entrées sans sortie correspondante
        entries_without_exit = Attendance.objects.filter(
            date=target_date,
            punch_type='in'
        ).exclude(
            employee__in=Attendance.objects.filter(
                date=target_date,
                punch_type='out'
            ).values_list('employee', flat=True)
        )
        
        anomalies_created = []
        
        for entry in entries_without_exit:
            # Mettre worked_hours à NULL
            entry.worked_hours = None
            entry.save()
            
            # Créer ou récupérer l'anomalie
            anomaly, created = AttendanceAnomaly.objects.get_or_create(
                attendance=entry,
                anomaly_type='missing_punch_out',
                defaults={
                    'description': f"Oubli de pointer la sortie le {entry.date}. Contactez votre manager pour correction.",
                    'status': 'pending'
                }
            )
            
            if created:
                anomalies_created.append(anomaly)
        
        return anomalies_created
    
    @classmethod
    def calculate_period_total_hours(cls, employee, start_date, end_date):
        """
        Calcule le total des heures travaillées sur une période.
        
        Args:
            employee (User): L'employé
            start_date (date): Date de début
            end_date (date): Date de fin
            
        Returns:
            dict: {
                'total_hours': Decimal,
                'days_with_hours': int,
                'days_with_null': int (oublis de sortie),
                'average_hours_per_day': Decimal
            }
        """
        # Récupérer tous les pointages de sortie avec worked_hours
        attendances = Attendance.objects.filter(
            employee=employee,
            date__range=(start_date, end_date),
            punch_type='out'
        )
        
        total_hours = Decimal('0.00')
        days_with_hours = 0
        days_with_null = 0
        
        for att in attendances:
            if att.worked_hours is not None:
                total_hours += att.worked_hours
                days_with_hours += 1
            else:
                days_with_null += 1
        
        # Moyenne
        if days_with_hours > 0:
            average = (total_hours / days_with_hours).quantize(Decimal('0.01'))
        else:
            average = Decimal('0.00')
        
        return {
            'total_hours': total_hours,
            'days_with_hours': days_with_hours,
            'days_with_null': days_with_null,
            'average_hours_per_day': average
        }
