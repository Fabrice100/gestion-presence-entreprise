"""
Service de gestion centralisée des erreurs pour PresencePro.

Ce module fournit :
- Gestion centralisée des exceptions
- Messages d'erreur utilisateur-friendly
- Codes d'erreur standardisés
- Récupération gracieuse des erreurs
- Logging structuré des erreurs

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import DatabaseError, IntegrityError
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from common.structured_logging import structured_logger


class ErrorCode(Enum):
    """Codes d'erreur standardisés du système."""
    
    # Erreurs générales
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    DATABASE_ERROR = "DATABASE_ERROR"
    
    # Erreurs d'authentification
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    
    # Erreurs de pointage
    PUNCH_INVALID_SEQUENCE = "PUNCH_INVALID_SEQUENCE"
    PUNCH_GPS_INVALID = "PUNCH_GPS_INVALID"
    PUNCH_OUTSIDE_ZONE = "PUNCH_OUTSIDE_ZONE"
    PUNCH_LOW_ACCURACY = "PUNCH_LOW_ACCURACY"
    PUNCH_DUPLICATE = "PUNCH_DUPLICATE"
    PUNCH_PERMISSION_DENIED = "PUNCH_PERMISSION_DENIED"
    
    # Erreurs de congés
    LEAVE_INSUFFICIENT_BALANCE = "LEAVE_INSUFFICIENT_BALANCE"
    LEAVE_INVALID_DATES = "LEAVE_INVALID_DATES"
    LEAVE_ALREADY_REQUESTED = "LEAVE_ALREADY_REQUESTED"
    LEAVE_APPROVAL_DENIED = "LEAVE_APPROVAL_DENIED"
    
    # Erreurs de données
    DATA_VALIDATION_FAILED = "DATA_VALIDATION_FAILED"
    DATA_CORRUPTION = "DATA_CORRUPTION"
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    
    # Erreurs système
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs."""
    LOW = "LOW"           # Erreurs mineures, système fonctionne
    MEDIUM = "MEDIUM"     # Erreurs modérées, fonctionnalité limitée
    HIGH = "HIGH"         # Erreurs importantes, fonctionnalité cassée
    CRITICAL = "CRITICAL" # Erreurs critiques, système en danger


class ErrorContext:
    """Contexte d'une erreur pour logging et debugging."""
    
    def __init__(self, user=None, request=None, operation=None, 
                 additional_data: Dict[str, Any] = None):
        self.user = user
        self.request = request
        self.operation = operation
        self.additional_data = additional_data or {}
        
        # Extraction des métadonnées de la requête
        if request:
            self.ip_address = self._get_client_ip(request)
            self.user_agent = request.META.get('HTTP_USER_AGENT', '')
            self.path = request.path
        else:
            self.ip_address = None
            self.user_agent = None
            self.path = None
    
    def _get_client_ip(self, request):
        """Extrait l'IP réelle du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le contexte en dictionnaire pour logging."""
        context = {
            'operation': self.operation,
            'additional_data': self.additional_data
        }
        
        if self.user:
            context['user_id'] = self.user.id
            try:
                if hasattr(self.user, 'employee_profile') and self.user.employee_profile:
                    context['employee_id'] = self.user.employee_profile.employee_id
            except:
                pass
        
        if self.request:
            context.update({
                'ip_address': self.ip_address,
                'user_agent': self.user_agent,
                'path': self.path
            })
        
        return context


class SystemError(Exception):
    """Exception personnalisée pour les erreurs système."""
    
    def __init__(self, code: ErrorCode, message: str, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: ErrorContext = None,
                 original_exception: Exception = None):
        self.code = code
        self.message = message
        self.severity = severity
        self.context = context
        self.original_exception = original_exception
        super().__init__(self.message)


class ErrorHandler:
    """Gestionnaire centralisé des erreurs."""
    
    def __init__(self):
        self.logger = structured_logger
        self.error_messages = self._init_error_messages()
    
    def _init_error_messages(self) -> Dict[ErrorCode, str]:
        """Initialise les messages d'erreur utilisateur-friendly."""
        return {
            # Erreurs générales
            ErrorCode.UNKNOWN_ERROR: _("Une erreur inattendue s'est produite. Veuillez réessayer."),
            ErrorCode.VALIDATION_ERROR: _("Les données fournies ne sont pas valides."),
            ErrorCode.PERMISSION_DENIED: _("Vous n'avez pas l'autorisation d'effectuer cette action."),
            ErrorCode.NOT_FOUND: _("La ressource demandée n'a pas été trouvée."),
            ErrorCode.DATABASE_ERROR: _("Une erreur de base de données s'est produite."),
            
            # Erreurs d'authentification
            ErrorCode.AUTHENTICATION_FAILED: _("Échec de l'authentification."),
            ErrorCode.INVALID_CREDENTIALS: _("Nom d'utilisateur ou mot de passe incorrect."),
            ErrorCode.ACCOUNT_DISABLED: _("Votre compte a été désactivé."),
            ErrorCode.SESSION_EXPIRED: _("Votre session a expiré. Veuillez vous reconnecter."),
            
            # Erreurs de pointage
            ErrorCode.PUNCH_INVALID_SEQUENCE: _("Séquence de pointage invalide. Vérifiez vos pointages précédents."),
            ErrorCode.PUNCH_GPS_INVALID: _("Coordonnées GPS invalides. Vérifiez votre localisation."),
            ErrorCode.PUNCH_OUTSIDE_ZONE: _("Vous êtes en dehors de la zone autorisée pour le pointage."),
            ErrorCode.PUNCH_LOW_ACCURACY: _("Précision GPS insuffisante. Attendez une meilleure réception."),
            ErrorCode.PUNCH_DUPLICATE: _("Pointage en double détecté."),
            ErrorCode.PUNCH_PERMISSION_DENIED: _("Pointage non autorisé pour votre compte."),
            
            # Erreurs de congés
            ErrorCode.LEAVE_INSUFFICIENT_BALANCE: _("Solde de congés insuffisant."),
            ErrorCode.LEAVE_INVALID_DATES: _("Dates de congé invalides."),
            ErrorCode.LEAVE_ALREADY_REQUESTED: _("Une demande de congé existe déjà pour cette période."),
            ErrorCode.LEAVE_APPROVAL_DENIED: _("Demande de congé refusée."),
            
            # Erreurs de données
            ErrorCode.DATA_VALIDATION_FAILED: _("Validation des données échouée."),
            ErrorCode.DATA_CORRUPTION: _("Données corrompues détectées."),
            ErrorCode.DATA_NOT_FOUND: _("Données non trouvées."),
            
            # Erreurs système
            ErrorCode.SYSTEM_MAINTENANCE: _("Le système est en maintenance. Réessayez plus tard."),
            ErrorCode.SERVICE_UNAVAILABLE: _("Service temporairement indisponible."),
            ErrorCode.RATE_LIMIT_EXCEEDED: _("Trop de tentatives. Veuillez patienter."),
        }
    
    def handle_exception(self, exception: Exception, 
                        context: ErrorContext = None) -> Tuple[ErrorCode, str, ErrorSeverity]:
        """
        Gère une exception et retourne les informations d'erreur.
        
        Args:
            exception: Exception à gérer
            context: Contexte de l'erreur
            
        Returns:
            Tuple (code, message, severity)
        """
        # Gestion des exceptions Django
        if isinstance(exception, ValidationError):
            return self._handle_validation_error(exception, context)
        elif isinstance(exception, PermissionDenied):
            return self._handle_permission_error(exception, context)
        elif isinstance(exception, Http404):
            return self._handle_not_found_error(exception, context)
        elif isinstance(exception, DatabaseError):
            return self._handle_database_error(exception, context)
        
        # Gestion des exceptions personnalisées
        elif isinstance(exception, SystemError):
            return self._handle_system_error(exception, context)
        
        # Gestion des exceptions génériques
        else:
            return self._handle_generic_error(exception, context)
    
    def _handle_validation_error(self, exception: ValidationError, 
                                context: ErrorContext) -> Tuple[ErrorCode, str, ErrorSeverity]:
        """Gère les erreurs de validation Django."""
        self.logger.log_error(
            exception, 
            context.to_dict() if context else {},
            error_type="validation_error"
        )
        
        return (
            ErrorCode.VALIDATION_ERROR,
            str(exception.message) if hasattr(exception, 'message') else self.error_messages[ErrorCode.VALIDATION_ERROR],
            ErrorSeverity.MEDIUM
        )
    
    def _handle_permission_error(self, exception: PermissionDenied, 
                               context: ErrorContext) -> Tuple[ErrorCode, str, ErrorSeverity]:
        """Gère les erreurs de permission."""
        self.logger.log_error(
            exception,
            context.to_dict() if context else {},
            error_type="permission_error"
        )
        
        return (
            ErrorCode.PERMISSION_DENIED,
            self.error_messages[ErrorCode.PERMISSION_DENIED],
            ErrorSeverity.HIGH
        )
    
    def _handle_not_found_error(self, exception: Http404, 
                               context: ErrorContext) -> Tuple[ErrorCode, str, ErrorSeverity]:
        """Gère les erreurs 404."""
        self.logger.log_error(
            exception,
            context.to_dict() if context else {},
            error_type="not_found_error"
        )
        
        return (
            ErrorCode.NOT_FOUND,
            self.error_messages[ErrorCode.NOT_FOUND],
            ErrorSeverity.MEDIUM
        )
    
    def _handle_database_error(self, exception: DatabaseError, 
                             context: ErrorContext) -> Tuple[ErrorCode, str, ErrorSeverity]:
        """Gère les erreurs de base de données."""
        self.logger.log_error(
            exception,
            context.to_dict() if context else {},
            error_type="database_error"
        )
        
        return (
            ErrorCode.DATABASE_ERROR,
            self.error_messages[ErrorCode.DATABASE_ERROR],
            ErrorSeverity.HIGH
        )
    
    def _handle_system_error(self, exception: SystemError, 
                           context: ErrorContext) -> Tuple[ErrorCode, str, ErrorSeverity]:
        """Gère les erreurs système personnalisées."""
        self.logger.log_error(
            exception,
            context.to_dict() if context else {},
            error_type="system_error",
            severity=exception.severity.value
        )
        
        return (
            exception.code,
            exception.message,
            exception.severity
        )
    
    def _handle_generic_error(self, exception: Exception, 
                            context: ErrorContext) -> Tuple[ErrorCode, str, ErrorSeverity]:
        """Gère les erreurs génériques."""
        self.logger.log_error(
            exception,
            context.to_dict() if context else {},
            error_type="generic_error"
        )
        
        return (
            ErrorCode.UNKNOWN_ERROR,
            self.error_messages[ErrorCode.UNKNOWN_ERROR],
            ErrorSeverity.HIGH
        )
    
    def create_error_response(self, code: ErrorCode, message: str, 
                            severity: ErrorSeverity, 
                            additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crée une réponse d'erreur standardisée.
        
        Args:
            code: Code d'erreur
            message: Message d'erreur
            severity: Sévérité de l'erreur
            additional_data: Données supplémentaires
            
        Returns:
            Dictionnaire de réponse d'erreur
        """
        response = {
            'success': False,
            'error': {
                'code': code.value,
                'message': message,
                'severity': severity.value,
                'timestamp': self.logger._get_timestamp()
            }
        }
        
        if additional_data:
            response['error']['details'] = additional_data
        
        return response
    
    def log_error_with_context(self, exception: Exception, 
                             context: ErrorContext,
                             error_type: str = "unknown"):
        """Log une erreur avec son contexte complet."""
        self.logger.log_error(
            exception,
            context.to_dict(),
            error_type=error_type
        )


# Instance globale du gestionnaire d'erreurs
error_handler = ErrorHandler()


# Décorateur pour gestion automatique des erreurs
def handle_errors(error_type: str = "unknown", 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """
    Décorateur pour gestion automatique des erreurs dans les vues.
    
    Args:
        error_type: Type d'erreur pour le logging
        severity: Sévérité par défaut
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extraction du contexte depuis les arguments
                context = None
                if args and hasattr(args[0], 'request'):
                    context = ErrorContext(
                        user=getattr(args[0], 'request', None).user if hasattr(args[0], 'request') else None,
                        request=getattr(args[0], 'request', None) if hasattr(args[0], 'request') else None,
                        operation=func.__name__
                    )
                
                code, message, actual_severity = error_handler.handle_exception(e, context)
                
                # Pour les vues Django, on peut rediriger ou retourner une réponse d'erreur
                if hasattr(args[0], 'request'):
                    from django.contrib import messages
                    messages.error(args[0].request, message)
                    return error_handler.create_error_response(code, message, actual_severity)
                
                # Pour les autres cas, on relance l'exception
                raise SystemError(code, message, actual_severity, context, e)
        
        return wrapper
    return decorator

