"""
Modèles pour la gestion des congés et absences.

Ce module contient les modèles Django pour :
- LeaveType : Types de congés disponibles
- LeaveRequest : Demandes de congés avec workflow de validation
- LeaveBalance : Soldes de congés par employé

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class LeaveType(models.Model):
    """
    Modèle représentant un type de congé (annuel, maladie, etc.).
    
    Définit les règles et caractéristiques de chaque type de congé.
    """
    
    # Choix pour les unités de calcul
    UNIT_CHOICES = [
        ('days', 'Jours'),
        ('hours', 'Heures'),
    ]
    
    # Choix pour les types d'attribution
    ALLOCATION_CHOICES = [
        ('annual', 'Annuelle'),
        ('monthly', 'Mensuelle'),
        ('on_demand', 'Sur demande'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du type",
        help_text="Nom du type de congé (ex: Congés payés, Maladie)"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description du type de congé"
    )
    
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code",
        help_text="Code court pour identifier le type (ex: CP, MAL)"
    )
    
    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='days',
        verbose_name="Unité",
        help_text="Unité de calcul (jours ou heures)"
    )
    
    allocation_type = models.CharField(
        max_length=20,
        choices=ALLOCATION_CHOICES,
        default='annual',
        verbose_name="Type d'attribution",
        help_text="Comment les congés sont attribués"
    )
    
    allocation_amount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Montant d'attribution",
        help_text="Quantité attribuée (ex: 25 jours par an)"
    )
    
    max_consecutive_days = models.PositiveIntegerField(
        default=30,
        verbose_name="Maximum consécutif",
        help_text="Nombre maximum de jours consécutifs autorisés"
    )
    
    requires_justification = models.BooleanField(
        default=False,
        verbose_name="Justification requise",
        help_text="Une justification est-elle requise ?"
    )
    
    requires_medical_certificate = models.BooleanField(
        default=False,
        verbose_name="Certificat médical",
        help_text="Un certificat médical est-il requis ?"
    )
    
    advance_notice_days = models.PositiveIntegerField(
        default=0,
        verbose_name="Préavis (jours)",
        help_text="Nombre de jours d'avance requis"
    )
    
    is_paid = models.BooleanField(
        default=True,
        verbose_name="Rémunéré",
        help_text="Le congé est-il rémunéré ?"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Type de congé disponible"
    )
    
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name="Couleur",
        help_text="Couleur hexadécimale pour l'affichage"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Type de congé"
        verbose_name_plural = "Types de congés"
        ordering = ['name']
    
    def __str__(self):
        """Représentation string du type de congé."""
        return self.name