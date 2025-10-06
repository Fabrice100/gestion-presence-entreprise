"""
Modèles pour la gestion des heures supplémentaires.

Ce module contient les modèles Django pour :
- OvertimeRequest : Demandes d'heures supplémentaires
- OvertimeConfiguration : Configuration des règles d'heures supplémentaires
- OvertimeCalculation : Calculs automatiques des heures supplémentaires

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import datetime, date, time, timedelta


class OvertimeConfiguration(models.Model):
    """
    Configuration des règles d'heures supplémentaires.
    
    Permet de définir les règles de suivi des heures supplémentaires
    selon les besoins de l'entreprise.
    """
    
    # Choix pour les types de configuration
    CONFIG_TYPE_CHOICES = [
        ('daily', 'Heures quotidiennes'),
        ('weekly', 'Heures hebdomadaires'),
        ('weekend', 'Weekend'),
        ('holiday', 'Jours fériés'),
        ('night', 'Heures de nuit'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de la configuration",
        help_text="Nom descriptif de la règle"
    )
    
    config_type = models.CharField(
        max_length=20,
        choices=CONFIG_TYPE_CHOICES,
        verbose_name="Type de configuration",
        help_text="Type de règle d'heures supplémentaires"
    )
    
    # Règles de déclenchement
    daily_hours_limit = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('8.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Limite d'heures quotidiennes",
        help_text="Nombre d'heures par jour avant déclenchement des heures supplémentaires"
    )
    
    weekly_hours_limit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('40.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Limite d'heures hebdomadaires",
        help_text="Nombre d'heures par semaine avant déclenchement des heures supplémentaires"
    )
    
    # Heures spécifiques
    night_start_hour = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Début des heures de nuit",
        help_text="Heure de début des heures de nuit (ex: 22:00)"
    )
    
    night_end_hour = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Fin des heures de nuit",
        help_text="Heure de fin des heures de nuit (ex: 06:00)"
    )
    
    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Cette configuration est-elle active ?"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Configuration heures supplémentaires"
        verbose_name_plural = "Configurations heures supplémentaires"
        ordering = ['config_type', 'name']
    
    def __str__(self):
        """Représentation string de la configuration."""
        return f"{self.name} ({self.get_config_type_display()})"


class OvertimeRequest(models.Model):
    """
    Demande d'heures supplémentaires par un employé.
    
    Permet aux employés de demander des heures supplémentaires
    avec validation hiérarchique. Focus sur le suivi de présence.
    """
    
    # Choix pour les types d'heures supplémentaires
    OVERTIME_TYPE_CHOICES = [
        ('planned', 'Planifiées'),
        ('unplanned', 'Non planifiées'),
        ('emergency', 'Urgentes'),
        ('project', 'Projet'),
    ]
    
    # Choix pour les statuts
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvées'),
        ('rejected', 'Rejetées'),
        ('cancelled', 'Annulées'),
    ]
    
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='overtime_requests',
        verbose_name="Employé",
        help_text="Employé qui demande les heures supplémentaires"
    )
    
    overtime_type = models.CharField(
        max_length=20,
        choices=OVERTIME_TYPE_CHOICES,
        default='unplanned',
        verbose_name="Type d'heures supplémentaires",
        help_text="Type de demande d'heures supplémentaires"
    )
    
    date = models.DateField(
        verbose_name="Date",
        help_text="Date des heures supplémentaires"
    )
    
    start_time = models.TimeField(
        verbose_name="Heure de début",
        help_text="Heure de début des heures supplémentaires"
    )
    
    end_time = models.TimeField(
        verbose_name="Heure de fin",
        help_text="Heure de fin des heures supplémentaires"
    )
    
    hours_requested = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Heures demandées",
        help_text="Nombre d'heures supplémentaires demandées"
    )
    
    reason = models.TextField(
        verbose_name="Motif",
        help_text="Motif de la demande d'heures supplémentaires"
    )
    
    # Validation
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut",
        help_text="Statut de la demande"
    )
    
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_overtime_requests',
        verbose_name="Manager",
        help_text="Manager responsable de la validation"
    )
    
    manager_decision = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Décision Manager",
        help_text="Décision du manager"
    )
    
    manager_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire Manager",
        help_text="Commentaire du manager"
    )
    
    manager_decision_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Décision Manager le",
        help_text="Date de décision du manager"
    )
    
    rh_decision = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Décision RH",
        help_text="Décision du RH/DG"
    )
    
    rh_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire RH",
        help_text="Commentaire du RH/DG"
    )
    
    rh_decision_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Décision RH le",
        help_text="Date de décision du RH/DG"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Demande d'heures supplémentaires"
        verbose_name_plural = "Demandes d'heures supplémentaires"
        ordering = ['-created_at']
    
    def __str__(self):
        """Représentation string de la demande."""
        return f"{self.employee.get_full_name()} - {self.date} - {self.hours_requested}h"
    
    def save(self, *args, **kwargs):
        """
        Override de la méthode save pour calculer automatiquement les heures.
        """
        # Calculer les heures demandées si pas déjà fait
        if not self.hours_requested and self.start_time and self.end_time:
            self.hours_requested = self.calculate_hours()
        
        # Déterminer le manager si pas déjà défini
        if not self.manager and self.employee.employee_profile.manager:
            self.manager = self.employee.employee_profile.manager
        
        super().save(*args, **kwargs)
    
    def calculate_hours(self):
        """
        Calcule le nombre d'heures entre start_time et end_time.
        """
        if not self.start_time or not self.end_time:
            return Decimal('0.00')
        
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        
        # Gérer le cas où end_time est le lendemain
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        duration = end_dt - start_dt
        hours = duration.total_seconds() / 3600
        
        return Decimal(str(round(hours, 2)))
    
    def is_weekend(self):
        """Vérifie si la date est un weekend."""
        return self.date.weekday() >= 5  # Samedi = 5, Dimanche = 6
    
    def is_holiday(self):
        """Vérifie si la date est un jour férié."""
        from leave.models import Holiday
        return Holiday.objects.filter(date=self.date, is_active=True).exists()
    
    def is_night_shift(self):
        """Vérifie si les heures sont en période de nuit."""
        config = OvertimeConfiguration.objects.filter(
            config_type='night',
            is_active=True
        ).first()
        
        if not config or not config.night_start_hour or not config.night_end_hour:
            return False
        
        # Vérifier si les heures chevauchent avec la période de nuit
        night_start = config.night_start_hour
        night_end = config.night_end_hour
        
        # Cas simple : période de nuit dans la même journée
        if night_start < night_end:
            return (self.start_time >= night_start and self.start_time < night_end) or \
                   (self.end_time > night_start and self.end_time <= night_end)
        
        # Cas complexe : période de nuit sur deux jours (ex: 22h-06h)
        return (self.start_time >= night_start) or (self.end_time <= night_end)
    
    def get_overtime_type_display_name(self):
        """
        Retourne le nom du type d'heures supplémentaires selon la période.
        """
        if self.is_holiday():
            return "Jours fériés"
        elif self.is_weekend():
            return "Weekend"
        elif self.is_night_shift():
            return "Heures de nuit"
        else:
            return "Heures quotidiennes"


