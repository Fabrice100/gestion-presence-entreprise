"""
Modèles pour les rapports et paramètres système.

Ce module contient les modèles Django pour :
- SystemSettings : Paramètres de configuration du système
- ReportTemplate : Modèles de rapports prédéfinis

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SystemSettings(models.Model):
    """
    Modèle pour stocker les paramètres de configuration du système.
    
    Permet de configurer dynamiquement les règles métier sans redéploiement.
    """
    
    # Choix pour les types de paramètres
    SETTING_TYPE_CHOICES = [
        ('general', 'Général'),
        ('attendance', 'Pointage'),
        ('leave', 'Congés'),
        ('notification', 'Notifications'),
        ('security', 'Sécurité'),
    ]
    
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Clé",
        help_text="Clé unique du paramètre"
    )
    
    value = models.TextField(
        verbose_name="Valeur",
        help_text="Valeur du paramètre"
    )
    
    setting_type = models.CharField(
        max_length=20,
        choices=SETTING_TYPE_CHOICES,
        default='general',
        verbose_name="Type",
        help_text="Type de paramètre"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description du paramètre"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Paramètre actif"
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Modifié par",
        help_text="Utilisateur qui a modifié le paramètre"
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
        verbose_name = "Paramètre système"
        verbose_name_plural = "Paramètres système"
        ordering = ['setting_type', 'key']
    
    def __str__(self):
        """Représentation string du paramètre."""
        return f"{self.key} = {self.value}"
    
    @classmethod
    def get_setting(cls, key, default=None):
        """
        Récupère la valeur d'un paramètre par sa clé.
        """
        try:
            setting = cls.objects.get(key=key, is_active=True)
            return setting.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, setting_type='general', description=None, user=None):
        """
        Définit la valeur d'un paramètre.
        """
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={
                'value': value,
                'setting_type': setting_type,
                'description': description,
                'updated_by': user
            }
        )
        
        if not created:
            setting.value = value
            setting.setting_type = setting_type
            if description:
                setting.description = description
            setting.updated_by = user
            setting.save()
        
        return setting
    
    def get_typed_value(self):
        """
        Retourne la valeur typée du paramètre (int, float, bool, str).
        """
        value = self.value.lower().strip()
        
        # Booléen
        if value in ['true', 'false']:
            return value == 'true'
        
        # Entier
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # String
        return self.value


class ReportTemplate(models.Model):
    """
    Modèle représentant un modèle de rapport prédéfini.
    
    Permet de créer des rapports standardisés pour les différents besoins.
    """
    
    # Choix pour les types de rapports
    REPORT_TYPE_CHOICES = [
        ('attendance', 'Rapport de présence'),
        ('leave', 'Rapport de congés'),
        ('anomaly', 'Rapport d\'anomalies'),
        ('summary', 'Rapport récapitulatif'),
        ('custom', 'Rapport personnalisé'),
    ]
    
    # Choix pour les formats
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name="Nom",
        help_text="Nom du modèle de rapport"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description du modèle de rapport"
    )
    
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        verbose_name="Type de rapport",
        help_text="Type de rapport"
    )
    
    format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default='pdf',
        verbose_name="Format",
        help_text="Format de sortie du rapport"
    )
    
    template_content = models.TextField(
        verbose_name="Contenu du modèle",
        help_text="Contenu du modèle de rapport (template)"
    )
    
    parameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Paramètres",
        help_text="Paramètres du rapport au format JSON"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Modèle de rapport actif"
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name="Public",
        help_text="Modèle accessible à tous les utilisateurs"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Créé par",
        help_text="Utilisateur qui a créé le modèle"
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
        verbose_name = "Modèle de rapport"
        verbose_name_plural = "Modèles de rapports"
        ordering = ['report_type', 'name']
    
    def __str__(self):
        """Représentation string du modèle de rapport."""
        return f"{self.name} ({self.get_report_type_display()})"
    
    def get_parameters_dict(self):
        """
        Retourne les paramètres sous forme de dictionnaire.
        """
        return self.parameters or {}
    
    def set_parameter(self, key, value):
        """
        Définit un paramètre.
        """
        if not self.parameters:
            self.parameters = {}
        self.parameters[key] = value
        self.save()
    
    def get_parameter(self, key, default=None):
        """
        Récupère un paramètre.
        """
        return self.parameters.get(key, default) if self.parameters else default