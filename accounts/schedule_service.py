"""
Service pour la gestion des profils horaires et leur affectation aux employés.

Fonctionnalités :
- Récupération du profil horaire valide à une date donnée (historique)
- Changement de profil horaire d'un employé (avec historisation)
- Création de profils par défaut
"""

from datetime import date, datetime
from django.db.models import Q
from django.utils import timezone
from accounts.models import WorkSchedule, EmployeeProfile, EmployeeScheduleHistory


class WorkScheduleService:
    """
    Service pour gérer les profils horaires et leur affectation.
    
    PRINCIPE D'IMMUABILITÉ :
    - Les données passées ne sont JAMAIS modifiées
    - Chaque changement crée une nouvelle entrée d'historique
    - Les paies des mois précédents utilisent toujours les bons profils
    """
    
    @staticmethod
    def get_schedule_for_date(employee, target_date=None):
        """
        Récupère le profil horaire valide pour un employé à une date donnée.
        
        Cette méthode est CRUCIALE pour l'immuabilité des paies :
        - Paie de Mars → utilise le profil actif en Mars
        - Paie d'Octobre → utilise le profil actif en Octobre
        - Même si le profil a changé entre-temps
        
        Args:
            employee (EmployeeProfile): L'employé
            target_date (date, optional): Date ciblée. Si None, utilise aujourd'hui.
            
        Returns:
            WorkSchedule: Le profil horaire valide à cette date
            
        Raises:
            ValueError: Si aucun profil n'est trouvé pour cette date
            
        Exemples:
            >>> # Jean avait profil "Matin" en Mars
            >>> get_schedule_for_date(jean, date(2025, 3, 15))
            <WorkSchedule: Matin (07:00-15:00)>
            
            >>> # Jean a maintenant profil "Bureau"  
            >>> get_schedule_for_date(jean)
            <WorkSchedule: Bureau (08:00-18:00)>
        """
        if target_date is None:
            target_date = timezone.now().date()
        
        try:
            # Recherche dans l'historique
            history = EmployeeScheduleHistory.objects.filter(
                employee=employee,
                assigned_date__lte=target_date
            ).filter(
                Q(end_date__gte=target_date) | Q(end_date__isnull=True)
            ).first()
            
            if history:
                return history.work_schedule
            else:
                raise EmployeeScheduleHistory.DoesNotExist
        except EmployeeScheduleHistory.DoesNotExist:
            # Fallback : utiliser le profil actuel si pas d'historique
            if employee.current_work_schedule:
                return employee.current_work_schedule
            else:
                # Dernier recours : profil par défaut
                return WorkSchedule.objects.get(is_default=True)
    
    @staticmethod
    def get_current_schedule(employee):
        """
        Récupère le profil horaire actuellement actif pour un employé.
        
        Raccourci pour get_schedule_for_date(employee, today).
        """
        return WorkScheduleService.get_schedule_for_date(employee)
    
    @staticmethod
    def change_employee_schedule(employee, new_schedule, assigned_by_user, effective_date=None):
        """
        Change le profil horaire d'un employé avec historisation automatique.
        
        PROCESSUS :
        1. Ferme l'ancien historique (end_date = aujourd'hui)
        2. Crée un nouveau historique (start_date = aujourd'hui)
        3. Met à jour le profil actuel de l'employé
        
        Cette méthode garantit l'immuabilité des données passées.
        
        Args:
            employee (EmployeeProfile): L'employé
            new_schedule (WorkSchedule): Le nouveau profil horaire
            assigned_by_user (User): Utilisateur RH qui fait le changement
            effective_date (date, optional): Date effective du changement. Si None, utilise aujourd'hui.
            
        Returns:
            EmployeeScheduleHistory: La nouvelle entrée d'historique créée
            
        Exemple:
            >>> # RH change Jean du profil Matin → Bureau
            >>> change_employee_schedule(
            ...     jean, 
            ...     profil_bureau, 
            ...     rh_marie
            ... )
            <EmployeeScheduleHistory: Jean - Bureau (actif)>
        """
        if effective_date is None:
            effective_date = timezone.now().date()
        
        # 1. Fermer l'ancien historique actif (si existe)
        EmployeeScheduleHistory.objects.filter(
            employee=employee,
            end_date__isnull=True
        ).update(end_date=effective_date)
        
        # 2. Créer le nouvel historique
        new_history = EmployeeScheduleHistory.objects.create(
            employee=employee,
            work_schedule=new_schedule,
            assigned_date=effective_date,
            assigned_by=assigned_by_user
        )
        
        # 3. Mettre à jour le profil actuel (dénormalisation pour performance)
        employee.current_work_schedule = new_schedule
        employee.save(update_fields=['current_work_schedule', 'updated_at'])
        
        return new_history
    
    @staticmethod
    def get_employee_schedule_history(employee, limit=None):
        """
        Récupère l'historique complet des affectations de profils pour un employé.
        
        Utile pour :
        - Audit trail
        - Affichage dans l'interface RH
        - Vérification des changements passés
        
        Args:
            employee (EmployeeProfile): L'employé
            limit (int, optional): Nombre maximum d'entrées à retourner
            
        Returns:
            QuerySet[EmployeeScheduleHistory]: Historique ordonné par date (plus récent en premier)
        """
        queryset = EmployeeScheduleHistory.objects.filter(
            employee=employee
        ).select_related('work_schedule', 'assigned_by').order_by('-assigned_date')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def get_employees_by_schedule(schedule, active_only=True):
        """
        Récupère tous les employés actuellement sur un profil horaire donné.
        
        Args:
            schedule (WorkSchedule): Le profil horaire
            active_only (bool): Si True, retourne uniquement les employés actifs
            
        Returns:
            QuerySet[EmployeeProfile]: Liste des employés
        """
        queryset = EmployeeProfile.objects.filter(current_work_schedule=schedule)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        return queryset.select_related('user', 'department')
    
    @staticmethod
    def create_schedule(name, start_time, end_time, pause_start, pause_end, 
                       description='', created_by=None, is_default=False):
        """
        Crée un nouveau profil horaire.
        
        Args:
            name (str): Nom du profil
            start_time (time): Heure de début contractuelle
            end_time (time): Heure de fin contractuelle
            pause_start (time): Début de pause
            pause_end (time): Fin de pause
            description (str, optional): Description du profil
            created_by (User, optional): Utilisateur qui crée le profil
            is_default (bool): Si True, ce sera le profil par défaut
            
        Returns:
            WorkSchedule: Le profil créé
        """
        schedule = WorkSchedule.objects.create(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            pause_start=pause_start,
            pause_end=pause_end,
            is_default=is_default,
            created_by=created_by
        )
        
        return schedule
    
    @staticmethod
    def get_default_schedule():
        """
        Récupère le profil horaire par défaut.
        
        Returns:
            WorkSchedule: Le profil par défaut
            
        Raises:
            WorkSchedule.DoesNotExist: Si aucun profil par défaut n'existe
        """
        return WorkSchedule.objects.get(is_default=True)
    
    @staticmethod
    def can_delete_schedule(schedule):
        """
        Vérifie si un profil horaire peut être supprimé.
        
        Un profil ne peut être supprimé si :
        - Des employés l'utilisent actuellement
        - Il apparaît dans l'historique (PROTECT foreign key)
        
        Args:
            schedule (WorkSchedule): Le profil à vérifier
            
        Returns:
            tuple: (bool, str) - (peut_supprimer, raison si non)
        """
        # Vérifier les employés actuels
        employee_count = schedule.employees.filter(is_active=True).count()
        if employee_count > 0:
            return False, f"{employee_count} employé(s) utilisent actuellement ce profil"
        
        # Vérifier l'historique
        history_count = schedule.history_entries.count()
        if history_count > 0:
            return False, f"Ce profil apparaît dans {history_count} enregistrement(s) d'historique"
        
        return True, ""
