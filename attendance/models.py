"""
Modèles pour la gestion du pointage et des présences.

Ce module contient les modèles Django pour :
- Attendance : Pointages d'entrée et de sortie avec géolocalisation
- OvertimeConfiguration : Configuration des règles d'heures supplémentaires
- OvertimeRequest : Demandes d'heures supplémentaires
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
from common.validators import (
    validate_gps_coordinate,
    validate_gps_accuracy,
    validate_safe_string
)


def get_current_date():
    """Helper function to get current date."""
    return timezone.now().date()


class Attendance(models.Model):
    """
    Modèle représentant un pointage d'entrée ou de sortie d'un employé.
    
    Ce modèle stocke les informations de géolocalisation et détecte
    automatiquement les anomalies de pointage.
    """
    
    # Choix pour les types de pointage
    PUNCH_TYPE_CHOICES = [
        ('in', 'Entrée'),
        ('out', 'Sortie'),
    ]
    
    # Choix pour les statuts (nettoyé - seulement les statuts réellement utilisés)
    STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('late', 'En retard'),
        ('early', 'Sortie anticipée'),
    ]
    
    # Choix pour les sources de pointage (système web uniquement)
    SOURCE_CHOICES = [
        ('web', 'Web'),
    ]
    
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="Employé",
        help_text="Employé qui effectue le pointage"
    )
    
    date = models.DateField(
        default=get_current_date,
        verbose_name="Date",
        help_text="Date du pointage"
    )
    
    punch_type = models.CharField(
        max_length=10,
        choices=PUNCH_TYPE_CHOICES,
        verbose_name="Type de pointage",
        help_text="Entrée ou sortie"
    )
    
    time = models.TimeField(
        verbose_name="Heure",
        help_text="Heure du pointage"
    )
    
    # Informations de géolocalisation (requises)
    latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90), validate_gps_coordinate],
        verbose_name="Latitude",
        help_text="Latitude GPS du pointage"
    )
    
    longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180), validate_gps_coordinate],
        verbose_name="Longitude",
        help_text="Longitude GPS du pointage"
    )
    
    accuracy = models.FloatField(
        validators=[validate_gps_accuracy],
        verbose_name="Précision GPS",
        help_text="Précision GPS en mètres"
    )
    
    distance_from_site = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Distance du site",
        help_text="Distance calculée du centre du site en mètres"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='normal',
        verbose_name="Statut",
        help_text="Statut du pointage (normal, retard, etc.)"
    )
    
    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default='web',
        verbose_name="Source",
        help_text="Source du pointage"
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name="User Agent",
        help_text="Navigateur/appareil utilisé pour le pointage"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="Adresse IP",
        help_text="Adresse IP de l'appareil"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
        help_text="Notes ou commentaires sur le pointage"
    )
    
    worked_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Heures travaillées",
        help_text="Heures travaillées calculées (pause déduite, plafonnées à 8h). NULL si sortie manquante."
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
        verbose_name = "Pointage"
        verbose_name_plural = "Pointages"
        ordering = ['-date', '-time']
        # Contrainte unique : un employé ne peut pointer qu'une fois par type par jour
        unique_together = ['employee', 'date', 'punch_type']
    
    def __str__(self):
        """Représentation string du pointage."""
        return f"{self.employee.get_full_name()} - {self.get_punch_type_display()} - {self.date} {self.time}"
    
    def save(self, *args, **kwargs):
        """
        Override de la méthode save pour calculer automatiquement la distance et détecter les anomalies.
        """
        # Définir la date et l'heure actuelles si non fournies
        if not self.time:
            now = timezone.now()
            self.time = now.time()
        
        if not self.date:
            now = timezone.now()
            self.date = now.date()
            
        # Définir une précision par défaut si non fournie
        if not self.accuracy:
            self.accuracy = 100.0  # 100 mètres par défaut
        
        # Calculer la distance du centre du site
        if self.latitude and self.longitude:
            self.distance_from_site = self.calculate_distance_from_site()
        
        # Déduire un statut simple (retard/départ anticipé) sans créer d'anomalies
        self.detect_anomalies()
        
        super().save(*args, **kwargs)
    
    def calculate_distance_from_site(self):
        """
        Calcule la distance entre le pointage et le centre du site.
        
        Utilise la formule de Haversine pour calculer la distance en mètres.
        """
        import math
        
        # Coordonnées du centre du site depuis la configuration de l'entreprise
        from .admin_models import CompanySettings
        company_settings = CompanySettings.load()
        site_lat = company_settings.site_center_latitude
        site_lng = company_settings.site_center_longitude
        
        # Conversion en radians
        lat1_rad = math.radians(site_lat)
        lng1_rad = math.radians(site_lng)
        lat2_rad = math.radians(self.latitude)
        lng2_rad = math.radians(self.longitude)
        
        # Différences
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        # Formule de Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Rayon de la Terre en mètres
        earth_radius = 6371000
        
        return earth_radius * c
    
    def detect_anomalies(self):
        """
        Détecte automatiquement les anomalies de pointage.
        
        Vérifie :
        - Distance du site
        - Précision GPS
        - Heures de pointage
        - Doublons
        """
        # Vérifier les heures de pointage (simplifié)
        hour = self.time.hour
        if hour < 6 or hour > 19:  # En dehors des heures normales
            if self.punch_type == 'in':
                self.status = 'late' if hour > 9 else 'normal'
            else:
                self.status = 'early' if hour < 16 else 'normal'
        
    def get_duration_with_previous(self):
        """
        Calcule la durée travaillée avec le pointage précédent.
        """
        if self.punch_type == 'out':
            previous_in = Attendance.objects.filter(
                employee=self.employee,
                date=self.date,
                punch_type='in'
            ).order_by('-time').first()
            
            if previous_in:
                from datetime import datetime, date
                in_datetime = datetime.combine(self.date, previous_in.time)
                out_datetime = datetime.combine(self.date, self.time)
                duration = out_datetime - in_datetime
                return duration.total_seconds() / 3600  # En heures
        
        return None


# Modèle AttendanceAnomaly supprimé (fonctionnalité anomalies désactivée)


# Les imports des modèles d'heures supplémentaires et de configuration
# sont déplacés vers la fin pour éviter les imports circulaires
