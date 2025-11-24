# 🚀 Guide de Déploiement - PresencePro

**Branche:** `full-project-snapshot`  
**Version:** 1.0.0  
**Date:** Novembre 2025

---

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Déploiement Local (Développement)](#déploiement-local-développement)
3. [Déploiement Production](#déploiement-production)
4. [Configuration PostgreSQL](#configuration-postgresql)
5. [Configuration Email](#configuration-email)
6. [Configuration GPS](#configuration-gps)
7. [Sécurité Production](#sécurité-production)
8. [Dépannage](#dépannage)

---

## 📦 Prérequis

### Logiciels requis

- **Python** 3.10 ou supérieur
- **PostgreSQL** 12+ (pour la production)
- **pip** (gestionnaire de paquets Python)
- **Git** (pour cloner le projet)

### Optionnel (production)

- **Nginx** (serveur web reverse proxy)
- **Gunicorn** (serveur WSGI)
- **Supervisor** ou **systemd** (gestion des processus)

---

## 🏠 Déploiement Local (Développement)

### Étape 1: Cloner le projet

```bash
# Cloner le repository
git clone <url-du-repo>
cd mon_projet/attendance_system

# Vérifier la branche
git checkout full-project-snapshot
```

### Étape 2: Créer l'environnement virtuel

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### Étape 3: Installer les dépendances

```bash
# Installer les dépendances de production
pip install -r requirements.txt

# OU pour le développement (avec outils de test)
pip install -r requirements-dev.txt
```

### Étape 4: Configurer les variables d'environnement

Créer un fichier `.env` à la racine du projet `attendance_system/` :

```ini
# ============================================
# DJANGO CORE
# ============================================
# Générer une clé secrète avec:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=votre-cle-secrete-generee-ici

# Mode développement
DEBUG=True

# Hosts autorisés (séparés par des virgules)
ALLOWED_HOSTS=localhost,127.0.0.1

# Origines CSRF autorisées
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# ============================================
# BASE DE DONNÉES
# ============================================
# Pour développement local avec SQLite (optionnel)
# DB_NAME=db.sqlite3

# Pour PostgreSQL (recommandé)
DB_NAME=attendance_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe_postgres
DB_HOST=localhost
DB_PORT=5432

# ============================================
# EMAIL
# ============================================
# Mode console (développement) - emails affichés dans le terminal
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# OU Mode Mailtrap (test)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.mailtrap.io
# EMAIL_PORT=2525
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=votre_user_mailtrap
# EMAIL_HOST_PASSWORD=votre_password_mailtrap

# OU Mode Gmail (production)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=votre-email@gmail.com
# EMAIL_HOST_PASSWORD=mot-de-passe-application-gmail

# ============================================
# GPS / GÉOLOCALISATION
# ============================================
# Coordonnées GPS du lieu de travail (Lomé par défaut)
SITE_CENTER_LAT=6.140766
SITE_CENTER_LNG=1.241907

# Rayon autorisé pour le pointage (en mètres)
RADIUS_METERS=200

# Précision GPS maximale acceptée (en mètres)
ACCURACY_MAX_METERS=100
```

### Étape 5: Configurer PostgreSQL (optionnel pour développement)

Si tu utilises PostgreSQL en local :

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer la base de données
CREATE DATABASE attendance_db;

# Créer un utilisateur
CREATE USER attendance_user WITH PASSWORD 'votre_mot_de_passe';

# Donner les permissions
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;

# Quitter
\q
```

### Étape 6: Appliquer les migrations

```bash
# Appliquer toutes les migrations
python manage.py migrate

# Vérifier l'état des migrations
python manage.py showmigrations
```

### Étape 7: Initialiser les données du Togo

```bash
# Charger les types de congés et jours fériés du Togo
python manage.py init_togo_setup
```

Cette commande crée :
- ✅ Types de congés conformes au Code du travail togolais
- ✅ Jours fériés 2025 du Togo
- ✅ Configuration GPS par défaut

### Étape 8: Créer un superutilisateur

```bash
# Créer un compte administrateur
python manage.py createsuperuser

# Suivre les instructions:
# - Username: admin
# - Email: admin@example.com
# - Password: (choisir un mot de passe sécurisé)
```

### Étape 9: Collecter les fichiers statiques

```bash
# Collecter les fichiers CSS/JS dans staticfiles/
python manage.py collectstatic --noinput
```

### Étape 10: Lancer le serveur de développement

```bash
# Démarrer le serveur Django
python manage.py runserver

# OU sur un port spécifique
python manage.py runserver 8000
```

**Accès à l'application:**
- 🏠 **Landing page:** http://127.0.0.1:8000/
- 🔐 **Connexion:** http://127.0.0.1:8000/accounts/login/
- ⚙️ **Admin Django:** http://127.0.0.1:8000/admin/

---

## 🌐 Déploiement Production

### Étape 1: Préparer le serveur

#### Sur Ubuntu/Debian:

```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Python et pip
sudo apt install python3 python3-pip python3-venv -y

# Installer PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Installer Nginx (optionnel)
sudo apt install nginx -y

# Installer Gunicorn
pip3 install gunicorn
```

### Étape 2: Cloner le projet sur le serveur

```bash
# Créer un répertoire pour l'application
sudo mkdir -p /var/www/presencepro
sudo chown $USER:$USER /var/www/presencepro

# Cloner le projet
cd /var/www/presencepro
git clone <url-du-repo> .
git checkout full-project-snapshot
cd attendance_system
```

### Étape 3: Configurer l'environnement virtuel

```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
pip install gunicorn
```

### Étape 4: Configurer PostgreSQL

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer la base de données
CREATE DATABASE attendance_db;

# Créer un utilisateur
CREATE USER attendance_user WITH PASSWORD 'MOT_DE_PASSE_SECURISE';

# Donner les permissions
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;
ALTER USER attendance_user CREATEDB;

# Quitter
\q
```

### Étape 5: Configurer le fichier `.env` (PRODUCTION)

**⚠️ IMPORTANT:** Utiliser des valeurs sécurisées en production !

```ini
# ============================================
# DJANGO CORE - PRODUCTION
# ============================================
SECRET_KEY=GENERER-UNE-CLE-SECRETE-UNIQUE-ET-LONGUE

# DÉSACTIVER LE MODE DEBUG EN PRODUCTION !
DEBUG=False

# Ajouter le domaine de production
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com,IP_DU_SERVEUR

# Origines CSRF
CSRF_TRUSTED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com

# ============================================
# BASE DE DONNÉES - PRODUCTION
# ============================================
DB_NAME=attendance_db
DB_USER=attendance_user
DB_PASSWORD=MOT_DE_PASSE_SECURISE
DB_HOST=localhost
DB_PORT=5432

# ============================================
# EMAIL - PRODUCTION
# ============================================
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-application-gmail
DEFAULT_FROM_EMAIL=noreply@votre-domaine.com

# ============================================
# GPS / GÉOLOCALISATION
# ============================================
# Coordonnées GPS du lieu de travail réel
SITE_CENTER_LAT=6.140766
SITE_CENTER_LNG=1.241907
RADIUS_METERS=200
ACCURACY_MAX_METERS=100
```

### Étape 6: Appliquer les migrations et initialiser

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Appliquer les migrations
python manage.py migrate

# Initialiser les données du Togo
python manage.py init_togo_setup

# Créer un superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

### Étape 7: Configurer Gunicorn

Créer un fichier `gunicorn_config.py` :

```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
max_requests = 1000
max_requests_jitter = 50
accesslog = "/var/log/presencepro/gunicorn_access.log"
errorlog = "/var/log/presencepro/gunicorn_error.log"
```

Tester Gunicorn :

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Tester Gunicorn
gunicorn --config gunicorn_config.py attendance_system.wsgi:application
```

### Étape 8: Configurer Supervisor (gestion des processus)

Créer `/etc/supervisor/conf.d/presencepro.conf` :

```ini
[program:presencepro]
command=/var/www/presencepro/attendance_system/venv/bin/gunicorn --config /var/www/presencepro/attendance_system/gunicorn_config.py attendance_system.wsgi:application
directory=/var/www/presencepro/attendance_system
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/presencepro/supervisor.log
```

Démarrer avec Supervisor :

```bash
# Recharger la configuration
sudo supervisorctl reread
sudo supervisorctl update

# Démarrer le service
sudo supervisorctl start presencepro

# Vérifier le statut
sudo supervisorctl status presencepro
```

### Étape 9: Configurer Nginx (reverse proxy)

Créer `/etc/nginx/sites-available/presencepro` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    # Redirection HTTPS (si certificat SSL configuré)
    # return 301 https://$server_name$request_uri;

    # OU configuration HTTP directe
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Servir les fichiers statiques directement
    location /static/ {
        alias /var/www/presencepro/attendance_system/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Servir les fichiers média
    location /media/ {
        alias /var/www/presencepro/attendance_system/media/;
    }
}
```

Activer le site :

```bash
# Créer le lien symbolique
sudo ln -s /etc/nginx/sites-available/presencepro /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Redémarrer Nginx
sudo systemctl restart nginx
```

### Étape 10: Configurer le pare-feu

```bash
# Autoriser HTTP (port 80)
sudo ufw allow 80/tcp

# Autoriser HTTPS (port 443) si SSL configuré
sudo ufw allow 443/tcp

# Vérifier le statut
sudo ufw status
```

---

## 🗄️ Configuration PostgreSQL

### Créer la base de données

```bash
sudo -u postgres psql

CREATE DATABASE attendance_db;
CREATE USER attendance_user WITH PASSWORD 'mot_de_passe_securise';
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;
ALTER USER attendance_user CREATEDB;
\q
```

### Vérifier la connexion

```bash
# Tester la connexion
psql -h localhost -U attendance_user -d attendance_db

# Si ça fonctionne, tu verras:
# attendance_db=>
```

### Backup de la base de données

```bash
# Créer un backup
pg_dump -U attendance_user attendance_db > backup_$(date +%Y%m%d).sql

# Restaurer un backup
psql -U attendance_user attendance_db < backup_20251115.sql
```

---

## 📧 Configuration Email

### Option 1: Mailtrap (Test/Développement)

```ini
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre_user_mailtrap
EMAIL_HOST_PASSWORD=votre_password_mailtrap
```

### Option 2: Gmail (Production)

1. **Activer l'authentification à 2 facteurs** sur ton compte Gmail
2. **Générer un mot de passe d'application:**
   - Aller sur: https://myaccount.google.com/apppasswords
   - Créer un mot de passe pour "Mail"
3. **Configurer `.env`:**

```ini
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-application-genere
DEFAULT_FROM_EMAIL=votre-email@gmail.com
```

### Option 3: Autres services SMTP

```ini
# Exemple: SendGrid, Mailgun, etc.
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=votre_api_key
```

### Tester l'envoi d'email

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Tester l'envoi
python manage.py shell

# Dans le shell Python:
from django.core.mail import send_mail
send_mail(
    'Test Email',
    'Ceci est un test',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)
```

---

## 📍 Configuration GPS

### Via l'interface web (recommandé)

1. Se connecter en tant qu'**admin** (superuser)
2. Aller dans **"Paramètres système"** (menu supérieur)
3. Modifier:
   - **Latitude du bureau:** Coordonnée GPS du lieu de travail
   - **Longitude du bureau:** Coordonnée GPS du lieu de travail
   - **Rayon autorisé:** 200 mètres (ou plus si besoin)
   - **Précision GPS max:** 100 mètres
4. **Enregistrer**

### Via le fichier `.env`

```ini
# Coordonnées GPS du lieu de travail
SITE_CENTER_LAT=6.140766
SITE_CENTER_LNG=1.241907

# Rayon autorisé (mètres)
RADIUS_METERS=200

# Précision GPS maximale acceptée (mètres)
ACCURACY_MAX_METERS=100
```

### Trouver les coordonnées GPS d'une adresse

1. **Google Maps:**
   - Aller sur https://maps.google.com
   - Cliquer droit sur l'adresse → "Plus d'infos"
   - Les coordonnées s'affichent en bas

2. **Via Python:**
```python
# Installer geopy
pip install geopy

# Dans un script Python:
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="presencepro")
location = geolocator.geocode("Adresse du lieu de travail, Lomé, Togo")
print(f"Latitude: {location.latitude}, Longitude: {location.longitude}")
```

---

## 🔒 Sécurité Production

### Checklist de sécurité

- [ ] **`DEBUG=False`** dans `.env`
- [ ] **`SECRET_KEY`** unique et complexe (50+ caractères)
- [ ] **`ALLOWED_HOSTS`** configuré avec le domaine réel
- [ ] **`CSRF_TRUSTED_ORIGINS`** configuré avec HTTPS
- [ ] **Base de données PostgreSQL** (pas SQLite)
- [ ] **Mot de passe PostgreSQL** sécurisé
- [ ] **HTTPS activé** (certificat SSL)
- [ ] **Fichiers statiques** servis par Nginx
- [ ] **Permissions fichiers** correctes (755 pour dossiers, 644 pour fichiers)
- [ ] **Backup automatique** de la base de données
- [ ] **Pare-feu** configuré (UFW)
- [ ] **Logs** surveillés régulièrement

### Générer une SECRET_KEY sécurisée

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Configurer HTTPS (Let's Encrypt)

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtenir un certificat SSL
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Renouvellement automatique
sudo certbot renew --dry-run
```

### Permissions des fichiers

```bash
# Permissions pour les fichiers
find /var/www/presencepro -type f -exec chmod 644 {} \;

# Permissions pour les dossiers
find /var/www/presencepro -type d -exec chmod 755 {} \;

# Propriétaire
sudo chown -R www-data:www-data /var/www/presencepro
```

---

## 🔧 Dépannage

### Erreur: "No module named 'django'"

**Solution:**
```bash
# Vérifier que l'environnement virtuel est activé
source venv/bin/activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Erreur: "OperationalError: no such table"

**Solution:**
```bash
# Appliquer les migrations
python manage.py migrate
```

### Erreur: "django.db.utils.OperationalError: FATAL: password authentication failed"

**Solution:**
- Vérifier les identifiants PostgreSQL dans `.env`
- Vérifier que l'utilisateur PostgreSQL existe
- Vérifier les permissions de l'utilisateur

### Erreur: "TemplateDoesNotExist"

**Solution:**
```bash
# Vérifier que les templates sont présents
ls -la templates/

# Vérifier la configuration dans settings.py
python manage.py check
```

### Erreur: "Static files not found"

**Solution:**
```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Vérifier que STATIC_ROOT est configuré dans settings.py
```

### Erreur: "CSRF verification failed"

**Solution:**
- Vérifier `CSRF_TRUSTED_ORIGINS` dans `.env`
- Vérifier que le domaine est dans `ALLOWED_HOSTS`
- Vérifier que les cookies fonctionnent (pas de blocage)

### Erreur Gunicorn: "Address already in use"

**Solution:**
```bash
# Trouver le processus qui utilise le port
sudo lsof -i :8000

# Tuer le processus
sudo kill -9 <PID>
```

### Vérifier les logs

```bash
# Logs Django
tail -f logs/django.log

# Logs Gunicorn
tail -f /var/log/presencepro/gunicorn_error.log

# Logs Nginx
sudo tail -f /var/log/nginx/error.log
```

---

## 📝 Commandes utiles

### Vérifier l'état du système

```bash
# Vérifier la configuration Django
python manage.py check

# Vérifier les migrations
python manage.py showmigrations

# Vérifier les permissions
python manage.py check --deploy
```

### Maintenance

```bash
# Créer un backup de la base de données
pg_dump -U attendance_user attendance_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Nettoyer les sessions expirées
python manage.py clearsessions

# Vérifier les fichiers statiques
python manage.py collectstatic --noinput --dry-run
```

### Redémarrer les services

```bash
# Redémarrer Gunicorn (Supervisor)
sudo supervisorctl restart presencepro

# Redémarrer Nginx
sudo systemctl restart nginx

# Redémarrer PostgreSQL
sudo systemctl restart postgresql
```

---

## ✅ Checklist de déploiement

### Avant le déploiement

- [ ] Code testé localement
- [ ] Migrations appliquées
- [ ] Fichier `.env` configuré
- [ ] Base de données créée
- [ ] Superutilisateur créé
- [ ] Données initiales chargées (`init_togo_setup`)

### Déploiement

- [ ] Environnement virtuel créé et activé
- [ ] Dépendances installées
- [ ] Migrations appliquées
- [ ] Fichiers statiques collectés
- [ ] Gunicorn configuré et testé
- [ ] Supervisor configuré
- [ ] Nginx configuré
- [ ] Pare-feu configuré

### Après le déploiement

- [ ] Site accessible via le domaine
- [ ] Connexion fonctionne
- [ ] Pointage GPS fonctionne
- [ ] Emails envoyés correctement
- [ ] Logs surveillés
- [ ] Backup automatique configuré

---

## 📞 Support

Pour toute question ou problème :

1. Vérifier les logs (`logs/django.log`, logs Gunicorn/Nginx)
2. Vérifier la configuration (`.env`, `settings.py`)
3. Vérifier les permissions des fichiers
4. Vérifier la connexion à la base de données
5. Vérifier la configuration email

---

**Document créé le:** Novembre 2025  
**Branche:** `full-project-snapshot`  
**Version:** 1.0.0

