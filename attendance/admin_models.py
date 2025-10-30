"""
Modèles pour la configuration système du pointage.

Ce module contient les paramètres configurables pour :
- Zones géographiques autorisées (GPS)
- Précision GPS requise
- Rayon autorisé pour le pointage

Note: Les horaires de travail sont gérés par le RH via WorkSchedule (Profils Horaires).
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class CompanySettings(models.Model):
    """
    Configuration globale de l'entreprise pour le système de pointage.
    Une seule instance existe (singleton).
    
    Note: Les horaires de travail sont gérés par le RH via WorkSchedule (Profils Horaires).
    """
    
    # Géolocalisation
    gps_required = models.BooleanField(
        default=True,
        verbose_name="GPS obligatoire",
        help_text="Si activé, la géolocalisation est obligatoire pour pointer"
    )
    
    site_center_latitude = models.FloatField(
        default=6.140766,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name="Latitude du bureau",
        help_text="Coordonnée GPS latitude du bureau principal (ex: 6.140766)"
    )
    
    site_center_longitude = models.FloatField(
        default=1.241907,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        verbose_name="Longitude du bureau",
        help_text="Coordonnée GPS longitude du bureau principal (ex: 1.241907)"
    )
    
    allowed_radius_meters = models.IntegerField(
        default=200,
        validators=[MinValueValidator(10), MaxValueValidator(5000)],
        verbose_name="Rayon autorisé (mètres)",
        help_text="Distance maximale autorisée du bureau pour pointer (ex: 200m)"
    )
    
    gps_accuracy_max_meters = models.IntegerField(
        default=200,
        validators=[MinValueValidator(10), MaxValueValidator(500)],
        verbose_name="Précision GPS maximale (mètres)",
        help_text="Précision GPS maximale acceptée (ex: 200m)"
    )
    
    # Métadonnées
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )
    
    updated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Modifié par"
    )
    
    class Meta:
        verbose_name = "Configuration Entreprise"
        verbose_name_plural = "Configuration Entreprise"
    
    def __str__(self):
        return "Configuration GPS"
    
    def save(self, *args, **kwargs):
        """Assure qu'une seule instance existe (singleton)."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Empêche la suppression."""
        pass
    
    @classmethod
    def load(cls):
        """Charge ou crée la configuration."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj



