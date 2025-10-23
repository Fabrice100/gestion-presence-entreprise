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

logger = logging.getLogger(__name__)


class PunchResult:
    """
    Classe pour encapsuler le résultat d'un pointage.
    
    Respecte le principe de responsabilité unique en séparant
    les données de résultat de la logique métier.
    """
    
    def __init__(self, success=False, attendance=None, error_message=None, warning_message=None):
        self.success = success
        self.attendance = attendance
        self.error_message = error_message
        self.warning_message = warning_message
    
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
    
    def create_punch(self, user, punch_type, gps_data, request_meta=None):
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
            request_meta (dict): Métadonnées de la requête (IP, user_agent, etc.)
            
        Returns:
            PunchResult: Résultat du pointage avec succès/erreur et données
        """
        try:
            # 1. VALIDATION DES PERMISSIONS
            can_punch, permission_error = self.validation.can_user_punch(user)
            if not can_punch:
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
            
            # 3. VALIDATION GPS
            gps_validation = self._validate_gps_data(gps_data)
            if not gps_validation['valid']:
                logger.warning(
                    f"Validation GPS échouée - {gps_validation['error_message']}",
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
            
            # 5. LOGGING DU SUCCÈS
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
            logger.error(
                f"Erreur inattendue lors du pointage - {str(e)}",
                extra={'user_id': user.id, 'punch_type': punch_type},
                exc_info=True
            )
            return PunchResult(
                success=False,
                error_message=f"Erreur système: {str(e)}"
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
        parsed_gps = self.gps.parse_gps_data(
            latitude_str=str(gps_data.get('latitude', '')),
            longitude_str=str(gps_data.get('longitude', '')),
            accuracy_str=str(gps_data.get('accuracy', '')),
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
