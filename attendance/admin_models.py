"""
Modèles pour la configuration système du pointage.

Ce module contient les paramètres configurables pour :
- Horaires de travail
- Zones géographiques autorisées
- Règles de pointage
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class CompanySettings(models.Model):
    """
    Configuration globale de l'entreprise pour le système de pointage.
    Une seule instance existe (singleton).
    """
    
    # Informations entreprise
    company_name = models.CharField(
        max_length=200,
        default="Mon Entreprise",
        verbose_name="Nom de l'entreprise"
    )
    
    # Horaires de travail
    work_start_time = models.TimeField(
        default='08:00',
        verbose_name="Heure de début",
        help_text="Heure d'arrivée attendue (ex: 08:00)"
    )
    
    work_end_time = models.TimeField(
        default='17:00',
        verbose_name="Heure de fin",
        help_text="Heure de sortie attendue (ex: 17:00)"
    )
    
    late_tolerance_minutes = models.IntegerField(
        default=15,
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        verbose_name="Tolérance retard (minutes)",
        help_text="Nombre de minutes de tolérance avant qu'un retard soit enregistré"
    )
    
    # Géolocalisation
    gps_required = models.BooleanField(
        default=True,
        verbose_name="GPS obligatoire",
        help_text="Si activé, la géolocalisation est obligatoire pour pointer"
    )
    
    site_center_latitude = models.FloatField(
        default=6.1304,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name="Latitude du bureau",
        help_text="Coordonnée GPS latitude du bureau principal (ex: 6.1304 pour Lomé)"
    )
    
    site_center_longitude = models.FloatField(
        default=1.2158,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        verbose_name="Longitude du bureau",
        help_text="Coordonnée GPS longitude du bureau principal (ex: 1.2158 pour Lomé)"
    )
    
    allowed_radius_meters = models.IntegerField(
        default=200,
        validators=[MinValueValidator(10), MaxValueValidator(5000)],
        verbose_name="Rayon autorisé (mètres)",
        help_text="Distance maximale autorisée du bureau pour pointer (ex: 200m)"
    )
    
    gps_accuracy_max_meters = models.IntegerField(
        default=50,
        validators=[MinValueValidator(10), MaxValueValidator(200)],
        verbose_name="Précision GPS minimale (mètres)",
        help_text="Précision GPS minimale acceptée (ex: 50m)"
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
        return f"Configuration {self.company_name}"
    
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



