"""
Modèles pour la gestion des heures supplémentaires.

Ce module contient les modèles Django pour :
- OvertimeConfiguration : Configuration des règles d'heures supplémentaires
- OvertimeRecord : Enregistrement des heures supplémentaires calculées automatiquement

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
    
    # Heures spécifiques pour les HS de nuit
    night_start_hour = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Heure de début nuit",
        help_text="Heure de début des heures de nuit (ex: 22:00)"
    )
    
    night_end_hour = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Heure de fin nuit",
        help_text="Heure de fin des heures de nuit (ex: 06:00)"
    )
    
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
        verbose_name = "Configuration Heures Supplémentaires"
        verbose_name_plural = "Configurations Heures Supplémentaires"
        ordering = ['config_type', 'name']
    
    def __str__(self):
        """Représentation string de la configuration."""
        return f"{self.name} ({self.get_config_type_display()})"


class OvertimeRecord(models.Model):
    """
    Enregistrement des heures supplémentaires calculées automatiquement.
    
    Les heures supplémentaires sont détectées automatiquement à partir
    des pointages et doivent être validées par la hiérarchie.
    """
    
    # Choix pour les types d'heures supplémentaires
    OVERTIME_TYPE_CHOICES = [
        ('daily', 'Quotidiennes'),
        ('weekly', 'Hebdomadaires'),
        ('weekend', 'Weekend'),
        ('holiday', 'Jours fériés'),
        ('night', 'Heures de nuit'),
    ]
    
    # Choix pour les statuts
    STATUS_CHOICES = [
        ('detected', 'Détectées'),
        ('pending_approval', 'En attente validation'),
        ('approved', 'Validées'),
        ('rejected', 'Rejetées'),
        ('disputed', 'Contestées'),
    ]
    
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='overtime_records',
        verbose_name="Employé",
        help_text="Employé concerné par les heures supplémentaires"
    )
    
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_overtime_records',
        verbose_name="Manager",
        help_text="Manager responsable de la validation"
    )
    
    # Référence aux pointages
    attendance_records = models.ManyToManyField(
        'Attendance',
        related_name='overtime_records',
        verbose_name="Pointages concernés",
        help_text="Pointages ayant généré ces heures supplémentaires"
    )
    
    overtime_type = models.CharField(
        max_length=20,
        choices=OVERTIME_TYPE_CHOICES,
        verbose_name="Type d'heures supplémentaires",
        help_text="Type d'heures supplémentaires détectées"
    )
    
    date = models.DateField(
        verbose_name="Date",
        help_text="Date des heures supplémentaires"
    )
    
    # Heures calculées automatiquement
    normal_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Heures normales",
        help_text="Nombre d'heures normales travaillées"
    )
    
    overtime_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="Heures supplémentaires",
        help_text="Nombre d'heures supplémentaires détectées"
    )
    
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Total heures",
        help_text="Total des heures travaillées"
    )
    
    # Workflow de validation
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
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='detected',
        verbose_name="Statut global"
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
        verbose_name = "Enregistrement Heures Supplémentaires"
        verbose_name_plural = "Enregistrements Heures Supplémentaires"
        ordering = ['-date', '-created_at']
        unique_together = ['employee', 'date', 'overtime_type']
    
    def __str__(self):
        """Représentation string de l'enregistrement."""
        return f"HS {self.get_overtime_type_display()} - {self.employee.get_full_name()} le {self.date} ({self.overtime_hours}h)"
    
    def save(self, *args, **kwargs):
        """
        Override de la méthode save pour mettre à jour le statut global.
        """
        # Mettre à jour le statut global basé sur les décisions
        if self.rh_decision == 'rejected' or self.manager_decision == 'rejected':
            self.status = 'rejected'
        elif self.rh_decision == 'approved' and self.manager_decision == 'approved':
            self.status = 'approved'
        elif self.manager_decision == 'approved' and not self.rh_decision:
            self.status = 'pending_approval'  # En attente RH
        elif self.manager_decision == 'detected' or not self.manager_decision:
            self.status = 'detected'  # Détectées, en attente manager
        
        super().save(*args, **kwargs)
    
    def is_weekend(self):
        """Vérifie si la date est un weekend."""
        return self.date.weekday() >= 5  # Samedi = 5, Dimanche = 6
    
    def is_holiday(self):
        """Vérifie si la date est un jour férié."""
        # TODO: Implémenter la vérification des jours fériés
        # from leave.models import Holiday
        # return Holiday.objects.filter(date=self.date, is_active=True).exists()
        return False
    
    def is_night_shift(self):
        """Vérifie si les heures supplémentaires sont de nuit."""
        if not self.overtime_type == 'night':
            return False
        
        # Vérifier si les heures se chevauchent avec la période de nuit
        config = OvertimeConfiguration.objects.filter(
            config_type='night',
            is_active=True
        ).first()
        
        if not config or not config.night_start_hour or not config.night_end_hour:
            return False
        
        night_start = config.night_start_hour
        night_end = config.night_end_hour
        
        # Cas simple : période de nuit dans la même journée
        if night_start < night_end:
            # TODO: Récupérer les heures de pointage pour vérifier
            return True
        
        # Cas complexe : période de nuit sur deux jours (ex: 22h-06h)
        return True
    
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