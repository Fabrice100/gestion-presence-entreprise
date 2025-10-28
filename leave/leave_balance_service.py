"""
Service de gestion des soldes de congés.

Ce module contient la logique métier pour :
- Initialisation des soldes (30 jours au Togo)
- Calcul des soldes restants
- Gestion des reports de congés
- Validation des demandes

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from .models import LeaveBalance, LeaveType, LeaveRequest, Holiday
from common.structured_logging import structured_logger


class LeaveBalanceService:
    """
    Service centralisé pour la gestion des soldes de congés.
    """
    
    # Configuration Togo
    DEFAULT_ANNUAL_LEAVE_DAYS = 30  # 30 jours au Togo
    MAX_CARRY_OVER_DAYS = 5  # Maximum 5 jours reportables
    CARRY_OVER_DEADLINE_MONTH = 3  # Report possible jusqu'en mars
    
    def __init__(self):
        self.logger = structured_logger.attendance_logger
    
    def initialize_employee_balance(self, user: User, year: int = None) -> Dict[str, any]:
        """
        Initialise le solde de congés d'un employé pour une année.
        
        Args:
            user: Utilisateur Django
            year: Année (défaut: année courante)
            
        Returns:
            Dict avec les soldes créés
        """
        if year is None:
            year = timezone.now().year
            
        try:
            # Récupérer le type de congé "Congés payés" ou "Congé annuel"
            annual_leave_type = LeaveType.objects.get(
                name__in=["Congés payés", "Congé Annuel"],
                is_active=True
            )
        except LeaveType.DoesNotExist:
            # Créer le type de congé annuel s'il n'existe pas
            annual_leave_type = LeaveType.objects.create(
                name="Congé Annuel",
                allocation_amount=self.DEFAULT_ANNUAL_LEAVE_DAYS,
                is_paid=True,
                is_active=True,
                color="#28a745"
            )
            self.logger.info(
                "Type de congé annuel créé",
                leave_type_id=annual_leave_type.id,
                max_days=self.DEFAULT_ANNUAL_LEAVE_DAYS,
                event_type="leave_type_created"
            )
        
        # Vérifier si le solde existe déjà
        balance, created = LeaveBalance.objects.get_or_create(
            employee=user,
            leave_type=annual_leave_type,
            year=year,
            defaults={
                'allocated_balance': self.DEFAULT_ANNUAL_LEAVE_DAYS,
                'taken_balance': 0,
                'carried_over_balance': 0
            }
        )
        
        if created:
            self.logger.info(
                "Solde de congés initialisé",
                user_id=user.id,
                year=year,
                allocated_days=self.DEFAULT_ANNUAL_LEAVE_DAYS,
                event_type="leave_balance_initialized"
            )
        else:
            # Mettre à jour si nécessaire
            if balance.allocated_balance != self.DEFAULT_ANNUAL_LEAVE_DAYS:
                balance.allocated_balance = self.DEFAULT_ANNUAL_LEAVE_DAYS
                balance.save()
                self.logger.info(
                    "Solde de congés mis à jour",
                    user_id=user.id,
                    year=year,
                    new_allocated_days=self.DEFAULT_ANNUAL_LEAVE_DAYS,
                    event_type="leave_balance_updated"
                )
        
        return {
            'balance': balance,
            'created': created,
            'remaining_days': balance.allocated_balance + balance.carried_over_balance - balance.taken_balance
        }
    
    def get_remaining_balance(self, user: User, year: int = None, leave_type_id: int = None) -> Decimal:
        """
        Calcule le solde restant d'un employé.
        
        Args:
            user: Utilisateur Django
            year: Année (défaut: année courante)
            leave_type_id: ID du type de congé (défaut: congé annuel)
            
        Returns:
            Nombre de jours restants
        """
        if year is None:
            year = timezone.now().year
            
        try:
            if leave_type_id:
                balance = LeaveBalance.objects.get(
                    employee=user,
                    leave_type_id=leave_type_id,
                    year=year
                )
            else:
                # Récupérer le congé annuel par défaut
                annual_leave_type = LeaveType.objects.get(
                    name__icontains="annuel",
                    is_active=True
                )
                balance = LeaveBalance.objects.get(
                    employee=user,
                    leave_type=annual_leave_type,
                    year=year
                )
            
            remaining = balance.allocated_balance + balance.carried_over_balance - balance.taken_balance
            return max(Decimal('0'), remaining)
            
        except (LeaveBalance.DoesNotExist, LeaveType.DoesNotExist):
            # Initialiser le solde si nécessaire
            result = self.initialize_employee_balance(user, year)
            return result['remaining_days']
    
    def can_take_leave(self, user: User, start_date: date, end_date: date, 
                      leave_type_id: int = None) -> Tuple[bool, str]:
        """
        Vérifie si un employé peut prendre des congés.
        
        Args:
            user: Utilisateur Django
            start_date: Date de début
            end_date: Date de fin
            leave_type_id: ID du type de congé
            
        Returns:
            Tuple (peut_prendre, message)
        """
        # Calculer la durée
        duration = (end_date - start_date).days + 1
        
        # Vérifier le solde
        remaining = self.get_remaining_balance(user, leave_type_id=leave_type_id)
        if remaining < duration:
            return False, f"Solde insuffisant. Restant: {remaining} jours, demandé: {duration} jours"
        
        # Vérifier les conflits
        conflicts = LeaveRequest.objects.filter(
            employee=user,
            status__in=['pending', 'approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exclude(leave_type_id=leave_type_id)
        
        if conflicts.exists():
            return False, "Conflit avec une autre demande de congé"
        
        # Vérifier les jours fériés
        holidays = self.get_holidays_in_period(start_date, end_date)
        if holidays:
            return False, f"Période contient des jours fériés: {', '.join(holidays)}"
        
        return True, "Demande valide"
    
    def get_holidays_in_period(self, start_date: date, end_date: date) -> List[str]:
        """
        Récupère les jours fériés dans une période.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Liste des noms des jours fériés
        """
        holidays = Holiday.objects.filter(
            date__range=[start_date, end_date],
            is_active=True
        ).values_list('name', flat=True)
        
        return list(holidays)
    
    def update_balance_after_approval(self, leave_request: LeaveRequest) -> bool:
        """
        Met à jour le solde UNIQUE après approbation d'une demande.
        
        IMPORTANT : Tous les congés payés déduisent du MÊME solde de 30 jours.
        
        Args:
            leave_request: Demande de congé approuvée
            
        Returns:
            True si mis à jour avec succès
        """
        # Vérifier si ce type déduit du solde
        if not leave_request.leave_type.deducts_balance:
            # Congé sans solde : ne rien faire
            return True
        
        try:
            # Récupérer le type "Congés payés" comme solde unique
            from leave.models import LeaveType
            conges_payes_type = LeaveType.objects.filter(name__icontains='payé').first()
            
            if not conges_payes_type:
                self.logger.error(
                    "Type 'Congés payés' non trouvé",
                    event_type="leave_type_not_found"
                )
                return False
            
            # TOUJOURS utiliser le solde "Congés payés" (solde unique de 30j)
            balance = LeaveBalance.objects.get(
                employee=leave_request.employee,
                leave_type=conges_payes_type,  # Solde unique
                year=leave_request.start_date.year
            )
            
            # Ajouter les jours pris
            balance.taken_balance += leave_request.duration_days
            balance.save()
            
            self.logger.info(
                "Solde mis à jour après approbation",
                user_id=leave_request.employee.id,
                leave_request_id=leave_request.id,
                days_taken=leave_request.duration_days,
                remaining_days=self.get_remaining_balance(leave_request.employee),
                event_type="leave_balance_updated_after_approval"
            )
            
            return True
            
        except LeaveBalance.DoesNotExist:
            self.logger.error(
                "Solde non trouvé pour mise à jour",
                user_id=leave_request.employee.id,
                year=leave_request.start_date.year,
                event_type="leave_balance_not_found"
            )
            return False
    
    def process_carry_over(self, user: User, from_year: int, to_year: int) -> Dict[str, any]:
        """
        Traite le report de congés d'une année à l'autre.
        
        Args:
            user: Utilisateur Django
            from_year: Année source
            to_year: Année destination
            
        Returns:
            Dict avec le résultat du report
        """
        try:
            # Récupérer le solde de l'année précédente
            old_balance = LeaveBalance.objects.get(
                employee=user,
                leave_type__name__icontains="annuel",
                year=from_year
            )
            
            # Calculer les jours reportables
            remaining = old_balance.allocated_balance + old_balance.carried_over_balance - old_balance.taken_balance
            carry_over_days = min(remaining, self.MAX_CARRY_OVER_DAYS)
            
            if carry_over_days <= 0:
                return {
                    'success': False,
                    'message': 'Aucun jour à reporter',
                    'carry_over_days': 0
                }
            
            # Initialiser le solde de la nouvelle année
            new_balance_result = self.initialize_employee_balance(user, to_year)
            new_balance = new_balance_result['balance']
            
            # Ajouter les jours reportés
            new_balance.carried_over_balance = carry_over_days
            new_balance.save()
            
            self.logger.info(
                "Report de congés effectué",
                user_id=user.id,
                from_year=from_year,
                to_year=to_year,
                carry_over_days=carry_over_days,
                event_type="leave_carry_over_processed"
            )
            
            return {
                'success': True,
                'message': f'{carry_over_days} jours reportés avec succès',
                'carry_over_days': carry_over_days,
                'new_remaining': self.get_remaining_balance(user, to_year)
            }
            
        except LeaveBalance.DoesNotExist:
            return {
                'success': False,
                'message': 'Solde de l\'année précédente non trouvé',
                'carry_over_days': 0
            }
    
    def get_employee_leave_summary(self, user: User, year: int = None) -> Dict[str, any]:
        """
        Récupère un résumé des congés d'un employé.
        
        Args:
            user: Utilisateur Django
            year: Année (défaut: année courante)
            
        Returns:
            Dict avec le résumé complet
        """
        if year is None:
            year = timezone.now().year
        
        # Initialiser le solde si nécessaire
        self.initialize_employee_balance(user, year)
        
        # Récupérer tous les soldes de l'année
        balances = LeaveBalance.objects.filter(
            employee=user,
            year=year
        ).select_related('leave_type')
        
        # Récupérer les demandes de l'année
        requests = LeaveRequest.objects.filter(
            employee=user,
            start_date__year=year
        ).select_related('leave_type').order_by('-created_at')
        
        # Calculer les statistiques
        total_allocated = sum(b.allocated_balance + b.carried_over_balance for b in balances)
        total_taken = sum(b.taken_balance for b in balances)
        total_remaining = total_allocated - total_taken
        
        return {
            'year': year,
            'balances': [
                {
                    'leave_type': balance.leave_type.name,
                    'allocated': float(balance.allocated_balance),
                    'taken': float(balance.taken_balance),
                    'carried_over': float(balance.carried_over_balance),
                    'remaining': float(self.get_remaining_balance(user, year, balance.leave_type.id))
                }
                for balance in balances
            ],
            'summary': {
                'total_allocated': float(total_allocated),
                'total_taken': float(total_taken),
                'total_remaining': float(total_remaining)
            },
            'requests': [
                {
                    'id': req.id,
                    'leave_type': req.leave_type.name,
                    'start_date': req.start_date,
                    'end_date': req.end_date,
                    'duration': float(req.duration_days),
                    'status': req.status,
                    'created_at': req.created_at
                }
                for req in requests
            ]
        }


# Instance globale du service
leave_balance_service = LeaveBalanceService()
