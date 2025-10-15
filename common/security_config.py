"""
Utilitaires de configuration sécurisée pour le système de gestion de présence.

Ce module fournit des fonctions pour valider et sécuriser la configuration
de l'application selon les meilleures pratiques de sécurité.

Auteur: Système de Gestion de Présence
Version: 2.0 (Sécurisé)
"""

import os
import secrets
import string
from django.core.management.utils import get_random_secret_key
from django.core.exceptions import ImproperlyConfigured


class SecurityConfigValidator:
    """
    Validateur de configuration de sécurité.
    
    Respecte le Single Responsibility Principle en se concentrant
    uniquement sur la validation de la sécurité de la configuration.
    """
    
    @staticmethod
    def validate_secret_key(secret_key):
        """
        Valide que la SECRET_KEY est sécurisée.
        
        Args:
            secret_key (str): La clé secrète à valider
            
        Raises:
            ImproperlyConfigured: Si la clé n'est pas sécurisée
        """
        if not secret_key:
            raise ImproperlyConfigured(
                "SECRET_KEY est requise. Définissez-la dans votre fichier .env"
            )
        
        # Vérifications de sécurité
        insecure_keys = [
            'django-insecure-change-me-in-production',
            'your-secret-key-here',
            'change-me',
            'secret',
            'key',
        ]
        
        if secret_key.lower() in [key.lower() for key in insecure_keys]:
            raise ImproperlyConfigured(
                f"SECRET_KEY '{secret_key}' n'est pas sécurisée. "
                f"Générez une nouvelle clé avec: "
                f"python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
            )
        
        if len(secret_key) < 50:
            raise ImproperlyConfigured(
                f"SECRET_KEY trop courte ({len(secret_key)} caractères). "
                f"Utilisez au moins 50 caractères."
            )
    
    @staticmethod
    def validate_email_config(email_backend, email_host_user, email_host_password):
        """
        Valide la configuration email.
        
        Args:
            email_backend (str): Backend email configuré
            email_host_user (str): Utilisateur SMTP
            email_host_password (str): Mot de passe SMTP
        """
        if email_backend == 'django.core.mail.backends.smtp.EmailBackend':
            if not email_host_user or not email_host_password:
                print("⚠️  AVERTISSEMENT: Configuration email SMTP incomplète")
                print("📧 EMAIL_HOST_USER et EMAIL_HOST_PASSWORD requis pour SMTP")
                print("💡 Utilisez 'django.core.mail.backends.console.EmailBackend' pour le développement")
    
    @staticmethod
    def validate_allowed_hosts(allowed_hosts, debug=False):
        """
        Valide la configuration ALLOWED_HOSTS.
        
        Args:
            allowed_hosts (list): Liste des hosts autorisés
            debug (bool): Si DEBUG est activé
        """
        if not debug and ('*' in allowed_hosts or not allowed_hosts):
            raise ImproperlyConfigured(
                "ALLOWED_HOSTS ne peut pas contenir '*' ou être vide en production. "
                "Définissez les domaines autorisés dans ALLOWED_HOSTS."
            )
    
    @staticmethod
    def check_production_security(debug, secret_key, allowed_hosts):
        """
        Vérifie la configuration de sécurité pour la production.
        
        Args:
            debug (bool): État du mode DEBUG
            secret_key (str): Clé secrète
            allowed_hosts (list): Hosts autorisés
        """
        if not debug:  # Mode production
            print("🔒 VÉRIFICATION SÉCURITÉ PRODUCTION...")
            
            # Vérifications obligatoires
            SecurityConfigValidator.validate_secret_key(secret_key)
            SecurityConfigValidator.validate_allowed_hosts(allowed_hosts, debug)
            
            print("✅ Configuration de sécurité validée pour la production")
        else:
            print("🚧 MODE DÉVELOPPEMENT - Vérifications de sécurité allégées")


class SecureConfigGenerator:
    """
    Générateur de configuration sécurisée.
    
    Fournit des méthodes pour générer des configurations sécurisées.
    """
    
    @staticmethod
    def generate_secret_key():
        """
        Génère une SECRET_KEY sécurisée.
        
        Returns:
            str: Une clé secrète sécurisée de 50 caractères
        """
        return get_random_secret_key()
    
    @staticmethod
    def generate_password(length=12):
        """
        Génère un mot de passe sécurisé.
        
        Args:
            length (int): Longueur du mot de passe (minimum 8)
            
        Returns:
            str: Mot de passe sécurisé
        """
        if length < 8:
            length = 8
        
        # Caractères pour le mot de passe
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        
        # Générer un mot de passe sécurisé
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        # S'assurer qu'il contient au moins un de chaque type
        if not any(c.islower() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)
        
        return password
    
    @staticmethod
    def create_env_template():
        """
        Crée un template .env sécurisé.
        
        Returns:
            str: Contenu du fichier .env template
        """
        secret_key = SecureConfigGenerator.generate_secret_key()
        
        template = f"""# ===================================================================
# CONFIGURATION SÉCURISÉE - SYSTÈME DE GESTION DE PRÉSENCE
# ===================================================================
# IMPORTANT: Ce fichier contient des informations sensibles !
# - Ne JAMAIS committer ce fichier dans Git
# - Utiliser des valeurs différentes pour chaque environnement
# - Générer de nouvelles clés pour la production

# ===================
# SÉCURITÉ DE BASE
# ===================
SECRET_KEY={secret_key}
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.com

# ===================
# BASE DE DONNÉES
# ===================
# SQLite (développement)
DATABASE_URL=sqlite:///db.sqlite3

# PostgreSQL (production - décommentez et configurez)
# DB_NAME=attendance_prod
# DB_USER=attendance_user
# DB_PASSWORD={SecureConfigGenerator.generate_password(16)}
# DB_HOST=localhost
# DB_PORT=5432

# ===================
# GÉOLOCALISATION
# ===================
SITE_CENTER_LAT=6.1304
SITE_CENTER_LNG=1.2158
RADIUS_METERS=200
ACCURACY_MAX_METERS=50
GPS_REQUIRED=True

# ===================
# CONFIGURATION EMAIL
# ===================
# Console (développement)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# SMTP (production - configurez vos vrais identifiants)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=votre-email@domaine.com
# EMAIL_HOST_PASSWORD={SecureConfigGenerator.generate_password(16)}

# ===================
# FICHIERS STATIQUES
# ===================
STATIC_ROOT=staticfiles/
MEDIA_ROOT=media/

# ===================
# SÉCURITÉ AVANCÉE (Production)
# ===================
# Décommentez pour la production HTTPS
# SECURE_SSL_REDIRECT=True
# SECURE_HSTS_SECONDS=31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS=True
# SECURE_HSTS_PRELOAD=True
# SESSION_COOKIE_SECURE=True
# CSRF_COOKIE_SECURE=True
"""
        return template


def validate_configuration():
    """
    Fonction principale de validation de la configuration.
    
    À appeler dans settings.py pour valider la configuration au démarrage.
    """
    from django.conf import settings
    
    try:
        # Valider la configuration de base
        SecurityConfigValidator.check_production_security(
            debug=getattr(settings, 'DEBUG', True),
            secret_key=getattr(settings, 'SECRET_KEY', ''),
            allowed_hosts=getattr(settings, 'ALLOWED_HOSTS', [])
        )
        
        # Valider la configuration email
        SecurityConfigValidator.validate_email_config(
            email_backend=getattr(settings, 'EMAIL_BACKEND', ''),
            email_host_user=getattr(settings, 'EMAIL_HOST_USER', ''),
            email_host_password=getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        )
        
    except ImproperlyConfigured as e:
        print(f"❌ ERREUR DE CONFIGURATION: {e}")
        print("🔧 Consultez la documentation pour corriger la configuration")
        raise