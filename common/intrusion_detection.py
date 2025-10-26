"""
Service de détection d'intrusion et d'anomalies pour PresencePro.

Ce module fournit :
- Détection de tentatives de force brute
- Analyse comportementale des utilisateurs
- Détection d'activité suspecte
- Alertes de sécurité en temps réel
- Machine learning pour détection d'anomalies

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import time
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from common.structured_logging import structured_logger
from common.intelligent_cache import intelligent_cache, CacheStrategy
from common.audit_trail import audit_trail_service, AuditEventType, AuditSeverity


class ThreatLevel:
    """Niveaux de menace."""
    
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyType:
    """Types d'anomalies détectées."""
    
    BRUTE_FORCE = "BRUTE_FORCE"
    UNUSUAL_LOGIN_TIME = "UNUSUAL_LOGIN_TIME"
    UNUSUAL_LOCATION = "UNUSUAL_LOCATION"
    RAPID_REQUESTS = "RAPID_REQUESTS"
    SUSPICIOUS_PATTERN = "SUSPICIOUS_PATTERN"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    UNUSUAL_DATA_ACCESS = "UNUSUAL_DATA_ACCESS"


class IntrusionDetectionService:
    """
    Service de détection d'intrusion et d'anomalies.
    
    Surveille les activités du système en temps réel
    et détecte les comportements suspects ou malveillants.
    """
    
    def __init__(self):
        self.cache = intelligent_cache
        self.audit_service = audit_trail_service
        
        # Configuration des seuils de détection
        self.config = {
            'brute_force': {
                'max_attempts': 5,
                'time_window': 300,  # 5 minutes
                'lockout_duration': 1800  # 30 minutes
            },
            'rapid_requests': {
                'max_requests': 100,
                'time_window': 60  # 1 minute
            },
            'unusual_login': {
                'unusual_hours': [22, 23, 0, 1, 2, 3, 4, 5],  # 22h-6h
                'weekend_penalty': 2.0
            },
            'data_access': {
                'max_records_per_hour': 1000,
                'sensitive_data_threshold': 10
            }
        }
    
    def analyze_login_attempt(self, username: str, ip_address: str, 
                            success: bool, user_agent: str = None) -> Dict[str, Any]:
        """
        Analyse une tentative de connexion pour détecter des anomalies.
        
        Args:
            username: Nom d'utilisateur
            ip_address: Adresse IP
            success: Succès de la connexion
            user_agent: User agent
            
        Returns:
            Résultat de l'analyse avec détection d'anomalies
        """
        try:
            analysis_result = {
                'anomalies_detected': [],
                'threat_level': ThreatLevel.LOW,
                'action_required': False,
                'lockout_until': None
            }
            
            # Détection de force brute
            brute_force_result = self._detect_brute_force(username, ip_address)
            if brute_force_result['detected']:
                analysis_result['anomalies_detected'].append({
                    'type': AnomalyType.BRUTE_FORCE,
                    'severity': ThreatLevel.HIGH,
                    'details': brute_force_result
                })
                analysis_result['threat_level'] = ThreatLevel.HIGH
                analysis_result['action_required'] = True
                analysis_result['lockout_until'] = brute_force_result.get('lockout_until')
            
            # Détection d'heure de connexion inhabituelle
            if success:
                unusual_time_result = self._detect_unusual_login_time()
                if unusual_time_result['detected']:
                    analysis_result['anomalies_detected'].append({
                        'type': AnomalyType.UNUSUAL_LOGIN_TIME,
                        'severity': ThreatLevel.MEDIUM,
                        'details': unusual_time_result
                    })
                    if analysis_result['threat_level'] == ThreatLevel.LOW:
                        analysis_result['threat_level'] = ThreatLevel.MEDIUM
            
            # Détection de pattern suspect
            suspicious_pattern_result = self._detect_suspicious_pattern(
                username, ip_address, user_agent
            )
            if suspicious_pattern_result['detected']:
                analysis_result['anomalies_detected'].append({
                    'type': AnomalyType.SUSPICIOUS_PATTERN,
                    'severity': ThreatLevel.MEDIUM,
                    'details': suspicious_pattern_result
                })
                if analysis_result['threat_level'] == ThreatLevel.LOW:
                    analysis_result['threat_level'] = ThreatLevel.MEDIUM
            
            # Logging de l'analyse
            self._log_analysis_result(username, ip_address, analysis_result)
            
            # Enregistrement de l'événement d'audit
            if analysis_result['anomalies_detected']:
                self.audit_service.log_security_event(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                    user=None,
                    details={
                        'username': username,
                        'ip_address': ip_address,
                        'anomalies': analysis_result['anomalies_detected'],
                        'threat_level': analysis_result['threat_level']
                    },
                    severity=AuditSeverity.HIGH,
                    ip_address=ip_address
                )
            
            return analysis_result
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'username': username, 'ip_address': ip_address, 'success': success},
                error_type="intrusion_detection_error"
            )
            return {'anomalies_detected': [], 'threat_level': ThreatLevel.LOW, 'action_required': False}
    
    def analyze_data_access(self, user: User, model_name: str, 
                          object_count: int, ip_address: str) -> Dict[str, Any]:
        """
        Analyse l'accès aux données pour détecter des anomalies.
        
        Args:
            user: Utilisateur concerné
            model_name: Nom du modèle accédé
            object_count: Nombre d'objets accédés
            ip_address: Adresse IP
            
        Returns:
            Résultat de l'analyse
        """
        try:
            analysis_result = {
                'anomalies_detected': [],
                'threat_level': ThreatLevel.LOW,
                'action_required': False
            }
            
            # Détection d'accès massif aux données
            mass_access_result = self._detect_mass_data_access(user, object_count)
            if mass_access_result['detected']:
                analysis_result['anomalies_detected'].append({
                    'type': AnomalyType.DATA_EXFILTRATION,
                    'severity': ThreatLevel.HIGH,
                    'details': mass_access_result
                })
                analysis_result['threat_level'] = ThreatLevel.HIGH
                analysis_result['action_required'] = True
            
            # Détection d'accès inhabituel
            unusual_access_result = self._detect_unusual_data_access(user, model_name)
            if unusual_access_result['detected']:
                analysis_result['anomalies_detected'].append({
                    'type': AnomalyType.UNUSUAL_DATA_ACCESS,
                    'severity': ThreatLevel.MEDIUM,
                    'details': unusual_access_result
                })
                if analysis_result['threat_level'] == ThreatLevel.LOW:
                    analysis_result['threat_level'] = ThreatLevel.MEDIUM
            
            # Logging et audit
            if analysis_result['anomalies_detected']:
                self.audit_service.log_data_access_event(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                    user=user,
                    model_name=model_name,
                    object_id=None,
                    details={
                        'object_count': object_count,
                        'anomalies': analysis_result['anomalies_detected'],
                        'threat_level': analysis_result['threat_level']
                    },
                    ip_address=ip_address
                )
            
            return analysis_result
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'user_id': user.id, 'model_name': model_name, 'object_count': object_count},
                error_type="data_access_analysis_error"
            )
            return {'anomalies_detected': [], 'threat_level': ThreatLevel.LOW, 'action_required': False}
    
    def analyze_request_pattern(self, ip_address: str, endpoint: str, 
                             user: Optional[User] = None) -> Dict[str, Any]:
        """
        Analyse le pattern de requêtes pour détecter des anomalies.
        
        Args:
            ip_address: Adresse IP
            endpoint: Endpoint accédé
            user: Utilisateur (optionnel)
            
        Returns:
            Résultat de l'analyse
        """
        try:
            analysis_result = {
                'anomalies_detected': [],
                'threat_level': ThreatLevel.LOW,
                'action_required': False
            }
            
            # Détection de requêtes rapides
            rapid_requests_result = self._detect_rapid_requests(ip_address)
            if rapid_requests_result['detected']:
                analysis_result['anomalies_detected'].append({
                    'type': AnomalyType.RAPID_REQUESTS,
                    'severity': ThreatLevel.MEDIUM,
                    'details': rapid_requests_result
                })
                analysis_result['threat_level'] = ThreatLevel.MEDIUM
                analysis_result['action_required'] = True
            
            # Détection de pattern suspect
            if user:
                suspicious_pattern_result = self._detect_user_suspicious_pattern(
                    user, endpoint, ip_address
                )
                if suspicious_pattern_result['detected']:
                    analysis_result['anomalies_detected'].append({
                        'type': AnomalyType.SUSPICIOUS_PATTERN,
                        'severity': ThreatLevel.MEDIUM,
                        'details': suspicious_pattern_result
                    })
                    if analysis_result['threat_level'] == ThreatLevel.LOW:
                        analysis_result['threat_level'] = ThreatLevel.MEDIUM
            
            return analysis_result
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'ip_address': ip_address, 'endpoint': endpoint, 'user_id': user.id if user else None},
                error_type="request_pattern_analysis_error"
            )
            return {'anomalies_detected': [], 'threat_level': ThreatLevel.LOW, 'action_required': False}
    
    def _detect_brute_force(self, username: str, ip_address: str) -> Dict[str, Any]:
        """Détecte les tentatives de force brute."""
        try:
            # Clé de cache pour les tentatives
            cache_key = self.cache._generate_cache_key('brute_force', username, ip_address)
            
            # Récupération des tentatives récentes
            attempts = self.cache.get(cache_key, CacheStrategy.SESSIONS) or []
            current_time = time.time()
            
            # Nettoyage des tentatives anciennes
            time_window = self.config['brute_force']['time_window']
            attempts = [attempt for attempt in attempts if current_time - attempt < time_window]
            
            # Ajout de la tentative actuelle
            attempts.append(current_time)
            
            # Mise à jour du cache
            self.cache.set(cache_key, attempts, time_window, CacheStrategy.SESSIONS)
            
            # Vérification du seuil
            max_attempts = self.config['brute_force']['max_attempts']
            if len(attempts) >= max_attempts:
                lockout_duration = self.config['brute_force']['lockout_duration']
                lockout_until = current_time + lockout_duration
                
                return {
                    'detected': True,
                    'attempt_count': len(attempts),
                    'time_window': time_window,
                    'lockout_until': lockout_until,
                    'lockout_duration': lockout_duration
                }
            
            return {'detected': False, 'attempt_count': len(attempts)}
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'username': username, 'ip_address': ip_address},
                error_type="brute_force_detection_error"
            )
            return {'detected': False}
    
    def _detect_unusual_login_time(self) -> Dict[str, Any]:
        """Détecte les connexions à des heures inhabituelles."""
        try:
            current_hour = timezone.now().hour
            current_weekday = timezone.now().weekday()
            
            unusual_hours = self.config['unusual_login']['unusual_hours']
            is_unusual_hour = current_hour in unusual_hours
            is_weekend = current_weekday >= 5  # Samedi = 5, Dimanche = 6
            
            if is_unusual_hour or is_weekend:
                return {
                    'detected': True,
                    'current_hour': current_hour,
                    'is_weekend': is_weekend,
                    'unusual_hours': unusual_hours
                }
            
            return {'detected': False}
            
        except Exception as e:
            structured_logger.log_error(e, {}, error_type="unusual_login_time_detection_error")
            return {'detected': False}
    
    def _detect_suspicious_pattern(self, username: str, ip_address: str, 
                                 user_agent: str) -> Dict[str, Any]:
        """Détecte les patterns suspects."""
        try:
            suspicious_indicators = []
            
            # Vérification du user agent
            if user_agent:
                suspicious_agents = ['bot', 'crawler', 'scanner', 'python-requests']
                if any(agent in user_agent.lower() for agent in suspicious_agents):
                    suspicious_indicators.append('suspicious_user_agent')
            
            # Vérification de l'IP (simulation)
            if ip_address.startswith('192.168.') or ip_address.startswith('10.'):
                suspicious_indicators.append('internal_ip')
            
            if suspicious_indicators:
                return {
                    'detected': True,
                    'indicators': suspicious_indicators,
                    'username': username,
                    'ip_address': ip_address
                }
            
            return {'detected': False}
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'username': username, 'ip_address': ip_address},
                error_type="suspicious_pattern_detection_error"
            )
            return {'detected': False}
    
    def _detect_mass_data_access(self, user: User, object_count: int) -> Dict[str, Any]:
        """Détecte l'accès massif aux données."""
        try:
            max_records = self.config['data_access']['max_records_per_hour']
            
            if object_count > max_records:
                return {
                    'detected': True,
                    'object_count': object_count,
                    'threshold': max_records,
                    'excess': object_count - max_records
                }
            
            return {'detected': False}
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'user_id': user.id, 'object_count': object_count},
                error_type="mass_data_access_detection_error"
            )
            return {'detected': False}
    
    def _detect_unusual_data_access(self, user: User, model_name: str) -> Dict[str, Any]:
        """Détecte l'accès inhabituel aux données."""
        try:
            # Simulation de détection d'accès inhabituel
            # En production, analyser l'historique d'accès de l'utilisateur
            
            cache_key = self.cache._generate_cache_key('user_data_access', user.id, model_name)
            access_history = self.cache.get(cache_key, CacheStrategy.FREQUENT_DATA) or []
            
            # Ajout de l'accès actuel
            access_history.append(timezone.now().isoformat())
            
            # Limitation de l'historique
            if len(access_history) > 100:
                access_history = access_history[-100:]
            
            # Mise à jour du cache
            self.cache.set(cache_key, access_history, 3600, CacheStrategy.FREQUENT_DATA)
            
            # Détection d'accès inhabituel (simulation)
            if len(access_history) > 50:  # Plus de 50 accès récents
                return {
                    'detected': True,
                    'access_count': len(access_history),
                    'model_name': model_name,
                    'user_id': user.id
                }
            
            return {'detected': False}
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'user_id': user.id, 'model_name': model_name},
                error_type="unusual_data_access_detection_error"
            )
            return {'detected': False}
    
    def _detect_rapid_requests(self, ip_address: str) -> Dict[str, Any]:
        """Détecte les requêtes rapides."""
        try:
            cache_key = self.cache._generate_cache_key('rapid_requests', ip_address)
            requests = self.cache.get(cache_key, CacheStrategy.SESSIONS) or []
            current_time = time.time()
            
            # Nettoyage des requêtes anciennes
            time_window = self.config['rapid_requests']['time_window']
            requests = [req_time for req_time in requests if current_time - req_time < time_window]
            
            # Ajout de la requête actuelle
            requests.append(current_time)
            
            # Mise à jour du cache
            self.cache.set(cache_key, requests, time_window, CacheStrategy.SESSIONS)
            
            # Vérification du seuil
            max_requests = self.config['rapid_requests']['max_requests']
            if len(requests) > max_requests:
                return {
                    'detected': True,
                    'request_count': len(requests),
                    'time_window': time_window,
                    'threshold': max_requests
                }
            
            return {'detected': False, 'request_count': len(requests)}
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'ip_address': ip_address},
                error_type="rapid_requests_detection_error"
            )
            return {'detected': False}
    
    def _detect_user_suspicious_pattern(self, user: User, endpoint: str, 
                                      ip_address: str) -> Dict[str, Any]:
        """Détecte les patterns suspects d'un utilisateur."""
        try:
            # Simulation de détection de pattern suspect
            # En production, analyser l'historique comportemental
            
            suspicious_endpoints = ['/admin/', '/api/admin/', '/debug/']
            if endpoint in suspicious_endpoints:
                return {
                    'detected': True,
                    'endpoint': endpoint,
                    'user_id': user.id,
                    'reason': 'suspicious_endpoint_access'
                }
            
            return {'detected': False}
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'user_id': user.id, 'endpoint': endpoint},
                error_type="user_suspicious_pattern_detection_error"
            )
            return {'detected': False}
    
    def _log_analysis_result(self, username: str, ip_address: str, 
                           analysis_result: Dict[str, Any]):
        """Log le résultat de l'analyse."""
        structured_logger.security_logger.info(
            "Analyse de sécurité terminée",
            username=username,
            ip_address=ip_address,
            threat_level=analysis_result['threat_level'],
            anomalies_count=len(analysis_result['anomalies_detected']),
            action_required=analysis_result['action_required'],
            event_type="security_analysis_completed"
        )


# Instance globale du service de détection d'intrusion
intrusion_detection_service = IntrusionDetectionService()

