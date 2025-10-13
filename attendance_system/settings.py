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

# SECURITY WARNING: keep the secret key used in production secret!
# Utilisation de python-decouple pour la gestion des variables d'environnement
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Hosts autorisés pour le déploiement
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '*']


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
SITE_CENTER_LAT = config('SITE_CENTER_LAT', default=6.1304, cast=float)  # Latitude Lomé
SITE_CENTER_LNG = config('SITE_CENTER_LNG', default=1.2158, cast=float)  # Longitude Lomé
RADIUS_METERS = config('RADIUS_METERS', default=200, cast=int)  # Rayon autorisé (200m)
ACCURACY_MAX_METERS = config('ACCURACY_MAX_METERS', default=50, cast=int)  # Précision GPS max

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

# Mailtrap (actuellement actif)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_PORT = 2525
EMAIL_HOST_USER = '1a7b198de7ad5e'
EMAIL_HOST_PASSWORD = '5932cf0f1347df'
EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = 'noreply@presencepro.local'
SITE_URL = 'http://localhost:8000'  # URL du site pour les emails
SITE_NAME = 'PresencePro'

# Configuration du logging pour voir les erreurs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
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

# Configuration des logs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
