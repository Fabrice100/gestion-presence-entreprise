"""
Configuration Django pour le système de gestion de présence.

Ce fichier contient toutes les configurations nécessaires pour le bon fonctionnement
du système de gestion de présence et congés pour PME.

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Import du validateur de sécurité
try:
    from common.security_config import SecurityConfigValidator
    SECURITY_VALIDATION_ENABLED = True
except ImportError:
    SECURITY_VALIDATION_ENABLED = False
    print("⚠️  Module de validation de sécurité non disponible")

# SECURITY WARNING: keep the secret key used in production secret!
# Utilisation de python-decouple pour la gestion des variables d'environnement
# SÉCURITÉ CRITIQUE: Pas de valeur par défaut pour SECRET_KEY !
SECRET_KEY = config('SECRET_KEY')

# Validation pour empêcher l'utilisation de la clé de développement en production
if SECRET_KEY == 'django-insecure-change-me-in-production':
    import sys
    print("❌ ERREUR CRITIQUE: SECRET_KEY par défaut détectée !")
    print("🔒 SÉCURITÉ: Vous devez définir une SECRET_KEY unique dans votre fichier .env")
    print("💡 Générez une clé sécurisée avec: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'")
    sys.exit(1)

# SECURITY WARNING: don't run with debug turned on in production!
# SÉCURITÉ: DEBUG=False par défaut pour la production
DEBUG = config('DEBUG', default=False, cast=bool)

# Avertissement si DEBUG est activé
if DEBUG:
    print("⚠️  AVERTISSEMENT: DEBUG=True détecté")
    print("🔒 Assurez-vous que DEBUG=False en production !")

# Hosts autorisés pour le déploiement
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver').split(',')


# Application definition
# Liste des applications Django installées dans le projet

INSTALLED_APPS = [
    # Applications Django par défaut
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Applications tierces
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Modules communs du projet
    'common',        # Utilitaires partagés (mixins, helpers)
    
    # Applications locales du projet
    'accounts',      # Gestion des comptes utilisateurs et authentification
    'attendance',    # Système de pointage avec géolocalisation
    'leave',         # Gestion des congés et validations
    'reports',       # Rapports et exports
]

# Configuration pour crispy-forms (formulaires Bootstrap)
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Backend d'authentification personnalisé
# Permet la connexion avec l'ID Employé (EMP001, MGR001, etc.)
AUTHENTICATION_BACKENDS = [
    'accounts.auth_backend.EmployeeIDBackend',  # Backend personnalisé (ID Employé)
    'django.contrib.auth.backends.ModelBackend',  # Backend par défaut (fallback)
]

# Middleware configuration
# Ordre important : les middlewares s'exécutent dans l'ordre de la liste
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.ForcePasswordChangeMiddleware',  # Changement mdp obligatoire
    'accounts.admin_middleware.AdminRedirectMiddleware',   # Redirection admin vers Django Admin
]

ROOT_URLCONF = 'attendance_system.urls'

# Configuration des templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Dossier templates global
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'attendance_system.wsgi.application'


# Database configuration
# Configuration de la base de données (SQLite pour le développement)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuration PostgreSQL pour la production (à décommenter si nécessaire)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME', default='attendance_db'),
#         'USER': config('DB_USER', default='postgres'),
#         'PASSWORD': config('DB_PASSWORD', default=''),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# Configuration pour la localisation (français pour le Togo)
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Lome'  # Fuseau horaire du Togo
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# CONFIGURATION DU SYSTÈME DE POINTAGE (GÉOLOCALISATION & HORAIRES)
# =============================================================================

# Configuration géolocalisation
SITE_CENTER_LAT = config('SITE_CENTER_LAT', default=6.140766, cast=float)  # Latitude lieu de travail
SITE_CENTER_LNG = config('SITE_CENTER_LNG', default=1.241907, cast=float)  # Longitude lieu de travail
RADIUS_METERS = config('RADIUS_METERS', default=200, cast=int)  # Rayon autorisé (200m)
ACCURACY_MAX_METERS = config('ACCURACY_MAX_METERS', default=200, cast=int)  # Précision GPS max

# Géolocalisation obligatoire
GPS_REQUIRED = config('GPS_REQUIRED', default=True, cast=bool)  # GPS obligatoire

# Horaires de travail
WORK_START_TIME = '08:00'  # Heure d'arrivée attendue
WORK_END_TIME = '17:00'    # Heure de sortie attendue
LATE_TOLERANCE_MINUTES = 15  # Tolérance retard (15 minutes)

# Configuration des messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Configuration des emails
# Backend console amélioré (décommenté pour revenir au mode console si besoin)
# EMAIL_BACKEND = 'accounts.email_backend.EnhancedConsoleEmailBackend'

# Configuration email sécurisée - AUCUNE valeur par défaut pour les credentials
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)

# SÉCURITÉ: Pas de valeurs par défaut pour les identifiants !
# Ces variables DOIVENT être définies dans .env ou variables d'environnement
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)

DEFAULT_FROM_EMAIL = 'noreply@presencepro.local'
SITE_URL = 'http://localhost:8000'  # URL du site pour les emails
SITE_NAME = 'PresencePro'

# Configuration des logs (unifiée et sécurisée)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Configuration de sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuration des sessions
SESSION_COOKIE_AGE = 86400  # 24 heures
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ===================================================================
# VALIDATION AUTOMATIQUE DE LA SÉCURITÉ
# ===================================================================
# Validation de la configuration au démarrage de l'application
if SECURITY_VALIDATION_ENABLED:
    try:
        # Valider la SECRET_KEY
        SecurityConfigValidator.validate_secret_key(SECRET_KEY)
        
        # Valider ALLOWED_HOSTS si pas en mode DEBUG
        SecurityConfigValidator.validate_allowed_hosts(ALLOWED_HOSTS, DEBUG)
        
        # Valider la configuration email
        SecurityConfigValidator.validate_email_config(
            EMAIL_BACKEND, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
        )
        
        # Affichage du statut de sécurité
        if not DEBUG:
            print("🔒 Configuration de production sécurisée validée ✅")
        else:
            print("🚧 Mode développement - Vérifications de sécurité OK ✅")
            
    except Exception as e:
        print(f"❌ ERREUR DE VALIDATION SÉCURITÉ: {e}")
        # En production, arrêter l'application si la sécurité n'est pas validée
        if not DEBUG:
            import sys
            print("🛑 Application arrêtée pour des raisons de sécurité")
            sys.exit(1)
