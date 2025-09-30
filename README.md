# Système de Gestion de Présence en Entreprise

## 📋 Description

Système web de gestion de présence développé avec Django pour les PME locales au Togo. Ce projet fait partie d'un projet de fin de cycle en architecture des logiciels.

## 🚀 Fonctionnalités

### ✅ Fonctionnalités principales
- **Authentification** : Connexion sécurisée avec gestion des rôles
- **Pointage** : Pointage d'entrée/sortie avec géolocalisation
- **Gestion des congés** : Demandes, validation et suivi des soldes
- **Rapports** : Génération de rapports de présence et congés
- **Administration** : Interface d'administration Django complète

### 👥 Rôles utilisateurs
- **Administrateur** : Gestion complète du système
- **Manager** : Validation des congés de son équipe
- **RH/DG** : Gestion globale des ressources humaines
- **Employé** : Pointage et demandes de congés

## 🛠️ Technologies

- **Backend** : Django 4.2.7
- **Base de données** : SQLite (développement) / PostgreSQL (production)
- **Frontend** : HTML/CSS/JavaScript + Bootstrap 5
- **Géolocalisation** : API Geolocation du navigateur
- **Authentification** : Django Auth System

## 📦 Installation

### Prérequis
- Python 3.8+
- pip
- Git

### Installation
```bash
# Cloner le projet
git clone <url-du-repo>
cd attendance_system

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Copier le fichier d'environnement
copy env.example .env

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python create_admin.py

# Créer les données de test
python create_test_data.py

# Lancer le serveur
python manage.py runserver
```

## 🔐 Comptes de test

| Rôle | Nom d'utilisateur | Mot de passe |
|------|-------------------|--------------|
| Administrateur | admin | admin123 |
| Manager IT | manager.it | password123 |
| RH/DG | rh.dg | password123 |
| Développeur | dev1 | password123 |
| Commercial | com1 | password123 |

## 📁 Structure du projet

```
attendance_system/
├── accounts/          # Gestion des utilisateurs et départements
├── attendance/        # Pointage et présences
├── leave/            # Gestion des congés
├── reports/          # Rapports et paramètres
├── attendance_system/ # Configuration Django
├── templates/        # Templates HTML
├── static/          # Fichiers statiques (CSS, JS)
├── media/           # Fichiers uploadés
└── logs/            # Fichiers de logs
```

## 🎯 Utilisation

1. **Accès** : http://127.0.0.1:8000/
2. **Administration** : http://127.0.0.1:8000/admin/
3. **Pointage** : http://127.0.0.1:8000/attendance/punch/

## 📊 Modèles de données

### Utilisateurs et départements
- `Department` : Départements de l'entreprise
- `EmployeeProfile` : Profils étendus des employés

### Présence
- `Attendance` : Pointages avec géolocalisation
- `AttendanceAnomaly` : Anomalies détectées

### Congés
- `LeaveType` : Types de congés
- `LeaveRequest` : Demandes de congés
- `LeaveBalance` : Soldes de congés
- `Holiday` : Jours fériés

### Système
- `SystemSettings` : Paramètres globaux
- `ReportTemplate` : Modèles de rapports

## 🔧 Configuration

### Variables d'environnement (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
SITE_CENTER_LAT=6.1378
SITE_CENTER_LNG=1.2123
RADIUS_METERS=200
ACCURACY_MAX_METERS=100
```

### Géolocalisation
Le système utilise les coordonnées GPS pour vérifier que le pointage se fait dans la zone autorisée :
- **Centre** : Lomé, Togo (6.1378°N, 1.2123°E)
- **Rayon autorisé** : 200 mètres
- **Précision requise** : < 100 mètres

## 🚀 Déploiement

### Production
1. Changer `DEBUG=False` dans les settings
2. Configurer une base de données PostgreSQL
3. Configurer les variables d'environnement
4. Utiliser un serveur web (nginx + gunicorn)

### Sécurité
- Changer la SECRET_KEY
- Configurer HTTPS
- Activer les cookies sécurisés
- Configurer HSTS

## 📝 Développement

### Commandes utiles
```bash
# Vérifier le code
python manage.py check

# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic

# Lancer les tests
python manage.py test
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commit les changements
4. Push vers la branche
5. Créer une Pull Request

## 📄 Licence

Ce projet est développé dans le cadre d'un projet académique.

## 👨‍💻 Auteur

**Votre nom** - Projet de fin de cycle - Licence en Architecture des Logiciels

## 📞 Support

Pour toute question ou problème, contactez l'administrateur système.

---

**Version** : 1.0.0  
**Dernière mise à jour** : Septembre 2025
