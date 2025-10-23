"""
Service pour la logique métier du pointage (attendance).

Ce module contient les services pour :
- Validation GPS et géolocalisation
- Calcul de distance (formule Haversine)
- Création de pointages
- Validation des règles métier

Auteur: Système de Gestion de Présence
Projet: Projet de fin de cycle
Version: 2.0 (Refactorisé selon principes SOLID)
Date: 22 octobre 2025
"""

from math import radians, sin, cos, sqrt, atan2
from datetime import date, time as dt_time
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal

from .models import Attendance
from .admin_models import CompanySettings


class GPSValidationService:
    """
    Service pour la validation GPS.
    
    Respecte le Single Responsibility Principle.
    """
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """
        Calcule la distance entre deux coordonnées GPS en mètres.
        
        Utilise la formule de Haversine pour un calcul précis sur une sphère.
        
        Args:
            lat1 (float): Latitude du point 1 en degrés
            lon1 (float): Longitude du point 1 en degrés
            lat2 (float): Latitude du point 2 en degrés
            lon2 (float): Longitude du point 2 en degrés
            
        Returns:
            float: Distance en mètres
            
        Example:
            >>> distance = GPSValidationService.calculate_distance(
            ...     6.1304, 1.2158,  # Cotonou
            ...     6.1320, 1.2170   # ~150m de Cotonou
            ... )
            >>> print(f"{distance:.0f}m")
            150m
        """
        R = 6371000  # Rayon de la Terre en mètres
        
        # Convertir en radians
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        # Formule de Haversine
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        
        return distance
    
    @staticmethod
    def validate_accuracy(accuracy, max_accuracy):
        """
        Valide la précision GPS.
        
        Args:
            accuracy (float): Précision GPS actuelle en mètres
            max_accuracy (float): Précision maximale autorisée en mètres
            
        Returns:
            tuple: (is_valid, error_message)
            
        Example:
            >>> is_valid, msg = GPSValidationService.validate_accuracy(10, 50)
            >>> print(is_valid)
            True
        """
        if accuracy > max_accuracy:
            return False, (
                f'Précision GPS trop faible ({accuracy:.0f}m). '
                f'Précision maximale autorisée: {max_accuracy}m. '
                f'Veuillez vous rapprocher d\'une fenêtre ou sortir à l\'extérieur.'
            )
        return True, None
    
    @staticmethod
    def validate_location(lat, lon, accuracy, site_lat, site_lon, allowed_radius, max_accuracy):
        """
        Validation complète de la géolocalisation.
        
        Vérifie :
        1. Précision GPS acceptable
        2. Distance par rapport au site dans le rayon autorisé
        
        Args:
            lat (float): Latitude employé
            lon (float): Longitude employé
            accuracy (float): Précision GPS en mètres
            site_lat (float): Latitude du site
            site_lon (float): Longitude du site
            allowed_radius (float): Rayon autorisé en mètres
            max_accuracy (float): Précision maximale en mètres
            
        Returns:
            dict: {
                'valid': bool,
                'distance': float,
                'error_message': str or None
            }
        """
        # Vérifier la précision
        is_accurate, accuracy_error = GPSValidationService.validate_accuracy(accuracy, max_accuracy)
        if not is_accurate:
            return {
                'valid': False,
                'distance': None,
                'error_message': accuracy_error
            }
        
        # Calculer la distance
        distance = GPSValidationService.calculate_distance(lat, lon, site_lat, site_lon)
        
        # Vérifier si dans le rayon
        if distance > allowed_radius:
            return {
                'valid': False,
                'distance': distance,
                'error_message': (
                    f'Vous êtes trop loin du lieu de travail ({distance:.0f}m). '
                    f'Distance maximale autorisée: {allowed_radius}m.'
                )
            }
        
        return {
            'valid': True,
            'distance': distance,
            'error_message': None
        }
    
    @staticmethod
    def parse_gps_data(latitude_str, longitude_str, accuracy_str, demo_mode=False, settings=None):
        """
        Parse et valide les données GPS brutes.
        
        Args:
            latitude_str (str): Latitude en string
            longitude_str (str): Longitude en string
            accuracy_str (str): Précision en string
            demo_mode (bool): Mode démo (utilise coordonnées du bureau)
            settings (CompanySettings): Configuration entreprise
            
        Returns:
            dict: {
                'valid': bool,
                'latitude': float or None,
                'longitude': float or None,
                'accuracy': float or None,
                'error_message': str or None
            }
        """
        if settings is None:
            settings = CompanySettings.load()
        
        # Mode démo : utiliser les coordonnées du bureau
        if demo_mode:
            return {
                'valid': True,
                'latitude': float(settings.site_center_latitude),
                'longitude': float(settings.site_center_longitude),
                'accuracy': 5.0,  # Précision parfaite
                'error_message': None
            }
        
        # GPS non disponible : utiliser les coordonnées du bureau
        if not latitude_str or not longitude_str or latitude_str == '0.0':
            return {
                'valid': True,
                'latitude': float(settings.site_center_latitude),
                'longitude': float(settings.site_center_longitude),
                'accuracy': 100.0,
                'error_message': None,
                'warning': 'Géolocalisation non disponible. Utilisation des coordonnées du bureau.'
            }
        
        # Parser les valeurs
        try:
            latitude = float(latitude_str)
            longitude = float(longitude_str)
            accuracy = float(accuracy_str) if accuracy_str else 999.0
            
            # Validation basique des coordonnées
            if not (-90 <= latitude <= 90):
                return {
                    'valid': False,
                    'latitude': None,
                    'longitude': None,
                    'accuracy': None,
                    'error_message': f'Latitude invalide: {latitude}'
                }
            
            if not (-180 <= longitude <= 180):
                return {
                    'valid': False,
                    'latitude': None,
                    'longitude': None,
                    'accuracy': None,
                    'error_message': f'Longitude invalide: {longitude}'
                }
            
            return {
                'valid': True,
                'latitude': latitude,
                'longitude': longitude,
                'accuracy': accuracy,
                'error_message': None
            }
            
        except ValueError:
            return {
                'valid': False,
                'latitude': None,
                'longitude': None,
                'accuracy': None,
                'error_message': 'Données GPS invalides.'
            }


class AttendanceBusinessRules:
    """
    Service pour les règles métier du pointage.
    
    Respecte le Single Responsibility Principle.
    """
    
    @staticmethod
    def can_user_punch(user):
        """
        Vérifie si un utilisateur peut pointer.
        
        Args:
            user (User): Utilisateur Django
            
        Returns:
            tuple: (can_punch, error_message)
        """
        # Vérifier profil employé
        try:
            profile = user.employee_profile
        except:
            return False, 'Vous n\'avez pas de profil employé. Contactez l\'administrateur.'
        
        # Vérifier permission de pointage
        if not profile.can_punch:
            return False, 'Vous n\'êtes pas autorisé à pointer.'
        
        # Vérifier si actif
        if not profile.is_active:
            return False, 'Votre compte est inactif.'
        
        return True, None
    
    @staticmethod
    def get_next_punch_type(user, today=None):
        """
        Détermine le prochain type de pointage (entrée ou sortie).
        
        Args:
            user (User): Utilisateur
            today (date): Date du jour (défaut: aujourd'hui)
            
        Returns:
            str: 'in' ou 'out'
        """
        if today is None:
            today = date.today()
        
        # Dernier pointage du jour
        last_attendance = Attendance.objects.filter(
            employee=user,
            date=today
        ).order_by('-time').first()
        
        if not last_attendance:
            return 'in'  # Première fois de la journée
        
        # Si le dernier était une entrée, le prochain est une sortie
        return 'out' if last_attendance.punch_type == 'in' else 'in'


class AttendanceService:
    """
    Service principal pour la gestion des pointages.
    
    Orchestre les autres services pour créer un pointage complet.
    """
    
    @staticmethod
    def create_punch(user, punch_type, gps_data, request_meta=None):
        """
        Crée un pointage avec toutes les validations.
        
        Transaction atomique pour garantir la cohérence des données.
        En cas d'erreur, toutes les modifications sont annulées.
        
        Args:
            user (User): Utilisateur qui pointe
            punch_type (str): 'in' ou 'out'
            gps_data (dict): Données GPS {latitude, longitude, accuracy, distance}
            request_meta (dict): Métadonnées de la requête (IP, user agent, etc.)
            
        Returns:
            tuple: (attendance, error_message)
        """
        from django.db import transaction
        
        # Vérifier les permissions
        can_punch, error = AttendanceBusinessRules.can_user_punch(user)
        if not can_punch:
            return None, error
        
        try:
            with transaction.atomic():
                # Créer le pointage
                now = timezone.now()
                
                attendance = Attendance.objects.create(
                    employee=user,
                    date=now.date(),
                    time=now.time(),
                    punch_type=punch_type,
                    latitude=gps_data.get('latitude'),
                    longitude=gps_data.get('longitude'),
                    accuracy=gps_data.get('accuracy'),
                    distance_from_site=gps_data.get('distance'),
                    source='web',
                    ip_address=request_meta.get('ip_address') if request_meta else None,
                    user_agent=request_meta.get('user_agent') if request_meta else None
                )
                
                return attendance, None
                
        except Exception as e:
            return None, f'Erreur lors de la création du pointage: {str(e)}'
    
    @staticmethod
    def get_today_attendances(user, today=None):
        """
        Récupère les pointages du jour pour un utilisateur.
        
        Args:
            user (User): Utilisateur
            today (date): Date (défaut: aujourd'hui)
            
        Returns:
            QuerySet: Pointages du jour
        """
        if today is None:
            today = date.today()
        
        return Attendance.objects.filter(
            employee=user,
            date=today
        ).order_by('time')
