"""
Service de validation sécurisée pour PresencePro.

Ce module fournit des validateurs robustes pour :
- Validation des données GPS
- Sanitisation des entrées utilisateur
- Validation des formats de données
- Protection contre les injections
- Validation des permissions

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

import re
import math
from typing import Dict, Any, Optional, Tuple
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from common.structured_logging import structured_logger


class SecureDataValidator:
    """
    Service de validation sécurisée des données.
    
    Fournit des méthodes de validation robustes pour tous les types
    de données sensibles du système.
    """
    
    # Patterns de validation
    GPS_PATTERN = re.compile(r'^-?\d{1,3}(\.\d{1,18})?$')  # Plus flexible pour accepter plus de décimales
    EMPLOYEE_ID_PATTERN = re.compile(r'^EMP\d{3}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[\d\s\-\(\)]{8,20}$')
    
    # Limites de sécurité
    MAX_GPS_COORDINATE = 90.0  # Latitude max
    MIN_GPS_COORDINATE = -90.0  # Latitude min
    MAX_GPS_LONGITUDE = 180.0
    MIN_GPS_LONGITUDE = -180.0
    MAX_GPS_ACCURACY = 1000.0  # 1km max
    MIN_GPS_ACCURACY = 0.1     # 10cm min
    
    MAX_STRING_LENGTH = 1000
    MAX_REASON_LENGTH = 500
    
    def __init__(self):
        self.logger = structured_logger
    
    # ===================================================================
    # VALIDATION GPS
    # ===================================================================
    
    def validate_gps_coordinates(self, latitude: str, longitude: str, 
                               accuracy: str) -> Dict[str, Any]:
        """
        Valide et sanitise les coordonnées GPS.
        
        Args:
            latitude: Latitude en string
            longitude: Longitude en string
            accuracy: Précision en string
            
        Returns:
            Dict avec 'valid', 'latitude', 'longitude', 'accuracy', 'error_message'
        """
        try:
            # Normaliser les valeurs (convertir en string, gérer None)
            latitude = str(latitude).strip() if latitude is not None else ''
            longitude = str(longitude).strip() if longitude is not None else ''
            accuracy = str(accuracy).strip() if accuracy is not None else ''
            
            # Normaliser les valeurs spéciales (accepter comme vides)
            if not latitude or latitude.lower() in ['none', 'null', 'nan', '', '0', '0.0']:
                latitude = ''
            if not longitude or longitude.lower() in ['none', 'null', 'nan', '', '0', '0.0']:
                longitude = ''
            if not accuracy or accuracy.lower() in ['none', 'null', 'nan', '', '0', '0.0']:
                accuracy = ''
            
            # 0. Gérer les valeurs vides - si vides, on accepte (sera géré par parse_gps_data qui utilisera les coordonnées du bureau)
            if not latitude:
                # Coordonnée vide acceptée - parse_gps_data gérera
                lat_float = None
            else:
                # 1. Validation du format seulement si valeur présente
                if not self._is_valid_gps_format(latitude):
                    return self._error_result("Format de latitude invalide")
                # 2. Conversion en float
                lat_float = float(latitude)
                # 3. Validation des limites latitude
                if not (self.MIN_GPS_COORDINATE <= lat_float <= self.MAX_GPS_COORDINATE):
                    return self._error_result("Latitude hors limites (-90° à +90°)")
            
            if not longitude:
                # Coordonnée vide acceptée - parse_gps_data gérera
                lng_float = None
            else:
                # 1. Validation du format seulement si valeur présente
                if not self._is_valid_gps_format(longitude):
                    return self._error_result("Format de longitude invalide")
                # 2. Conversion en float
                lng_float = float(longitude)
                # 3. Validation des limites longitude
                if not (self.MIN_GPS_LONGITUDE <= lng_float <= self.MAX_GPS_LONGITUDE):
                    return self._error_result("Longitude hors limites (-180° à +180°)")
            
            # Si accuracy est vide, utiliser valeur par défaut
            if not accuracy:
                acc_float = 50.0  # Précision par défaut acceptable
            else:
                # Validation seulement si valeur présente
                if not self._is_valid_accuracy_format(accuracy):
                    return self._error_result("Format de précision invalide")
                acc_float = float(accuracy)
                # Validation des limites précision
                if not (self.MIN_GPS_ACCURACY <= acc_float <= self.MAX_GPS_ACCURACY):
                    return self._error_result(f"Précision hors limites ({self.MIN_GPS_ACCURACY}m à {self.MAX_GPS_ACCURACY}m)")
            
            # 4. Validation de cohérence (pas de coordonnées impossibles) seulement si présentes
            if lat_float is not None and lng_float is not None:
                if abs(lat_float) > 90 or abs(lng_float) > 180:
                    return self._error_result("Coordonnées GPS impossibles")
            
            # 5. Logging de la validation réussie (si valeurs présentes)
            if lat_float is not None:
                self.logger.system_logger.info(
                    "Validation GPS réussie",
                    latitude=lat_float,
                    longitude=lng_float,
                    accuracy=acc_float,
                    event_type="gps_validation"
                )
            
            # 6. Retourner les valeurs validées (None si vides - sera géré par parse_gps_data)
            return {
                'valid': True,
                'latitude': lat_float,
                'longitude': lng_float,
                'accuracy': acc_float if acc_float is not None else 50.0,
                'error_message': None
            }
            
        except ValueError as e:
            self.logger.log_error(e, {'latitude': latitude, 'longitude': longitude, 'accuracy': accuracy})
            return self._error_result("Erreur de conversion des coordonnées GPS")
        except Exception as e:
            self.logger.log_error(e, {'latitude': latitude, 'longitude': longitude, 'accuracy': accuracy})
            return self._error_result("Erreur de validation GPS")
    
    def _is_valid_gps_format(self, value: str) -> bool:
        """Vérifie le format d'une coordonnée GPS."""
        if not isinstance(value, str):
            # Si ce n'est pas une string, essayer de convertir
            try:
                value = str(value)
            except:
                return False
        
        value = value.strip()
        
        # Accepter les valeurs vides (sera géré par parse_gps_data)
        if not value or value == '' or value == 'None' or value == 'null' or value == 'NaN' or value.lower() == 'nan':
            return True
        
        # Essayer de convertir en float pour vérifier que c'est un nombre valide
        try:
            float_val = float(value)
            # Vérifier que ce n'est pas NaN, inf, ou -inf
            if math.isnan(float_val) or math.isinf(float_val):
                return False
            # Si la conversion réussit, c'est un nombre valide
            return True
        except (ValueError, OverflowError):
            return False
    
    def _is_valid_accuracy_format(self, value: str) -> bool:
        """Vérifie le format de précision GPS."""
        if not isinstance(value, str):
            return False
        try:
            acc_float = float(value.strip())
            return self.MIN_GPS_ACCURACY <= acc_float <= self.MAX_GPS_ACCURACY
        except ValueError:
            return False
    
    # ===================================================================
    # VALIDATION DES DONNÉES UTILISATEUR
    # ===================================================================
    
    def validate_employee_id(self, employee_id: str) -> Tuple[bool, str]:
        """
        Valide un ID employé.
        
        Args:
            employee_id: ID employé à valider
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(employee_id, str):
            return False, "ID employé doit être une chaîne de caractères"
        
        employee_id = employee_id.strip().upper()
        
        if not self.EMPLOYEE_ID_PATTERN.match(employee_id):
            return False, "Format d'ID employé invalide (doit être EMPXXX)"
        
        if len(employee_id) != 6:
            return False, "ID employé doit faire exactement 6 caractères"
        
        return True, None
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """
        Valide une adresse email.
        
        Args:
            email: Email à valider
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(email, str):
            return False, "Email doit être une chaîne de caractères"
        
        email = email.strip().lower()
        
        if len(email) > 254:  # RFC 5321 limite
            return False, "Email trop long (max 254 caractères)"
        
        # Vérification des caractères dangereux AVANT le regex
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')']
        if any(char in email for char in dangerous_chars):
            return False, "Email contient des caractères non autorisés"
        
        if not self.EMAIL_PATTERN.match(email):
            return False, "Format d'email invalide"
        
        return True, None
    
    def validate_reason(self, reason: str) -> Tuple[bool, str]:
        """
        Valide un motif de congé ou note.
        
        Args:
            reason: Motif à valider
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(reason, str):
            return False, "Motif doit être une chaîne de caractères"
        
        reason = reason.strip()
        
        if len(reason) > self.MAX_REASON_LENGTH:
            return False, f"Motif trop long (max {self.MAX_REASON_LENGTH} caractères)"
        
        if len(reason) < 3:
            return False, "Motif trop court (min 3 caractères)"
        
        # Vérification des caractères dangereux
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}', '[', ']']
        if any(char in reason for char in dangerous_chars):
            return False, "Motif contient des caractères non autorisés"
        
        dangerous_patterns = [
            r'<script.*?>.*?</script>',  # Scripts
            r'javascript:',              # JavaScript
            r'data:',                    # Data URLs
            r'vbscript:',                # VBScript
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, reason, re.IGNORECASE):
                return False, "Motif contient du code potentiellement dangereux"
        
        return True, None
    
    # ===================================================================
    # SANITISATION DES DONNÉES
    # ===================================================================
    
    def sanitize_string(self, value: str, max_length: int = None) -> str:
        """
        Sanitise une chaîne de caractères.
        
        Args:
            value: Valeur à sanitizer
            max_length: Longueur maximale
            
        Returns:
            Chaîne sanitizée
        """
        if not isinstance(value, str):
            return ""
        
        # Suppression des espaces en début/fin
        sanitized = value.strip()
        
        # Suppression des caractères de contrôle
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Limitation de longueur
        if max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    def sanitize_gps_data(self, gps_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitise les données GPS.
        
        Args:
            gps_data: Dictionnaire avec latitude, longitude, accuracy
            
        Returns:
            Dictionnaire sanitizé
        """
        sanitized = {}
        
        # Sanitisation des coordonnées
        for key in ['latitude', 'longitude', 'accuracy']:
            if key in gps_data and gps_data[key] is not None:
                value = str(gps_data[key]).strip()
                # Suppression des caractères non numériques sauf . et -
                value = re.sub(r'[^\d\.\-]', '', value)
                sanitized[key] = value if value else ''  # Chaîne vide si tout supprimé
            else:
                sanitized[key] = ''  # Chaîne vide si None ou absent
        
        return sanitized
    
    # ===================================================================
    # VALIDATION DES PERMISSIONS
    # ===================================================================
    
    def validate_punch_permission(self, user, punch_type: str) -> Tuple[bool, str]:
        """
        Valide les permissions de pointage.
        
        Args:
            user: Utilisateur Django
            punch_type: Type de pointage
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not user.is_authenticated:
            return False, "Utilisateur non authentifié"
        
        if not hasattr(user, 'employee_profile'):
            return False, "Profil employé manquant"
        
        if not user.employee_profile.is_active:
            return False, "Compte employé inactif"
        
        if not user.employee_profile.can_punch:
            return False, "Pointage non autorisé pour cet employé"
        
        if punch_type not in ['in', 'out']:
            return False, "Type de pointage invalide"
        
        return True, None
    
    # ===================================================================
    # MÉTHODES UTILITAIRES
    # ===================================================================
    
    def _error_result(self, message: str) -> Dict[str, Any]:
        """Retourne un résultat d'erreur standardisé."""
        return {
            'valid': False,
            'error_message': message,
            'latitude': None,
            'longitude': None,
            'accuracy': None
        }
    
    def log_validation_attempt(self, data_type: str, data: Dict[str, Any], 
                              success: bool, error: str = None):
        """
        Log une tentative de validation.
        
        Args:
            data_type: Type de données validées
            data: Données validées
            success: True si validation réussie
            error: Message d'erreur si applicable
        """
        self.logger.system_logger.info(
            "Tentative de validation",
            data_type=data_type,
            success=success,
            error=error,
            data_keys=list(data.keys()) if isinstance(data, dict) else None,
            event_type="data_validation"
        )


# Instance globale du validateur
secure_validator = SecureDataValidator()
