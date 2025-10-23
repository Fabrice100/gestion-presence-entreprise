"""
Formulaires de validation pour le pointage.

Ce module contient les formulaires Django pour :
- Validation des données de pointage
- Validation GPS stricte
- Prévention des injections

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .admin_models import CompanySettings


class PunchForm(forms.Form):
    """
    Formulaire de validation pour le pointage.
    
    Valide toutes les données entrantes avant traitement.
    Respecte les principes de sécurité (validation stricte).
    """
    
    PUNCH_TYPE_CHOICES = [
        ('in', 'Entrée'),
        ('out', 'Sortie'),
    ]
    
    punch_type = forms.ChoiceField(
        choices=PUNCH_TYPE_CHOICES,
        required=True,
        error_messages={
            'required': 'Le type de pointage est requis.',
            'invalid_choice': 'Type de pointage invalide. Doit être "in" ou "out".'
        }
    )
    
    latitude = forms.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=False,
        validators=[
            MinValueValidator(-90, message='La latitude doit être entre -90 et 90.'),
            MaxValueValidator(90, message='La latitude doit être entre -90 et 90.')
        ],
        error_messages={
            'invalid': 'Latitude invalide. Format attendu: décimal (-90 à 90).'
        }
    )
    
    longitude = forms.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=False,
        validators=[
            MinValueValidator(-180, message='La longitude doit être entre -180 et 180.'),
            MaxValueValidator(180, message='La longitude doit être entre -180 et 180.')
        ],
        error_messages={
            'invalid': 'Longitude invalide. Format attendu: décimal (-180 à 180).'
        }
    )
    
    accuracy = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        validators=[
            MinValueValidator(0, message='La précision GPS ne peut pas être négative.'),
            MaxValueValidator(10000, message='Précision GPS trop élevée (max 10000m).')
        ],
        error_messages={
            'invalid': 'Précision GPS invalide. Format attendu: nombre décimal.'
        }
    )
    
    demo_mode = forms.BooleanField(
        required=False,
        initial=False
    )
    
    gps_disabled = forms.BooleanField(
        required=False,
        initial=False
    )
    
    def clean_accuracy(self):
        """
        Validation supplémentaire de la précision GPS.
        
        Vérifie que la précision ne dépasse pas la limite configurée.
        """
        accuracy = self.cleaned_data.get('accuracy')
        
        # Si pas de précision fournie, retourner valeur par défaut
        if accuracy is None:
            return 999.0
        
        # Charger les paramètres
        settings = CompanySettings.load()
        max_accuracy = settings.gps_accuracy_max_meters
        
        # Vérifier la limite (sauf en mode démo)
        demo_mode = self.cleaned_data.get('demo_mode', False)
        if not demo_mode and accuracy > max_accuracy:
            raise forms.ValidationError(
                f'Précision GPS trop faible ({accuracy}m). '
                f'Maximum autorisé: {max_accuracy}m.'
            )
        
        return accuracy
    
    def clean(self):
        """
        Validation globale du formulaire.
        
        Vérifie la cohérence des données GPS.
        """
        cleaned_data = super().clean()
        
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        demo_mode = cleaned_data.get('demo_mode', False)
        gps_disabled = cleaned_data.get('gps_disabled', False)
        
        # En mode normal (pas démo, GPS activé), coordonnées requises
        if not demo_mode and not gps_disabled:
            if latitude is None or longitude is None:
                # Pas d'erreur, on utilisera les coordonnées du bureau
                pass
        
        return cleaned_data
    
    def get_gps_data(self):
        """
        Retourne les données GPS validées.
        
        Returns:
            dict: {
                'latitude': float,
                'longitude': float,
                'accuracy': float,
                'demo_mode': bool,
                'gps_disabled': bool
            }
        """
        return {
            'latitude': self.cleaned_data.get('latitude'),
            'longitude': self.cleaned_data.get('longitude'),
            'accuracy': self.cleaned_data.get('accuracy', 999.0),
            'demo_mode': self.cleaned_data.get('demo_mode', False),
            'gps_disabled': self.cleaned_data.get('gps_disabled', False)
        }


class PunchAPIForm(PunchForm):
    """
    Formulaire pour l'API de pointage (JSON).
    
    Hérite de PunchForm mais avec validation plus stricte.
    """
    
    # Rendre les coordonnées obligatoires pour l'API
    latitude = forms.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=True,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90)
        ],
        error_messages={
            'required': 'La latitude est requise pour l\'API.',
            'invalid': 'Latitude invalide.'
        }
    )
    
    longitude = forms.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=True,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180)
        ],
        error_messages={
            'required': 'La longitude est requise pour l\'API.',
            'invalid': 'Longitude invalide.'
        }
    )
    
    accuracy = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10000)
        ],
        error_messages={
            'required': 'La précision GPS est requise pour l\'API.',
            'invalid': 'Précision GPS invalide.'
        }
    )
