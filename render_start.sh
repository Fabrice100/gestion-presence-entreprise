#!/bin/bash
# Script de démarrage pour Render
# Exécute les migrations automatiquement avant de lancer Gunicorn

set -e  # Arrêter en cas d'erreur

echo "=== Démarrage de l'application PresencePro ==="
echo "Répertoire actuel: $(pwd)"

# Le script est dans attendance_system/, donc on est déjà au bon endroit
# après le "cd attendance_system" du Start Command

# Exécuter les migrations
echo "=== Exécution des migrations ==="
python manage.py migrate --noinput || {
    echo "ERREUR: Les migrations ont échoué"
    exit 1
}

# Lancer Gunicorn
echo "=== Démarrage de Gunicorn ==="
exec gunicorn attendance_system.wsgi:application --bind 0.0.0.0:${PORT:-10000}

