"""
Services unifiés pour la gestion des pointages.

Ce module contient le PunchService unifié qui centralise toute la logique
de pointage en respectant les principes SOLID.

Auteur: Système de Gestion de Présence
Version: 2.0 (Refactorisé)
Date: 22 octobre 2025
"""

from datetime import date
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib import messages
import logging

from .attendance_service import (
    GPSValidationService,
    AttendanceBusinessRules,
    AttendanceService
)
from .admin_models import CompanySettings
from common.structured_logging import structured_logger
from common.secure_validation import secure_validator
from common.error_handler import error_handler, ErrorContext, ErrorCode, ErrorSeverity, SystemError
# Cache intelligent désactivé pour simplification
# from common.intelligent_cache import intelligent_cache, CacheStrategy, performance_cache

logger = logging.getLogger(__name__)


class PunchResult:
    """
    Classe pour encapsuler le résultat d'un pointage.
    
    Respecte le principe de responsabilité unique en séparant
    les données de résultat de la logique métier.
    """
    
    def __init__(self, success=False, attendance=None, error_message=None, warning_message=None, 
                 error_code=None, error_severity=None):
        self.success = success
        self.attendance = attendance
        self.error_message = error_message
        self.warning_message = warning_message
        self.error_code = error_code
        self.error_severity = error_severity
    
    def is_success(self):
        """Vérifie si le pointage a réussi."""
        return self.success and self.attendance is not None
    
    def has_error(self):
        """Vérifie s'il y a une erreur."""
        return not self.success or self.error_message is not None
    
    def has_warning(self):
        """Vérifie s'il y a un avertissement."""
        return self.warning_message is not None


class PunchService:
    """
    Service unifié pour la gestion des pointages.
    
    Centralise toute la logique de pointage en respectant les principes SOLID :
    - Single Responsibility: Gère uniquement les pointages
    - Open/Closed: Extensible via injection de dépendances
    - Dependency Inversion: Dépend d'abstractions (services)
    """
    
    def __init__(self, validation_service=None, gps_service=None, attendance_service=None):
        """
        Initialise le service avec injection de dépendances.
        
        Args:
            validation_service: Service de validation des règles métier
            gps_service: Service de validation GPS
            attendance_service: Service de création des pointages
        """
        self.validation = validation_service or AttendanceBusinessRules()
        self.gps = gps_service or GPSValidationService()
        self.attendance = attendance_service or AttendanceService()
        self.settings = CompanySettings.load()
    
    def create_punch(self, user, punch_type, gps_data, request_meta=None, **kwargs):
        """
        Crée un pointage avec toute la validation et logique métier.
        
        Cette méthode centralise toute la logique de pointage :
        1. Validation des permissions
        2. Validation GPS
        3. Vérification des doublons
        4. Création du pointage
        5. Calcul des heures travaillées
        6. Logging des événements
        
        Args:
            user (User): Utilisateur qui effectue le pointage
            punch_type (str): Type de pointage ('in' ou 'out')
            gps_data (dict): Données GPS {latitude, longitude, accuracy, demo_mode}
            request_meta (dict, optional): Métadonnées de la requête (IP, user_agent, etc.)
            
        Returns:
            PunchResult: Résultat du pointage avec succès/erreur et données
        """
        # Utiliser request_meta fourni ou None par défaut
        if request_meta is None:
            request_meta = {}
        
        # Création du contexte d'erreur
        error_context = ErrorContext(
            user=user,
            request=None,  # Pas de request dans request_meta, c'est juste IP/user_agent
            operation='create_punch',
            additional_data={
                'punch_type': punch_type,
                'gps_data_keys': list(gps_data.keys()) if gps_data else []
            }
        )
        
        try:
            # 0. VALIDATION SÉCURISÉE DES DONNÉES ENTRANTES
            # Sanitisation des données GPS
            sanitized_gps = secure_validator.sanitize_gps_data(gps_data)
            
            # Récupérer les valeurs (peuvent être vides - OK)
            lat_val = sanitized_gps.get('latitude', '') or ''
            lon_val = sanitized_gps.get('longitude', '') or ''
            acc_val = sanitized_gps.get('accuracy', '') or '50'  # Par défaut si vide
            
            # Validation sécurisée des coordonnées GPS
            gps_validation_result = secure_validator.validate_gps_coordinates(
                lat_val,
                lon_val,
                acc_val
            )
            
            if not gps_validation_result['valid']:
                # Logging de la validation échouée
                secure_validator.log_validation_attempt(
                    'gps_coordinates',
                    sanitized_gps,
                    success=False,
                    error=gps_validation_result['error_message']
                )
                
                structured_logger.log_punch_attempt(
                    user=user,
                    punch_type=punch_type,
                    latitude=0,
                    longitude=0,
                    accuracy=0,
                    success=False,
                    reason=f"Validation GPS échouée: {gps_validation_result['error_message']}"
                )
                
                return PunchResult(
                    success=False,
                    error_message=gps_validation_result['error_message']
                )
            
            # Utilisation des données GPS validées
            # Si les coordonnées sont None (GPS non disponible), on les laisse vides
            # pour que parse_gps_data utilise les coordonnées du bureau
            validated_gps_data = {
                'latitude': gps_validation_result.get('latitude'),
                'longitude': gps_validation_result.get('longitude'),
                'accuracy': gps_validation_result.get('accuracy'),
                'demo_mode': gps_data.get('demo_mode', False)
            }
            
            # 1. VALIDATION DES PERMISSIONS
            can_punch, permission_error = self.validation.can_user_punch(user)
            if not can_punch:
                # Logging structuré de la tentative refusée
                structured_logger.log_punch_attempt(
                    user=user,
                    punch_type=punch_type,
                    latitude=validated_gps_data.get('latitude', 0),
                    longitude=validated_gps_data.get('longitude', 0),
                    accuracy=validated_gps_data.get('accuracy', 0),
                    success=False,
                    reason=permission_error
                )
                
                logger.warning(
                    f"Tentative de pointage refusée - {permission_error}",
                    extra={'user_id': user.id, 'punch_type': punch_type}
                )
                return PunchResult(
                    success=False,
                    error_message=permission_error
                )
            
            # 2. VALIDATION DE LA SÉQUENCE DE POINTAGE
            sequence_valid, sequence_error = self._validate_punch_sequence(user, punch_type)
            if not sequence_valid:
                logger.warning(
                    f"Séquence de pointage invalide - {sequence_error}",
                    extra={'user_id': user.id, 'punch_type': punch_type}
                )
                return PunchResult(
                    success=False,
                    error_message=sequence_error
                )
            
            # 3. VALIDATION GPS AVEC SERVICE EXISTANT (pour cohérence métier)
            gps_validation = self._validate_gps_data(validated_gps_data)
            if not gps_validation['valid']:
                logger.warning(
                    f"Validation GPS métier échouée - {gps_validation['error_message']}",
                    extra={'user_id': user.id, 'punch_type': punch_type}
                )
                return PunchResult(
                    success=False,
                    error_message=gps_validation['error_message']
                )
            
            # 4. CRÉATION DU POINTAGE (Transaction atomique)
            with transaction.atomic():
                attendance, creation_error = self.attendance.create_punch(
                    user=user,
                    punch_type=punch_type,
                    gps_data=gps_validation,
                    request_meta=request_meta
                )
                
                if creation_error:
                    logger.error(
                        f"Erreur création pointage - {creation_error}",
                        extra={'user_id': user.id, 'punch_type': punch_type}
                    )
                    return PunchResult(
                        success=False,
                        error_message=creation_error
                    )
            
            # 5. LOGGING STRUCTURÉ DU SUCCÈS
            structured_logger.log_punch_attempt(
                user=user,
                punch_type=punch_type,
                latitude=gps_validation.get('latitude', 0),
                longitude=gps_validation.get('longitude', 0),
                accuracy=gps_validation.get('accuracy', 0),
                success=True,
                distance=gps_validation.get('distance')
            )
            
            structured_logger.log_punch_created(
                attendance_id=attendance.id,
                user=user,
                punch_type=punch_type,
                worked_hours=getattr(attendance, 'worked_hours', None)
            )
            
            logger.info(
                f"Pointage {punch_type} créé avec succès",
                extra={
                    'user_id': user.id,
                    'employee_id': user.employee_profile.employee_id,
                    'punch_type': punch_type,
                    'attendance_id': attendance.id,
                    'gps_accuracy': gps_validation.get('accuracy'),
                    'distance_from_site': gps_validation.get('distance')
                }
            )
            
            # 6. PRÉPARATION DU MESSAGE DE SUCCÈS
            success_message = self._generate_success_message(attendance, punch_type)
            
            return PunchResult(
                success=True,
                attendance=attendance,
                warning_message=gps_validation.get('warning')
            )
            
        except Exception as e:
            # Gestion centralisée des erreurs
            code, message, severity = error_handler.handle_exception(e, error_context)
            
            # Création d'une erreur système personnalisée si nécessaire
            if code == ErrorCode.UNKNOWN_ERROR:
                system_error = SystemError(
                    code=code,
                    message=message,
                    severity=severity,
                    context=error_context,
                    original_exception=e
                )
                raise system_error
            
            # Retour d'un résultat d'erreur avec gestion centralisée
            return PunchResult(
                success=False,
                error_message=message,
                error_code=code.value,
                error_severity=severity.value
            )
    
    def _validate_punch_sequence(self, user, punch_type):
        """
        Valide la séquence de pointage (pas de sortie sans entrée).
        
        Args:
            user (User): Utilisateur
            punch_type (str): Type de pointage
            
        Returns:
            tuple: (is_valid, error_message)
        """
        today = date.today()
        
        # Vérifier les doublons
        from .models import Attendance
        existing_punch = Attendance.objects.filter(
            employee=user,
            date=today,
            punch_type=punch_type
        ).exists()
        
        if existing_punch:
            return False, f"Pointage {punch_type} déjà effectué aujourd'hui"
        
        # Vérifier la séquence (sortie sans entrée)
        if punch_type == 'out':
            punch_in_exists = Attendance.objects.filter(
                employee=user,
                date=today,
                punch_type='in'
            ).exists()
            
            if not punch_in_exists:
                return False, "Vous devez d'abord pointer l'entrée"
        
        return True, None
    
    def _validate_gps_data(self, gps_data):
        """
        Valide les données GPS.
        
        Args:
            gps_data (dict): Données GPS brutes
            
        Returns:
            dict: Résultat de validation avec données nettoyées
        """
        # Parser les données GPS
        # Convertir None ou valeurs vides en string vide pour parse_gps_data
        lat_val = gps_data.get('latitude')
        lon_val = gps_data.get('longitude')
        acc_val = gps_data.get('accuracy')
        
        parsed_gps = self.gps.parse_gps_data(
            latitude_str=str(lat_val) if lat_val is not None else '',
            longitude_str=str(lon_val) if lon_val is not None else '',
            accuracy_str=str(acc_val) if acc_val is not None else '',
            demo_mode=gps_data.get('demo_mode', False),
            settings=self.settings
        )
        
        if not parsed_gps['valid']:
            return parsed_gps
        
        # Validation de localisation
        location_validation = self.gps.validate_location(
            lat=parsed_gps['latitude'],
            lon=parsed_gps['longitude'],
            accuracy=parsed_gps['accuracy'],
            site_lat=float(self.settings.site_center_latitude),
            site_lon=float(self.settings.site_center_longitude),
            allowed_radius=self.settings.allowed_radius_meters,
            max_accuracy=self.settings.gps_accuracy_max_meters
        )
        
        if not location_validation['valid']:
            return {
                'valid': False,
                'error_message': location_validation['error_message']
            }
        
        # Ajouter la distance calculée
        parsed_gps['distance'] = location_validation['distance']
        
        return parsed_gps
    
    def _generate_success_message(self, attendance, punch_type):
        """
        Génère le message de succès approprié.
        
        Args:
            attendance (Attendance): Pointage créé
            punch_type (str): Type de pointage
            
        Returns:
            str: Message de succès
        """
        time_str = attendance.time.strftime("%H:%M")
        
        if punch_type == 'in':
            return f"Pointage d'entrée enregistré à {time_str}."
        else:
            # Calculer les heures travaillées si c'est une sortie
            worked_hours = getattr(attendance, 'worked_hours', None)
            if worked_hours:
                return f"Pointage de sortie enregistré à {time_str}. Heures travaillées: {worked_hours}h."
            else:
                return f"Pointage de sortie enregistré à {time_str}."
    
    def get_today_attendances(self, user):
        """
        Récupère les pointages du jour pour un utilisateur.
        
        Args:
            user (User): Utilisateur
            
        Returns:
            QuerySet: Pointages du jour
        """
        return self.attendance.get_today_attendances(user)
    
    def get_next_punch_type(self, user):
        """
        Détermine le prochain type de pointage.
        
        Args:
            user (User): Utilisateur
            
        Returns:
            str: 'in' ou 'out'
        """
        return self.validation.get_next_punch_type(user)
    
    def can_user_punch(self, user):
        """
        Vérifie si un utilisateur peut pointer.
        
        Args:
            user (User): Utilisateur
            
        Returns:
            tuple: (can_punch, error_message)
        """
        return self.validation.can_user_punch(user)
