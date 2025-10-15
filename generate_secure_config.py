#!/usr/bin/env python3
"""
Script de génération de configuration sécurisée.

Ce script génère automatiquement des fichiers .env sécurisés
avec des clés et mots de passe générés aléatoirement.

Usage:
    python generate_secure_config.py [--production]

Auteur: Système de Gestion de Présence
Version: 2.0 (Sécurisé)
"""

import os
import sys
import argparse
from pathlib import Path

# Ajouter le répertoire du projet au path Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configuration Django minimale pour importer nos modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')

try:
    import django
    django.setup()
    from common.security_config import SecureConfigGenerator
except ImportError as e:
    print(f"❌ Erreur d'import Django: {e}")
    print("💡 Assurez-vous que Django est installé et que vous êtes dans le bon répertoire")
    sys.exit(1)


def generate_development_config():
    """Génère un fichier .env pour le développement."""
    print("🛠️  Génération de la configuration de DÉVELOPPEMENT...")
    
    secret_key = SecureConfigGenerator.generate_secret_key()
    
    config_content = f"""# ===================================================================
# CONFIGURATION DÉVELOPPEMENT - SYSTÈME DE GESTION DE PRÉSENCE
# ===================================================================
# Fichier généré automatiquement le {os.popen('date').read().strip()}
# IMPORTANT: Ne pas utiliser en production !

# ===================
# SÉCURITÉ DE BASE
# ===================
SECRET_KEY={secret_key}
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# ===================
# BASE DE DONNÉES
# ===================
DATABASE_URL=sqlite:///db.sqlite3

# ===================
# GÉOLOCALISATION (EXEMPLE LOMÉ, TOGO)
# ===================
SITE_CENTER_LAT=6.1304
SITE_CENTER_LNG=1.2158
RADIUS_METERS=200
ACCURACY_MAX_METERS=50
GPS_REQUIRED=True

# ===================
# EMAIL DÉVELOPPEMENT
# ===================
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=25
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# ===================
# FICHIERS STATIQUES
# ===================
STATIC_ROOT=staticfiles/
MEDIA_ROOT=media/
"""
    
    return config_content


def generate_production_config():
    """Génère un template de configuration pour la production."""
    print("🏭 Génération du TEMPLATE de configuration PRODUCTION...")
    
    secret_key = SecureConfigGenerator.generate_secret_key()
    db_password = SecureConfigGenerator.generate_password(20)
    email_password = SecureConfigGenerator.generate_password(16)
    
    config_content = f"""# ===================================================================
# CONFIGURATION PRODUCTION - SYSTÈME DE GESTION DE PRÉSENCE
# ===================================================================
# Template généré automatiquement le {os.popen('date').read().strip()}
# IMPORTANT: Modifiez toutes les valeurs avant utilisation !

# ===================
# SÉCURITÉ DE BASE
# ===================
SECRET_KEY={secret_key}
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com

# ===================
# BASE DE DONNÉES PRODUCTION
# ===================
DB_NAME=attendance_prod
DB_USER=attendance_user
DB_PASSWORD={db_password}
DB_HOST=localhost
DB_PORT=5432

# ===================
# GÉOLOCALISATION
# ===================
# REMPLACEZ par les coordonnées de votre entreprise
SITE_CENTER_LAT=6.1304
SITE_CENTER_LNG=1.2158
RADIUS_METERS=200
ACCURACY_MAX_METERS=50
GPS_REQUIRED=True

# ===================
# EMAIL PRODUCTION
# ===================
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@entreprise.com
EMAIL_HOST_PASSWORD={email_password}

# ===================
# SÉCURITÉ HTTPS
# ===================
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# ===================
# FICHIERS STATIQUES
# ===================
STATIC_ROOT=/var/www/attendance/staticfiles/
MEDIA_ROOT=/var/www/attendance/media/
"""
    
    return config_content


def backup_existing_env():
    """Sauvegarde le fichier .env existant s'il existe."""
    env_file = Path('.env')
    if env_file.exists():
        import time
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_file = Path(f'.env.backup_{timestamp}')
        env_file.rename(backup_file)
        print(f"💾 Fichier .env existant sauvegardé vers {backup_file}")
        return True
    return False


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Génère des fichiers de configuration sécurisée"
    )
    parser.add_argument(
        '--production', 
        action='store_true',
        help='Génère un template pour la production'
    )
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force la génération même si .env existe'
    )
    
    args = parser.parse_args()
    
    print("🔐 GÉNÉRATEUR DE CONFIGURATION SÉCURISÉE")
    print("=" * 50)
    
    # Vérifier si .env existe
    env_file = Path('.env')
    if env_file.exists() and not args.force:
        print("⚠️  Un fichier .env existe déjà !")
        print("💡 Utilisez --force pour le remplacer ou renommez-le manuellement")
        sys.exit(1)
    
    try:
        if args.production:
            # Génération pour la production
            content = generate_production_config()
            filename = '.env.production'
            
            # Sauvegarde si nécessaire
            if Path(filename).exists():
                backup_existing_env()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Template de production généré: {filename}")
            print("🔧 ACTIONS REQUISES:")
            print("   1. Modifiez TOUS les paramètres marqués 'votre-...'")
            print("   2. Remplacez les coordonnées GPS par celles de votre entreprise")
            print("   3. Configurez votre serveur SMTP réel")
            print("   4. Testez la configuration avant déploiement")
            
        else:
            # Génération pour le développement
            content = generate_development_config()
            
            # Sauvegarde si nécessaire
            if env_file.exists():
                backup_existing_env()
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Configuration de développement générée: .env")
            print("🚀 PRÊT POUR LE DÉVELOPPEMENT:")
            print("   - SECRET_KEY sécurisée générée")
            print("   - Mode DEBUG activé")
            print("   - Base SQLite configurée")
            print("   - Email console activé")
        
        print("\n🔒 SÉCURITÉ:")
        print("   - Ne JAMAIS committer les fichiers .env")
        print("   - Générer de nouvelles clés pour chaque environnement")
        print("   - Vérifier les permissions des fichiers de configuration")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()