"""
Service d'authentification à deux facteurs (2FA) pour PresencePro.

Ce module fournit :
- Génération de codes TOTP (Time-based One-Time Password)
- QR codes pour configuration des applications d'authentification
- Backup codes pour récupération d'accès
- Validation des codes 2FA
- Gestion des sessions sécurisées

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Dict, List, Optional, Tuple
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from common.structured_logging import structured_logger
from common.intelligent_cache import intelligent_cache, CacheStrategy


class TwoFactorAuthService:
    """
    Service d'authentification à deux facteurs.
    
    Implémente TOTP (RFC 6238) pour la génération de codes
    d'authentification basés sur le temps.
    """
    
    def __init__(self):
        self.cache = intelligent_cache
        self.totp_window = 1  # Fenêtre de tolérance pour les codes
        self.backup_codes_count = 10
        self.backup_code_length = 8
    
    def generate_secret_key(self, user: User) -> str:
        """
        Génère une clé secrète unique pour l'utilisateur.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            Clé secrète TOTP
        """
        # Génération d'une clé secrète basée sur l'utilisateur
        user_data = f"{user.id}:{user.username}:{user.email}"
        seed = hashlib.sha256(user_data.encode()).hexdigest()[:32]
        
        # Génération d'une clé secrète TOTP
        secret_key = pyotp.random_base32()
        
        # Stockage temporaire en cache pour configuration
        cache_key = self.cache._generate_cache_key('2fa_setup', user.id)
        self.cache.set(cache_key, secret_key, 300, CacheStrategy.SESSIONS)  # 5 minutes
        
        structured_logger.security_logger.info(
            "Clé 2FA générée",
            user_id=user.id,
            event_type="2fa_key_generated"
        )
        
        return secret_key
    
    def generate_qr_code(self, user: User, secret_key: str) -> str:
        """
        Génère un QR code pour configuration de l'application d'authentification.
        
        Args:
            user: Utilisateur Django
            secret_key: Clé secrète TOTP
            
        Returns:
            QR code en base64
        """
        # Configuration du TOTP
        totp = pyotp.TOTP(secret_key)
        
        # URL de configuration pour l'application d'authentification
        app_name = getattr(settings, 'TWO_FACTOR_APP_NAME', 'PresencePro')
        issuer = getattr(settings, 'TWO_FACTOR_ISSUER', 'PresencePro System')
        
        provisioning_uri = totp.provisioning_uri(
            name=f"{app_name} ({user.username})",
            issuer_name=issuer
        )
        
        # Génération du QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Création de l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Conversion en base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        structured_logger.security_logger.info(
            "QR code 2FA généré",
            user_id=user.id,
            event_type="2fa_qr_generated"
        )
        
        return qr_code_base64
    
    def generate_backup_codes(self, user: User) -> List[str]:
        """
        Génère des codes de sauvegarde pour l'utilisateur.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            Liste des codes de sauvegarde
        """
        backup_codes = []
        
        for _ in range(self.backup_codes_count):
            # Génération d'un code de sauvegarde sécurisé
            code = secrets.token_hex(self.backup_code_length // 2).upper()
            backup_codes.append(code)
        
        # Stockage des codes de sauvegarde (hashés)
        hashed_codes = [hashlib.sha256(code.encode()).hexdigest() for code in backup_codes]
        
        cache_key = self.cache._generate_cache_key('2fa_backup_codes', user.id)
        self.cache.set(cache_key, hashed_codes, 86400, CacheStrategy.SESSIONS)  # 24 heures
        
        structured_logger.security_logger.info(
            "Codes de sauvegarde 2FA générés",
            user_id=user.id,
            codes_count=len(backup_codes),
            event_type="2fa_backup_codes_generated"
        )
        
        return backup_codes
    
    def verify_totp_code(self, user: User, code: str, secret_key: str) -> bool:
        """
        Vérifie un code TOTP.
        
        Args:
            user: Utilisateur Django
            code: Code à vérifier
            secret_key: Clé secrète TOTP
            
        Returns:
            True si le code est valide
        """
        try:
            totp = pyotp.TOTP(secret_key)
            
            # Vérification du code avec fenêtre de tolérance
            is_valid = totp.verify(code, valid_window=self.totp_window)
            
            if is_valid:
                structured_logger.security_logger.info(
                    "Code 2FA TOTP vérifié avec succès",
                    user_id=user.id,
                    event_type="2fa_totp_verified"
                )
            else:
                structured_logger.security_logger.warning(
                    "Code 2FA TOTP invalide",
                    user_id=user.id,
                    event_type="2fa_totp_failed"
                )
            
            return is_valid
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'user_id': user.id, 'code_length': len(code)},
                error_type="2fa_verification_error"
            )
            return False
    
    def verify_backup_code(self, user: User, code: str) -> bool:
        """
        Vérifie un code de sauvegarde.
        
        Args:
            user: Utilisateur Django
            code: Code de sauvegarde à vérifier
            
        Returns:
            True si le code est valide
        """
        try:
            cache_key = self.cache._generate_cache_key('2fa_backup_codes', user.id)
            hashed_codes = self.cache.get(cache_key, CacheStrategy.SESSIONS)
            
            if not hashed_codes:
                return False
            
            # Hash du code fourni
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            
            # Vérification du code
            if code_hash in hashed_codes:
                # Suppression du code utilisé
                hashed_codes.remove(code_hash)
                self.cache.set(cache_key, hashed_codes, 86400, CacheStrategy.SESSIONS)
                
                structured_logger.security_logger.info(
                    "Code de sauvegarde 2FA utilisé",
                    user_id=user.id,
                    remaining_codes=len(hashed_codes),
                    event_type="2fa_backup_code_used"
                )
                
                return True
            else:
                structured_logger.security_logger.warning(
                    "Code de sauvegarde 2FA invalide",
                    user_id=user.id,
                    event_type="2fa_backup_code_failed"
                )
                
                return False
                
        except Exception as e:
            structured_logger.log_error(
                e,
                {'user_id': user.id},
                error_type="2fa_backup_verification_error"
            )
            return False
    
    def is_2fa_enabled(self, user: User) -> bool:
        """
        Vérifie si la 2FA est activée pour l'utilisateur.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            True si la 2FA est activée
        """
        cache_key = self.cache._generate_cache_key('2fa_enabled', user.id)
        return self.cache.get(cache_key, CacheStrategy.SESSIONS) is not None
    
    def enable_2fa(self, user: User, secret_key: str) -> bool:
        """
        Active la 2FA pour l'utilisateur.
        
        Args:
            user: Utilisateur Django
            secret_key: Clé secrète TOTP
            
        Returns:
            True si l'activation a réussi
        """
        try:
            # Stockage de la clé secrète (hashée)
            secret_hash = hashlib.sha256(secret_key.encode()).hexdigest()
            
            cache_key = self.cache._generate_cache_key('2fa_enabled', user.id)
            self.cache.set(cache_key, secret_hash, 86400 * 30, CacheStrategy.SESSIONS)  # 30 jours
            
            structured_logger.security_logger.info(
                "2FA activée",
                user_id=user.id,
                event_type="2fa_enabled"
            )
            
            return True
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'user_id': user.id},
                error_type="2fa_enable_error"
            )
            return False
    
    def disable_2fa(self, user: User) -> bool:
        """
        Désactive la 2FA pour l'utilisateur.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            True si la désactivation a réussi
        """
        try:
            # Suppression des données 2FA
            cache_key_enabled = self.cache._generate_cache_key('2fa_enabled', user.id)
            cache_key_backup = self.cache._generate_cache_key('2fa_backup_codes', user.id)
            
            self.cache.delete(cache_key_enabled, CacheStrategy.SESSIONS)
            self.cache.delete(cache_key_backup, CacheStrategy.SESSIONS)
            
            structured_logger.security_logger.info(
                "2FA désactivée",
                user_id=user.id,
                event_type="2fa_disabled"
            )
            
            return True
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'user_id': user.id},
                error_type="2fa_disable_error"
            )
            return False
    
    def get_remaining_backup_codes(self, user: User) -> int:
        """
        Retourne le nombre de codes de sauvegarde restants.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            Nombre de codes restants
        """
        cache_key = self.cache._generate_cache_key('2fa_backup_codes', user.id)
        hashed_codes = self.cache.get(cache_key, CacheStrategy.SESSIONS)
        
        return len(hashed_codes) if hashed_codes else 0


class SecureSessionManager:
    """
    Gestionnaire de sessions sécurisées.
    
    Gère les sessions avec rotation des tokens,
    détection d'anomalies et invalidation sécurisée.
    """
    
    def __init__(self):
        self.cache = intelligent_cache
        self.session_timeout = 3600  # 1 heure
        self.max_concurrent_sessions = 3
    
    def create_secure_session(self, user: User, request) -> str:
        """
        Crée une session sécurisée pour l'utilisateur.
        
        Args:
            user: Utilisateur Django
            request: Requête Django
            
        Returns:
            Token de session sécurisé
        """
        # Génération d'un token de session sécurisé
        session_token = secrets.token_urlsafe(32)
        
        # Métadonnées de session
        session_data = {
            'user_id': user.id,
            'created_at': timezone.now().isoformat(),
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'is_2fa_verified': False
        }
        
        # Stockage de la session
        cache_key = self.cache._generate_cache_key('secure_session', session_token)
        self.cache.set(cache_key, session_data, self.session_timeout, CacheStrategy.SESSIONS)
        
        # Gestion des sessions concurrentes
        self._manage_concurrent_sessions(user, session_token)
        
        structured_logger.security_logger.info(
            "Session sécurisée créée",
            user_id=user.id,
            session_token=session_token[:8] + "...",
            ip_address=session_data['ip_address'],
            event_type="secure_session_created"
        )
        
        return session_token
    
    def verify_session(self, session_token: str, request) -> Optional[Dict]:
        """
        Vérifie et retourne les données de session.
        
        Args:
            session_token: Token de session
            request: Requête Django
            
        Returns:
            Données de session ou None
        """
        cache_key = self.cache._generate_cache_key('secure_session', session_token)
        session_data = self.cache.get(cache_key, CacheStrategy.SESSIONS)
        
        if not session_data:
            return None
        
        # Vérification de l'IP (optionnel, peut être désactivé pour la mobilité)
        current_ip = self._get_client_ip(request)
        if session_data.get('ip_address') != current_ip:
            structured_logger.security_logger.warning(
                "Changement d'IP détecté",
                user_id=session_data.get('user_id'),
                original_ip=session_data.get('ip_address'),
                current_ip=current_ip,
                event_type="ip_change_detected"
            )
        
        return session_data
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalide une session.
        
        Args:
            session_token: Token de session
            
        Returns:
            True si l'invalidation a réussi
        """
        cache_key = self.cache._generate_cache_key('secure_session', session_token)
        result = self.cache.delete(cache_key, CacheStrategy.SESSIONS)
        
        if result:
            structured_logger.security_logger.info(
                "Session invalidée",
                session_token=session_token[:8] + "...",
                event_type="session_invalidated"
            )
        
        return result
    
    def _manage_concurrent_sessions(self, user: User, new_session_token: str):
        """
        Gère les sessions concurrentes de l'utilisateur.
        
        Args:
            user: Utilisateur Django
            new_session_token: Nouveau token de session
        """
        # Récupération des sessions existantes
        user_sessions_key = self.cache._generate_cache_key('user_sessions', user.id)
        user_sessions = self.cache.get(user_sessions_key, CacheStrategy.SESSIONS) or []
        
        # Ajout de la nouvelle session
        user_sessions.append(new_session_token)
        
        # Limitation du nombre de sessions
        if len(user_sessions) > self.max_concurrent_sessions:
            # Suppression des sessions les plus anciennes
            sessions_to_remove = user_sessions[:-self.max_concurrent_sessions]
            for old_token in sessions_to_remove:
                self.invalidate_session(old_token)
            
            user_sessions = user_sessions[-self.max_concurrent_sessions:]
        
        # Mise à jour de la liste des sessions
        self.cache.set(user_sessions_key, user_sessions, self.session_timeout, CacheStrategy.SESSIONS)
    
    def _get_client_ip(self, request) -> str:
        """Extrait l'IP réelle du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Instances globales des services de sécurité
two_factor_service = TwoFactorAuthService()
secure_session_manager = SecureSessionManager()

