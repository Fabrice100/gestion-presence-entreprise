"""
Modèles pour la gestion du pointage et des présences.

Ce module contient les modèles Django pour :
- Attendance : Pointages d'entrée et de sortie avec géolocalisation
- AttendanceAnomaly : Anomalies détectées lors du pointage
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
    
    # Choix pour les statuts
    STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('late', 'En retard'),
        ('early', 'Sortie anticipée'),
        ('missing_out', 'Sortie oubliée'),
        ('double_punch', 'Double pointage'),
        ('outside_zone', 'Hors zone'),
        ('low_accuracy', 'Précision faible'),
    ]
    
    # Choix pour les sources de pointage
    SOURCE_CHOICES = [
        ('web', 'Web'),
        ('mobile', 'Mobile'),
        ('kiosk', 'Kiosque'),
        ('admin', 'Administration'),
    ]
    
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="Employé",
        help_text="Employé qui effectue le pointage"
    )
    
    date = models.DateField(
        default=timezone.now,
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
    
    # Informations de géolocalisation
    latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name="Latitude",
        help_text="Latitude GPS du pointage"
    )
    
    longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        verbose_name="Longitude",
        help_text="Longitude GPS du pointage"
    )
    
    accuracy = models.FloatField(
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
        # Calculer la distance du centre du site
        if self.latitude and self.longitude:
            self.distance_from_site = self.calculate_distance_from_site()
        
        # Détecter les anomalies
        self.detect_anomalies()
        
        super().save(*args, **kwargs)
    
    def calculate_distance_from_site(self):
        """
        Calcule la distance entre le pointage et le centre du site.
        
        Utilise la formule de Haversine pour calculer la distance en mètres.
        """
        import math
        
        # Coordonnées du centre du site (configurées dans settings)
        site_lat = settings.SITE_CENTER_LAT
        site_lng = settings.SITE_CENTER_LNG
        
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
        # Vérifier la distance du site
        if self.distance_from_site and self.distance_from_site > settings.RADIUS_METERS:
            self.status = 'outside_zone'
            return
        
        # Vérifier la précision GPS
        if self.accuracy and self.accuracy > settings.ACCURACY_MAX_METERS:
            self.status = 'low_accuracy'
            return
        
        # Vérifier les heures de pointage (8h-17h)
        hour = self.time.hour
        if hour < 6 or hour > 19:  # En dehors des heures normales
            if self.punch_type == 'in':
                self.status = 'late' if hour > 9 else 'normal'
            else:
                self.status = 'early' if hour < 16 else 'normal'
        
        # Vérifier les doublons
        existing_punch = Attendance.objects.filter(
            employee=self.employee,
            date=self.date,
            punch_type=self.punch_type
        ).exclude(id=self.id).exists()
        
        if existing_punch:
            self.status = 'double_punch'
    
    def is_within_zone(self):
        """Vérifie si le pointage est dans la zone autorisée."""
        return self.distance_from_site <= settings.RADIUS_METERS if self.distance_from_site else False
    
    def is_accurate(self):
        """Vérifie si la précision GPS est acceptable."""
        return self.accuracy <= settings.ACCURACY_MAX_METERS if self.accuracy else False
    
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


class AttendanceAnomaly(models.Model):
    """
    Modèle pour enregistrer les anomalies détectées lors du pointage.
    
    Permet le suivi et la gestion des anomalies par les managers.
    """
    
    # Choix pour les types d'anomalies
    ANOMALY_TYPE_CHOICES = [
        ('late_arrival', 'Arrivée en retard'),
        ('early_departure', 'Départ anticipé'),
        ('missing_punch_out', 'Oubli de sortie'),
        ('outside_zone', 'Pointage hors zone'),
        ('low_accuracy', 'Précision GPS faible'),
        ('double_punch', 'Double pointage'),
        ('long_duration', 'Durée de travail excessive'),
    ]
    
    # Choix pour les statuts de résolution
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('justified', 'Justifiée'),
        ('resolved', 'Résolue'),
        ('ignored', 'Ignorée'),
    ]
    
    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name='anomalies',
        verbose_name="Pointage",
        help_text="Pointage concerné par l'anomalie"
    )
    
    anomaly_type = models.CharField(
        max_length=20,
        choices=ANOMALY_TYPE_CHOICES,
        verbose_name="Type d'anomalie",
        help_text="Type d'anomalie détectée"
    )
    
    description = models.TextField(
        verbose_name="Description",
        help_text="Description détaillée de l'anomalie"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut",
        help_text="Statut de résolution de l'anomalie"
    )
    
    justification = models.TextField(
        blank=True,
        null=True,
        verbose_name="Justification",
        help_text="Justification fournie par l'employé ou le manager"
    )
    
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_anomalies',
        verbose_name="Résolu par",
        help_text="Manager qui a résolu l'anomalie"
    )
    
    resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Résolu le",
        help_text="Date de résolution de l'anomalie"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        verbose_name = "Anomalie de pointage"
        verbose_name_plural = "Anomalies de pointage"
        ordering = ['-created_at']
    
    def __str__(self):
        """Représentation string de l'anomalie."""
        return f"{self.attendance.employee.get_full_name()} - {self.get_anomaly_type_display()}"
    
    def resolve(self, user, justification=None):
        """
        Marque l'anomalie comme résolue.
        """
        self.status = 'resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        if justification:
            self.justification = justification
        self.save()
    
    def justify(self, justification):
        """
        Marque l'anomalie comme justifiée.
        """
        self.status = 'justified'
        self.justification = justification
        self.save()


# Import des modèles d'heures supplémentaires
from .overtime_models import OvertimeConfiguration, OvertimeRecord
