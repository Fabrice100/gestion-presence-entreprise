# 📦 Guide d'Installation - Système de Gestion de Présence

## Vue d'ensemble

Ce système est une application Django complète pour la gestion des présences avec :
- ✅ Pointage par géolocalisation GPS
- ✅ Gestion des congés avec workflow de validation
- ✅ 4 rôles (Admin, RH/DG, Manager, Employee)
- ✅ Rapports et exports
- ✅ Interface moderne Bootstrap 5

---

## 🖥️ Prérequis

### Logiciels requis

| Logiciel | Version minimale | Téléchargement |
|----------|-----------------|----------------|
| **Python** | 3.11+ | https://www.python.org/downloads/ |
| **Git** | 2.30+ | https://git-scm.com/downloads |
| **Visual Studio Code** (recommandé) | Latest | https://code.visualstudio.com/ |

### Système d'exploitation

- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu 20.04+, Debian, Fedora)

---

## 📥 Installation

### Étape 1: Cloner le projet

```bash
# Naviguer dans le dossier de votre choix
cd ~/Documents  # macOS/Linux
cd C:\Users\VotreNom\Documents  # Windows

# Cloner le repository
git clone https://github.com/votre-username/attendance-system.git
cd attendance-system
```

### Étape 2: Créer un environnement virtuel

**Windows PowerShell:**
```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
python -m venv env
env\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv env
source env/bin/activate
```

**Vérification:**
```bash
# Vous devriez voir (env) dans votre terminal
(env) C:\...\attendance-system>
```

### Étape 3: Installer les dépendances

```bash
# Mise à jour de pip
python -m pip install --upgrade pip

# Installation des packages
pip install -r requirements.txt
```

**Liste des dépendances principales:**
- Django 5.1.3
- Pillow (gestion d'images)
- python-dateutil
- pytz
- django-extensions (développement)

### Étape 4: Configuration de l'environnement

1. **Copier le fichier d'environnement:**
```bash
cp env.example .env  # macOS/Linux
copy env.example .env  # Windows
```

2. **Éditer `.env`:**
```ini
# Django Core
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite par défaut)
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

# Email (optionnel pour développement)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# Sécurité (production uniquement)
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
```

### Étape 5: Initialiser la base de données

```bash
# Appliquer les migrations
python manage.py migrate

# Créer les données de démonstration
python init_database.py
```

**Comptes créés automatiquement:**

| Rôle | Username | Password | Peut pointer |
|------|----------|----------|--------------|
| **Admin** | admin | admin123 | ❌ Non (superuser) |
| **RH/DG** | rh.dg | password123 | ❌ Non |
| **Manager IT** | manager.it | password123 | ✅ Oui |
| **Employés** | emp1, emp2, ... emp11 | password123 | ✅ Oui |

### Étape 6: Collecter les fichiers statiques

```bash
python manage.py collectstatic --noinput
```

### Étape 7: Lancer le serveur de développement

```bash
python manage.py runserver
```

**Accéder à l'application:**
- Interface web: http://127.0.0.1:8000/
- Admin Django: http://127.0.0.1:8000/admin/

---

## 🚀 Premier démarrage

### 1. Se connecter en tant qu'Admin

1. Ouvrir http://127.0.0.1:8000/
2. Cliquer sur "Connexion"
3. Entrer:
   - **Username:** admin
   - **Password:** admin123

### 2. Configurer la géolocalisation

1. Se connecter en tant qu'admin
2. Aller dans "Paramètres système" (menu supérieur)
3. Configurer les coordonnées GPS du bureau:

**Exemple - Cotonou, Bénin:**
```
Latitude: 6.3654
Longitude: 2.4183
Rayon autorisé: 200m
Précision maximale: 100m
```

**Autres exemples:**
- **Paris**: Lat: 48.8566, Lon: 2.3522
- **Abidjan**: Lat: 5.3600, Lon: -4.0083
- **Dakar**: Lat: 14.7167, Lon: -17.4677

4. Configurer les horaires de travail:
```
Heure d'arrivée: 08:00
Heure de départ: 17:00
Tolérance retard: 15 minutes
```

5. Cliquer sur "Enregistrer"

### 3. Tester un pointage

1. Se déconnecter (Menu utilisateur → Déconnexion)
2. Se reconnecter avec un compte employé:
   - **Username:** emp1
   - **Password:** password123
3. Aller dans "Pointer" (menu)
4. Activer le **Mode Démo** (pour les tests sans GPS)
5. Cliquer sur "Pointer l'arrivée"

---

## 🧪 Tests

### Exécuter tous les tests

```bash
# Tous les tests
python manage.py test

# Tests d'un module spécifique
python manage.py test tests.test_user_service
python manage.py test tests.test_permissions
python manage.py test tests.test_gps_validation
```

### Tests manuels recommandés

**Test 1: Pointage GPS**
1. Se connecter en tant qu'employé
2. Activer le Mode Démo
3. Pointer arrivée → Vérifier succès
4. Pointer sortie → Vérifier succès

**Test 2: Validation congé**
1. Se connecter en tant qu'employé (emp1)
2. Créer une demande de congé
3. Se déconnecter
4. Se connecter en tant que manager (manager.it)
5. Approuver la demande
6. Se connecter en tant que RH (rh.dg)
7. Approuver définitivement

**Test 3: Sécurité GPS**
1. Se connecter en tant que RH (rh.dg)
2. Aller dans "Paramètres système"
3. Vérifier que les champs GPS sont **en lecture seule**
4. Se connecter en tant qu'admin
5. Vérifier que les champs GPS sont **modifiables**

---

## 📁 Structure du projet

```
attendance_system/
├── accounts/               # Gestion utilisateurs et authentification
│   ├── models.py          # EmployeeProfile, User
│   ├── views.py           # Connexion, dashboard
│   ├── user_services.py   # Services métier (génération ID, etc.)
│   └── middleware.py      # Force password change
├── attendance/            # Gestion des pointages
│   ├── models.py          # Attendance, CompanySettings
│   ├── views.py           # PunchView
│   ├── attendance_service.py  # Services GPS, validation
│   ├── forms.py           # PunchForm, validation
│   └── admin_models.py    # CompanySettings
├── leave/                 # Gestion des congés
│   ├── models.py          # LeaveRequest, LeaveType
│   ├── workflow_views.py  # Workflow de validation
│   └── forms.py           # Formulaires congé
├── reports/               # Rapports et exports
│   ├── views.py           # Vues de rapports
│   └── export_services.py # Export Excel, PDF
├── templates/             # Templates HTML
│   ├── base_modern.html   # Template de base
│   ├── accounts/          # Templates comptes
│   ├── attendance/        # Templates pointage
│   └── leave/             # Templates congé
├── static/                # Fichiers statiques (CSS, JS)
├── media/                 # Fichiers uploadés
├── tests/                 # Tests unitaires
│   ├── test_user_service.py
│   ├── test_permissions.py
│   └── test_gps_validation.py
├── manage.py              # Commandes Django
├── requirements.txt       # Dépendances Python
├── init_database.py       # Script d'initialisation
└── db.sqlite3            # Base de données SQLite
```

---

## 🔧 Configuration avancée

### Base de données PostgreSQL (Production)

1. **Installer PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS (Homebrew)
brew install postgresql
```

2. **Créer la base:**
```bash
sudo -u postgres psql
CREATE DATABASE attendance_db;
CREATE USER attendance_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;
\q
```

3. **Modifier `.env`:**
```ini
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=attendance_db
DATABASE_USER=attendance_user
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

4. **Installer psycopg2:**
```bash
pip install psycopg2-binary
```

5. **Migrer:**
```bash
python manage.py migrate
```

### Email en production (Gmail)

1. **Activer l'authentification à 2 facteurs Gmail**
2. **Générer un mot de passe d'application:**
   - https://myaccount.google.com/apppasswords

3. **Modifier `.env`:**
```ini
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-application
DEFAULT_FROM_EMAIL=votre-email@gmail.com
```

### Déploiement (Production)

**Checklist sécurité:**
- [ ] `DEBUG=False` dans `.env`
- [ ] `SECRET_KEY` complexe (50+ caractères)
- [ ] `ALLOWED_HOSTS` configuré
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] Base de données PostgreSQL
- [ ] Collecte des fichiers statiques
- [ ] Serveur WSGI (Gunicorn, uWSGI)
- [ ] Reverse proxy (Nginx, Apache)

**Exemple Gunicorn:**
```bash
pip install gunicorn
gunicorn attendance_system.wsgi:application --bind 0.0.0.0:8000
```

---

## ❓ Dépannage

### Erreur: "No module named 'django'"

**Solution:**
```bash
# Vérifier que l'environnement virtuel est activé
# Réinstaller les dépendances
pip install -r requirements.txt
```

### Erreur: "OperationalError: no such table"

**Solution:**
```bash
# Appliquer les migrations
python manage.py migrate
```

### Erreur: GPS non détecté

**Solutions:**
1. Utiliser le **Mode Démo** pour les tests
2. Vérifier que le navigateur a accès à la géolocalisation
3. Autoriser la géolocalisation dans les paramètres du navigateur
4. Utiliser HTTPS en production (requis pour GPS)

### Erreur: "DisallowedHost"

**Solution:**
```bash
# Modifier .env
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.com
```

---

## 📞 Support

**Problèmes connus:**
- Consultez `GUIDE_RESOLUTION_GPS.md` pour les problèmes GPS
- Consultez `ANALYSE_BONNES_PRATIQUES.md` pour l'architecture

**Contact:**
- Email: votre-email@example.com
- GitHub Issues: https://github.com/votre-username/attendance-system/issues

---

## 📄 Licence

Ce projet est développé dans le cadre d'un projet de fin de cycle.

© 2024 - Système de Gestion de Présence
