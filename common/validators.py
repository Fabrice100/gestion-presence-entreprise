"""
Validateurs Django personnalisés pour PresencePro.

Ce module fournit des validateurs Django intégrés pour :
- Validation des coordonnées GPS
- Validation des IDs employés
- Validation des motifs de congé
- Validation des données sensibles

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from common.secure_validation import secure_validator


def validate_gps_coordinate(value):
    """
    Valide une coordonnée GPS (latitude ou longitude).
    
    Args:
        value: Coordonnée à valider
        
    Raises:
        ValidationError: Si la coordonnée est invalide
    """
    if not isinstance(value, (str, float, int)):
        raise ValidationError(
            _('La coordonnée GPS doit être un nombre.'),
            code='invalid_gps_type'
        )
    
    # Conversion en string pour validation
    coord_str = str(value).strip()
    
    # Validation du format
    if not secure_validator._is_valid_gps_format(coord_str):
        raise ValidationError(
            _('Format de coordonnée GPS invalide.'),
            code='invalid_gps_format'
        )
    
    try:
        coord_float = float(coord_str)
        
        # Validation des limites pour latitude
        if -90 <= coord_float <= 90:
            # C'est probablement une latitude
            if not (secure_validator.MIN_GPS_COORDINATE <= coord_float <= secure_validator.MAX_GPS_COORDINATE):
                raise ValidationError(
                    _('Latitude hors limites (-90° à +90°).'),
                    code='latitude_out_of_range'
                )
        elif -180 <= coord_float <= 180:
            # C'est probablement une longitude
            if not (secure_validator.MIN_GPS_LONGITUDE <= coord_float <= secure_validator.MAX_GPS_LONGITUDE):
                raise ValidationError(
                    _('Longitude hors limites (-180° à +180°).'),
                    code='longitude_out_of_range'
                )
        else:
            # Coordonnée complètement hors limites
            raise ValidationError(
                _('Coordonnée GPS hors limites.'),
                code='coordinate_out_of_range'
            )
    
    except ValueError:
        raise ValidationError(
            _('Coordonnée GPS non numérique.'),
            code='invalid_gps_numeric'
        )


def validate_gps_accuracy(value):
    """
    Valide la précision GPS.
    
    Args:
        value: Précision à valider
        
    Raises:
        ValidationError: Si la précision est invalide
    """
    if not isinstance(value, (str, float, int)):
        raise ValidationError(
            _('La précision GPS doit être un nombre.'),
            code='invalid_accuracy_type'
        )
    
    try:
        accuracy = float(value)
        
        if not (secure_validator.MIN_GPS_ACCURACY <= accuracy <= secure_validator.MAX_GPS_ACCURACY):
            raise ValidationError(
                _('Précision GPS hors limites (%(min)s m à %(max)s m).'),
                code='accuracy_out_of_range',
                params={
                    'min': secure_validator.MIN_GPS_ACCURACY,
                    'max': secure_validator.MAX_GPS_ACCURACY
                }
            )
    
    except ValueError:
        raise ValidationError(
            _('Précision GPS non numérique.'),
            code='invalid_accuracy_numeric'
        )


def validate_employee_id(value):
    """
    Valide un ID employé.
    
    Args:
        value: ID employé à valider
        
    Raises:
        ValidationError: Si l'ID est invalide
    """
    is_valid, error_message = secure_validator.validate_employee_id(value)
    
    if not is_valid:
        raise ValidationError(
            _(error_message),
            code='invalid_employee_id'
        )


def validate_email_address(value):
    """
    Valide une adresse email.
    
    Args:
        value: Email à valider
        
    Raises:
        ValidationError: Si l'email est invalide
    """
    is_valid, error_message = secure_validator.validate_email(value)
    
    if not is_valid:
        raise ValidationError(
            _(error_message),
            code='invalid_email'
        )


def validate_reason_text(value):
    """
    Valide un motif de congé ou note.
    
    Args:
        value: Motif à valider
        
    Raises:
        ValidationError: Si le motif est invalide
    """
    is_valid, error_message = secure_validator.validate_reason(value)
    
    if not is_valid:
        raise ValidationError(
            _(error_message),
            code='invalid_reason'
        )


def validate_phone_number(value):
    """
    Valide un numéro de téléphone.
    
    Args:
        value: Numéro de téléphone à valider
        
    Raises:
        ValidationError: Si le numéro est invalide
    """
    if not isinstance(value, str):
        raise ValidationError(
            _('Le numéro de téléphone doit être une chaîne de caractères.'),
            code='invalid_phone_type'
        )
    
    phone = value.strip()
    
    if len(phone) < 8:
        raise ValidationError(
            _('Numéro de téléphone trop court (minimum 8 caractères).'),
            code='phone_too_short'
        )
    
    if len(phone) > 20:
        raise ValidationError(
            _('Numéro de téléphone trop long (maximum 20 caractères).'),
            code='phone_too_long'
        )
    
    if not secure_validator.PHONE_PATTERN.match(phone):
        raise ValidationError(
            _('Format de numéro de téléphone invalide.'),
            code='invalid_phone_format'
        )


def validate_safe_string(value, max_length=None):
    """
    Valide une chaîne de caractères sécurisée.
    
    Args:
        value: Chaîne à valider
        max_length: Longueur maximale
        
    Raises:
        ValidationError: Si la chaîne est invalide
    """
    if not isinstance(value, str):
        raise ValidationError(
            _('La valeur doit être une chaîne de caractères.'),
            code='invalid_string_type'
        )
    
    # Sanitisation
    sanitized = secure_validator.sanitize_string(value, max_length)
    
    if len(sanitized) == 0:
        raise ValidationError(
            _('La chaîne ne peut pas être vide.'),
            code='empty_string'
        )
    
    if max_length and len(sanitized) > max_length:
        raise ValidationError(
            _('La chaîne est trop longue (maximum %(max_length)s caractères).'),
            code='string_too_long',
            params={'max_length': max_length}
        )
    
    # Vérification des caractères dangereux
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}', '[', ']']
    found_chars = [char for char in dangerous_chars if char in sanitized]
    
    if found_chars:
        raise ValidationError(
            _('La chaîne contient des caractères non autorisés: %(chars)s'),
            code='dangerous_characters',
            params={'chars': ', '.join(found_chars)}
        )


# Validateurs composés pour des cas spécifiques
class GPSDataValidator:
    """
    Validateur composé pour les données GPS complètes.
    """
    
    def __call__(self, value):
        """
        Valide un dictionnaire de données GPS.
        
        Args:
            value: Dict avec 'latitude', 'longitude', 'accuracy'
            
        Raises:
            ValidationError: Si les données GPS sont invalides
        """
        if not isinstance(value, dict):
            raise ValidationError(
                _('Les données GPS doivent être un dictionnaire.'),
                code='invalid_gps_data_type'
            )
        
        required_fields = ['latitude', 'longitude', 'accuracy']
        for field in required_fields:
            if field not in value:
                raise ValidationError(
                    _('Champ GPS manquant: %(field)s'),
                    code='missing_gps_field',
                    params={'field': field}
                )
        
        # Validation de chaque champ
        try:
            validate_gps_coordinate(value['latitude'])
            validate_gps_coordinate(value['longitude'])
            validate_gps_accuracy(value['accuracy'])
        except ValidationError as e:
            raise ValidationError(
                _('Données GPS invalides: %(error)s'),
                code='invalid_gps_data',
                params={'error': str(e)}
            )


# Instance globale du validateur GPS
validate_gps_data = GPSDataValidator()
