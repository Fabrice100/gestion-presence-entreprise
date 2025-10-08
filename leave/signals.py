"""
Signals pour l'application leave.

Ce module contient les signaux Django pour :
- Création automatique des soldes de congés lors de la création d'un employé
- Mise à jour automatique des soldes

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from datetime import date

from .models import LeaveBalance, LeaveType
from accounts.models import EmployeeProfile


@receiver(post_save, sender=EmployeeProfile)
def create_default_leave_balances(sender, instance, created, **kwargs):
    """
    Crée automatiquement les soldes de congés payés pour un nouvel employé.
    
    Signal déclenché après la création d'un profil d'employé.
    Initialise le solde de congés payés annuels (24 jours - législation togolaise).
    """
    if created:
        # Récupérer le type de congés payés
        try:
            conges_payes = LeaveType.objects.get(code='CP')
            
            # Créer le solde de congés payés pour l'année en cours
            LeaveBalance.objects.get_or_create(
                employee=instance.user,
                leave_type=conges_payes,
                year=date.today().year,
                defaults={
                    'allocated_balance': conges_payes.allocation_amount,
                    'taken_balance': 0,
                    'carried_over_balance': 0
                }
            )
            
            print(f"✓ Solde de congés créé pour {instance.user.username}: {conges_payes.allocation_amount} jours")
            
        except LeaveType.DoesNotExist:
            # Si le type de congés payés n'existe pas encore, on ne fait rien
            # (sera créé lors du chargement des fixtures)
            pass


