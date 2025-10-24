"""
Service de logging structuré pour PresencePro.

Ce module fournit des loggers structurés pour différents domaines :
- Sécurité (authentification, autorisation, tentatives d'intrusion)
- Pointage (création, validation, anomalies)
- Comptes (création, modification, suppression)
- Système (erreurs, performances, monitoring)

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

import structlog
from django.conf import settings
from django.contrib.auth.models import User
from typing import Optional, Dict, Any


class StructuredLogger:
    """
    Service centralisé pour le logging structuré.
    
    Fournit des loggers spécialisés pour différents domaines métier
    avec un format JSON structuré pour faciliter l'analyse.
    """
    
    def __init__(self):
        self.security_logger = structlog.get_logger('attendance_system.security')
        self.attendance_logger = structlog.get_logger('attendance_system.attendance')
        self.accounts_logger = structlog.get_logger('attendance_system.accounts')
        self.system_logger = structlog.get_logger('attendance_system.system')
        # Logger général utilisé pour les messages applicatifs génériques
        # (utilisé par le middleware et autres composants)
        self.general_logger = structlog.get_logger('attendance_system.general')
    
    # ===================================================================
    # LOGGING SÉCURITÉ
    # ===================================================================
    
    def log_login_attempt(self, username: str, ip_address: str, success: bool, 
                          user_agent: str = None, reason: str = None):
        """
        Log une tentative de connexion.
        
        Args:
            username: Nom d'utilisateur ou ID employé
            ip_address: Adresse IP de la requête
            success: True si connexion réussie
            user_agent: User-Agent du navigateur
            reason: Raison de l'échec si applicable
        """
        self.security_logger.info(
            "Tentative de connexion",
            username=username,
            ip_address=ip_address,
            success=success,
            user_agent=user_agent,
            reason=reason,
            event_type="authentication"
        )
    
    def log_permission_denied(self, user: User, resource: str, action: str, 
                             ip_address: str = None):
        """
        Log un accès refusé.
        
        Args:
            user: Utilisateur qui a tenté l'accès
            resource: Ressource demandée
            action: Action tentée
            ip_address: Adresse IP
        """
        self.security_logger.warning(
            "Accès refusé",
            user_id=user.id,
            username=user.username,
            resource=resource,
            action=action,
            ip_address=ip_address,
            event_type="authorization"
        )
    
    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str, 
                               limit: str, user: User = None):
        """
        Log un dépassement de limite de taux.
        
        Args:
            ip_address: Adresse IP
            endpoint: Endpoint concerné
            limit: Limite dépassée
            user: Utilisateur si authentifié
        """
        self.security_logger.warning(
            "Limite de taux dépassée",
            ip_address=ip_address,
            endpoint=endpoint,
            limit=limit,
            user_id=user.id if user else None,
            event_type="rate_limit"
        )
    
    # ===================================================================
    # LOGGING POINTAGE
    # ===================================================================
    
    def log_punch_attempt(self, user: User, punch_type: str, latitude: float, 
                          longitude: float, accuracy: float, success: bool,
                          reason: str = None, distance: float = None):
        """
        Log une tentative de pointage.
        
        Args:
            user: Utilisateur qui pointe
            punch_type: Type de pointage (in/out)
            latitude: Latitude GPS
            longitude: Longitude GPS
            accuracy: Précision GPS
            success: True si pointage réussi
            reason: Raison de l'échec si applicable
            distance: Distance du site si calculée
        """
        # Récupération sécurisée de l'employee_id
        employee_id = None
        try:
            if hasattr(user, 'employee_profile') and user.employee_profile:
                employee_id = user.employee_profile.employee_id
        except:
            pass
            
        self.attendance_logger.info(
            "Tentative de pointage",
            user_id=user.id,
            employee_id=employee_id,
            punch_type=punch_type,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            success=success,
            reason=reason,
            distance_from_site=distance,
            event_type="punch_attempt"
        )
    
    def log_punch_created(self, attendance_id: int, user: User, punch_type: str,
                         worked_hours: float = None):
        """
        Log un pointage créé avec succès.
        
        Args:
            attendance_id: ID du pointage créé
            user: Utilisateur
            punch_type: Type de pointage
            worked_hours: Heures travaillées si calculées
        """
        # Récupération sécurisée de l'employee_id
        employee_id = None
        try:
            if hasattr(user, 'employee_profile') and user.employee_profile:
                employee_id = user.employee_profile.employee_id
        except:
            pass
            
        self.attendance_logger.info(
            "Pointage créé",
            attendance_id=attendance_id,
            user_id=user.id,
            employee_id=employee_id,
            punch_type=punch_type,
            worked_hours=worked_hours,
            event_type="punch_created"
        )
    
    def log_anomaly_detected(self, attendance_id: int, anomaly_type: str, 
                           description: str, user: User):
        """
        Log une anomalie détectée.
        
        Args:
            attendance_id: ID du pointage concerné
            anomaly_type: Type d'anomalie
            description: Description de l'anomalie
            user: Utilisateur concerné
        """
        self.attendance_logger.warning(
            "Anomalie détectée",
            attendance_id=attendance_id,
            user_id=user.id,
            employee_id=getattr(user.employee_profile, 'employee_id', None),
            anomaly_type=anomaly_type,
            description=description,
            event_type="anomaly"
        )
    
    # ===================================================================
    # LOGGING COMPTES
    # ===================================================================
    
    def log_user_created(self, user: User, created_by: User, 
                        employee_id: str = None):
        """
        Log la création d'un utilisateur.
        
        Args:
            user: Utilisateur créé
            created_by: Utilisateur qui a créé le compte
            employee_id: ID employé généré
        """
        self.accounts_logger.info(
            "Utilisateur créé",
            user_id=user.id,
            username=user.username,
            email=user.email,
            employee_id=employee_id,
            created_by_id=created_by.id,
            created_by_username=created_by.username,
            event_type="user_creation"
        )
    
    def log_password_changed(self, user: User, changed_by: User = None):
        """
        Log un changement de mot de passe.
        
        Args:
            user: Utilisateur dont le mot de passe a changé
            changed_by: Utilisateur qui a effectué le changement (si admin)
        """
        self.accounts_logger.info(
            "Mot de passe changé",
            user_id=user.id,
            username=user.username,
            changed_by_id=changed_by.id if changed_by else user.id,
            changed_by_username=changed_by.username if changed_by else user.username,
            event_type="password_change"
        )
    
    # ===================================================================
    # LOGGING SYSTÈME
    # ===================================================================
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                  user: User = None):
        """
        Log une erreur système.
        
        Args:
            error: Exception levée
            context: Contexte supplémentaire
            user: Utilisateur concerné si applicable
        """
        self.system_logger.error(
            "Erreur système",
            error_type=type(error).__name__,
            error_message=str(error),
            user_id=user.id if user else None,
            context=context or {},
            event_type="system_error"
        )
    
    def log_performance(self, operation: str, duration_ms: float, 
                       user: User = None, **kwargs):
        """
        Log une métrique de performance.
        
        Args:
            operation: Nom de l'opération
            duration_ms: Durée en millisecondes
            user: Utilisateur concerné
            **kwargs: Métriques supplémentaires
        """
        self.system_logger.info(
            "Métrique de performance",
            operation=operation,
            duration_ms=duration_ms,
            user_id=user.id if user else None,
            **kwargs,
            event_type="performance"
        )

    def log_error(self, exception: Exception, context: dict = None, 
                  error_type: str = "unknown", severity: str = "medium"):
        """
        Log une erreur système avec contexte complet.
        
        Args:
            exception: Exception à logger
            context: Contexte de l'erreur
            error_type: Type d'erreur
            severity: Sévérité de l'erreur
        """
        error_context = context or {}
        error_context.update({
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'error_type': error_type,
            'severity': severity
        })
        
        # Log selon la sévérité
        if severity == "critical":
            self.security_logger.critical(
                "Erreur critique",
                **error_context,
                event_type="critical_error"
            )
        elif severity == "high":
            self.security_logger.error(
                "Erreur importante",
                **error_context,
                event_type="high_error"
            )
        else:
            self.accounts_logger.warning(
                "Erreur système",
                **error_context,
                event_type="system_error"
            )

    def _get_timestamp(self):
        """Retourne un timestamp ISO pour les réponses d'erreur."""
        from datetime import datetime
        return datetime.now().isoformat()


# Instance globale du logger structuré
structured_logger = StructuredLogger()
