#!/bin/bash
# Script de démarrage pour Render
# Exécute les migrations automatiquement avant de lancer Gunicorn

set -e  # Arrêter en cas d'erreur

echo "=== Démarrage de l'application PresencePro ==="

# Aller dans le répertoire du projet
cd attendance_system

# Exécuter les migrations
echo "=== Exécution des migrations ==="
python manage.py migrate --noinput || {
    echo "ERREUR: Les migrations ont échoué"
    exit 1
}

# Lancer Gunicorn
echo "=== Démarrage de Gunicorn ==="
exec gunicorn attendance_system.wsgi:application --bind 0.0.0.0:${PORT:-10000}

