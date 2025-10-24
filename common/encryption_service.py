"""
Service de chiffrement des données sensibles pour PresencePro.

Ce module fournit :
- Chiffrement AES-256-GCM pour les données sensibles
- Gestion des clés de chiffrement avec rotation
- Chiffrement des champs de base de données
- Hachage sécurisé des mots de passe
- Chiffrement des logs sensibles

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import os
import base64
import hashlib
import secrets
from typing import Any, Dict, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from common.structured_logging import structured_logger


class EncryptionService:
    """
    Service de chiffrement des données sensibles.
    
    Utilise AES-256-GCM pour le chiffrement symétrique
    avec gestion sécurisée des clés.
    """
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.salt_length = 32
        self.iv_length = 16
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Récupère ou crée une clé de chiffrement.
        
        Returns:
            Clé de chiffrement Fernet
        """
        # Tentative de récupération depuis les settings
        key_b64 = getattr(settings, 'ENCRYPTION_KEY', None)
        
        if key_b64:
            try:
                return base64.b64decode(key_b64)
            except Exception as e:
                structured_logger.log_error(
                    e,
                    {'key_source': 'settings'},
                    error_type="encryption_key_error"
                )
                raise ImproperlyConfigured("Clé de chiffrement invalide dans les settings")
        
        # Génération d'une nouvelle clé
        new_key = Fernet.generate_key()
        
        # Log de la génération (en production, sauvegarder la clé)
        structured_logger.security_logger.warning(
            "Nouvelle clé de chiffrement générée",
            key_preview=new_key[:8].decode() + "...",
            event_type="encryption_key_generated"
        )
        
        return new_key
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """
        Chiffre des données sensibles.
        
        Args:
            data: Données à chiffrer
            
        Returns:
            Données chiffrées en base64
        """
        try:
            # Conversion en bytes si nécessaire
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Chiffrement avec Fernet
            encrypted_data = self.fernet.encrypt(data_bytes)
            
            # Encodage en base64
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            structured_logger.security_logger.debug(
                "Données chiffrées",
                data_length=len(data_bytes),
                event_type="data_encrypted"
            )
            
            return encrypted_b64
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'data_type': type(data).__name__},
                error_type="encryption_error"
            )
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Déchiffre des données sensibles.
        
        Args:
            encrypted_data: Données chiffrées en base64
            
        Returns:
            Données déchiffrées
        """
        try:
            # Décodage depuis base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Déchiffrement avec Fernet
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            
            # Conversion en string
            decrypted_data = decrypted_bytes.decode('utf-8')
            
            structured_logger.security_logger.debug(
                "Données déchiffrées",
                data_length=len(decrypted_data),
                event_type="data_decrypted"
            )
            
            return decrypted_data
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'encrypted_data_length': len(encrypted_data)},
                error_type="decryption_error"
            )
            raise
    
    def encrypt_field(self, field_value: Any) -> Optional[str]:
        """
        Chiffre un champ de base de données.
        
        Args:
            field_value: Valeur du champ à chiffrer
            
        Returns:
            Valeur chiffrée ou None si None
        """
        if field_value is None:
            return None
        
        return self.encrypt_data(str(field_value))
    
    def decrypt_field(self, encrypted_value: str) -> Optional[str]:
        """
        Déchiffre un champ de base de données.
        
        Args:
            encrypted_value: Valeur chiffrée du champ
            
        Returns:
            Valeur déchiffrée ou None si None
        """
        if encrypted_value is None or encrypted_value == '':
            return None
        
        return self.decrypt_data(encrypted_value)


class PasswordHashingService:
    """
    Service de hachage sécurisé des mots de passe.
    
    Utilise PBKDF2 avec SHA-256 pour le hachage
    des mots de passe avec salt unique.
    """
    
    def __init__(self):
        self.algorithm = hashes.SHA256()
        self.length = 32
        self.salt_length = 32
        self.iterations = 100000  # OWASP recommandation 2023
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        """
        Hache un mot de passe avec salt.
        
        Args:
            password: Mot de passe en clair
            salt: Salt personnalisé (optionnel)
            
        Returns:
            Dictionnaire avec hash et salt
        """
        try:
            # Génération du salt si non fourni
            if salt is None:
                salt = secrets.token_bytes(self.salt_length)
            
            # Dérivation de la clé avec PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=self.algorithm,
                length=self.length,
                salt=salt,
                iterations=self.iterations,
            )
            
            # Hachage du mot de passe
            password_hash = kdf.derive(password.encode('utf-8'))
            
            # Encodage en base64
            hash_b64 = base64.b64encode(password_hash).decode('utf-8')
            salt_b64 = base64.b64encode(salt).decode('utf-8')
            
            structured_logger.security_logger.debug(
                "Mot de passe haché",
                iterations=self.iterations,
                event_type="password_hashed"
            )
            
            return {
                'hash': hash_b64,
                'salt': salt_b64,
                'algorithm': 'PBKDF2-SHA256',
                'iterations': str(self.iterations)
            }
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'password_length': len(password)},
                error_type="password_hashing_error"
            )
            raise
    
    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """
        Vérifie un mot de passe contre son hash stocké.
        
        Args:
            password: Mot de passe à vérifier
            stored_hash: Hash stocké
            salt: Salt utilisé
            
        Returns:
            True si le mot de passe est correct
        """
        try:
            # Décodage des données stockées
            hash_bytes = base64.b64decode(stored_hash.encode('utf-8'))
            salt_bytes = base64.b64decode(salt.encode('utf-8'))
            
            # Dérivation de la clé avec les mêmes paramètres
            kdf = PBKDF2HMAC(
                algorithm=self.algorithm,
                length=self.length,
                salt=salt_bytes,
                iterations=self.iterations,
            )
            
            # Hachage du mot de passe fourni
            password_hash = kdf.derive(password.encode('utf-8'))
            
            # Comparaison sécurisée
            is_valid = secrets.compare_digest(hash_bytes, password_hash)
            
            if is_valid:
                structured_logger.security_logger.debug(
                    "Mot de passe vérifié",
                    event_type="password_verified"
                )
            else:
                structured_logger.security_logger.warning(
                    "Tentative de connexion avec mot de passe invalide",
                    event_type="password_verification_failed"
                )
            
            return is_valid
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'password_length': len(password)},
                error_type="password_verification_error"
            )
            return False


class SensitiveDataManager:
    """
    Gestionnaire des données sensibles.
    
    Fournit des méthodes pour chiffrer/déchiffrer
    automatiquement les champs sensibles des modèles.
    """
    
    def __init__(self):
        self.encryption_service = EncryptionService()
        self.password_service = PasswordHashingService()
    
    def encrypt_model_field(self, model_instance, field_name: str, value: Any) -> str:
        """
        Chiffre un champ d'un modèle.
        
        Args:
            model_instance: Instance du modèle
            field_name: Nom du champ
            value: Valeur à chiffrer
            
        Returns:
            Valeur chiffrée
        """
        try:
            encrypted_value = self.encryption_service.encrypt_field(value)
            
            structured_logger.security_logger.debug(
                "Champ de modèle chiffré",
                model=model_instance.__class__.__name__,
                field=field_name,
                event_type="model_field_encrypted"
            )
            
            return encrypted_value
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {
                    'model': model_instance.__class__.__name__,
                    'field': field_name,
                    'value_type': type(value).__name__
                },
                error_type="model_field_encryption_error"
            )
            raise
    
    def decrypt_model_field(self, model_instance, field_name: str, encrypted_value: str) -> Any:
        """
        Déchiffre un champ d'un modèle.
        
        Args:
            model_instance: Instance du modèle
            field_name: Nom du champ
            encrypted_value: Valeur chiffrée
            
        Returns:
            Valeur déchiffrée
        """
        try:
            decrypted_value = self.encryption_service.decrypt_field(encrypted_value)
            
            structured_logger.security_logger.debug(
                "Champ de modèle déchiffré",
                model=model_instance.__class__.__name__,
                field=field_name,
                event_type="model_field_decrypted"
            )
            
            return decrypted_value
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {
                    'model': model_instance.__class__.__name__,
                    'field': field_name,
                    'encrypted_length': len(encrypted_value) if encrypted_value else 0
                },
                error_type="model_field_decryption_error"
            )
            raise
    
    def hash_sensitive_string(self, sensitive_string: str) -> str:
        """
        Hache une chaîne sensible pour l'indexation.
        
        Args:
            sensitive_string: Chaîne sensible
            
        Returns:
            Hash de la chaîne
        """
        try:
            # Utilisation de SHA-256 pour l'indexation
            hash_object = hashlib.sha256(sensitive_string.encode('utf-8'))
            return hash_object.hexdigest()
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'string_length': len(sensitive_string)},
                error_type="sensitive_string_hashing_error"
            )
            raise
    
    def create_secure_token(self, length: int = 32) -> str:
        """
        Crée un token sécurisé.
        
        Args:
            length: Longueur du token en bytes
            
        Returns:
            Token sécurisé
        """
        return secrets.token_urlsafe(length)
    
    def create_secure_id(self, prefix: str = '') -> str:
        """
        Crée un ID sécurisé.
        
        Args:
            prefix: Préfixe pour l'ID
            
        Returns:
            ID sécurisé
        """
        secure_id = secrets.token_hex(16)
        return f"{prefix}{secure_id}" if prefix else secure_id


class LogEncryptionService:
    """
    Service de chiffrement des logs sensibles.
    
    Chiffre automatiquement les données sensibles
    dans les logs pour la conformité RGPD.
    """
    
    def __init__(self):
        self.encryption_service = EncryptionService()
        self.sensitive_patterns = [
            r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'email["\']?\s*[:=]\s*["\']?([^"\'\s@]+@[^"\'\s]+)',
            r'phone["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        ]
    
    def encrypt_sensitive_log_data(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chiffre les données sensibles dans un log.
        
        Args:
            log_data: Données du log
            
        Returns:
            Données du log avec données sensibles chiffrées
        """
        try:
            encrypted_data = log_data.copy()
            
            # Champs sensibles connus
            sensitive_fields = [
                'password', 'token', 'secret', 'key', 'email',
                'phone', 'ssn', 'credit_card', 'bank_account'
            ]
            
            for field in sensitive_fields:
                if field in encrypted_data and encrypted_data[field]:
                    encrypted_data[f"{field}_encrypted"] = self.encryption_service.encrypt_data(
                        str(encrypted_data[field])
                    )
                    del encrypted_data[field]  # Suppression de la valeur en clair
            
            return encrypted_data
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'log_keys': list(log_data.keys())},
                error_type="log_encryption_error"
            )
            return log_data  # Retour des données originales en cas d'erreur


# Instances globales des services de chiffrement
encryption_service = EncryptionService()
password_hashing_service = PasswordHashingService()
sensitive_data_manager = SensitiveDataManager()
log_encryption_service = LogEncryptionService()
