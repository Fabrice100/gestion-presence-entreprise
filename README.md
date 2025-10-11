# PresencePro - Système de Gestion de Présence

## 📋 Description

**PresencePro** est un système web professionnel de gestion de présence et congés développé avec Django. 
Conçu pour les entreprises au Togo, il offre une solution complète pour la gestion des ressources humaines.

**Projet de fin de cycle** - Licence en Architecture des Logiciels

---

## 🚀 Fonctionnalités principales

### ✅ Gestion des employés
- Création automatique d'ID unique (EMPXXX)
- Génération de mot de passe sécurisé
- Envoi automatique des credentials par email
- Changement de mot de passe obligatoire à la première connexion
- Gestion des départements et hiérarchies

### 👆 Pointage GPS
- Pointage entrée/sortie avec géolocalisation
- Vérification de la zone autorisée
- Détection automatique des anomalies (retards, absences)
- Historique complet des présences

### 🏖️ Gestion des congés
- Types de congés conformes au Code du travail togolais
- Workflow de validation à 2 niveaux (Manager → RH/DG)
- Calcul automatique des soldes
- Détection des chevauchements
- Jours fériés du Togo intégrés

### 📊 Rapports & Analytics
- Rapports de présence
- Rapports de congés
- Détection d'anomalies
- Export des données

### 🔔 Notifications automatiques
- Email de bienvenue (création compte)
- Notification de demande (pour validateur)
- Notification d'approbation (pour employé)
- Notification de rejet (avec motif)

---

## 👥 Rôles utilisateurs

| Rôle | Permissions |
|------|-------------|
| **Employé** | Pointage, demandes de congés, consultation historique |
| **Manager** | + Validation congés niveau 1, gestion équipe |
| **RH/DG** | + Validation congés niveau 2, gestion employés/départements |
| **Admin** | + Accès complet, rapports, configuration système |

---

## 🛠️ Technologies

- **Backend** : Django 5.1.3
- **Base de données** : SQLite (développement)
- **Frontend** : HTML5, CSS3, Bootstrap 5.3.2
- **Design System** : CSS Variables, composants réutilisables
- **Géolocalisation** : API Geolocation HTML5
- **Emails** : Console backend (démo) / Mailtrap (test)
- **Authentification** : Django Auth + Backend personnalisé

---

## 📦 Installation

### Prérequis
- Python 3.10+
- pip

### Étapes d'installation

```bash
# 1. Cloner le projet
git clone <url-du-repo>
cd attendance_system

# 2. Créer un environnement virtuel
python -m venv venv

# 3. Activer l'environnement virtuel
# Windows
venv\Scripts\activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Appliquer les migrations
python manage.py migrate

# 6. Charger les données initiales (Togo)
python manage.py init_togo_setup

# 7. Lancer le serveur
python manage.py runserver
```

### Accès
- **Landing page** : http://127.0.0.1:8000/
- **Connexion** : http://127.0.0.1:8000/accounts/login/

---

## 🔐 Comptes de démonstration

| Rôle | ID Employé | Mot de passe |
|------|------------|--------------|
| Administrateur | EMP007 | admin123 |
| RH/DG | EMP009 | password123 |
| Manager | EMP008 | password123 |
| Employé | EMP001 | password123 |

---

## 📁 Structure du projet

```
attendance_system/
├── accounts/              # Authentification & Gestion utilisateurs
│   ├── models.py         # Department, EmployeeProfile
│   ├── views.py          # Vues authentification
│   ├── hr_views.py       # Vues gestion RH
│   ├── user_services.py  # Services création utilisateurs
│   ├── notification_service.py  # Notifications email
│   └── auth_backend.py   # Authentification par employee_id
│
├── attendance/           # Gestion des présences
│   ├── models.py        # Attendance, AttendanceAnomaly
│   ├── views.py         # Pointage, historique
│   └── overtime_*.py    # Heures supplémentaires
│
├── leave/               # Gestion des congés
│   ├── models.py       # LeaveType, LeaveRequest, LeaveBalance, Holiday
│   ├── workflow_views.py  # Workflow de validation
│   ├── fixtures/       # Données Togo (types congés, jours fériés)
│   └── signals.py      # Création automatique soldes
│
├── reports/            # Rapports & Analytics
│   ├── report_views.py # Génération rapports
│   └── export_services.py  # Export Excel
│
├── templates/          # Templates HTML (35 pages)
│   ├── landing.html   # Page d'accueil
│   ├── base.html      # Template de base
│   ├── accounts/      # Auth, profil, emails
│   ├── dashboard/     # Tableaux de bord (4 rôles)
│   ├── hr/           # Gestion RH
│   ├── leave/        # Congés
│   └── attendance/   # Pointage
│
└── static/
    └── css/
        ├── design-system.css  # Design System
        └── style.css         # Styles globaux
```

---

## 🎨 Design System

Le projet utilise un Design System professionnel avec :
- Variables CSS (couleurs, espacements, typographie)
- Composants standardisés (boutons, cartes, formulaires, tableaux)
- Responsive mobile/tablette/desktop
- Règle des 8px pour les espacements
- Palette de couleurs cohérente (bleu principal)

---

## 📧 Configuration Email

### Mode Console (par défaut)
Les emails s'affichent dans le terminal avec un format amélioré.

### Mode Mailtrap (optionnel)
Voir `MAILTRAP_SETUP.md` pour la configuration.

---

## 🌍 Localisation Togo

Le système intègre les spécificités togolaises :
- **Types de congés** : Conformes au Code du travail togolais
- **Jours fériés 2025** : 10 jours fériés officiels
- **Samedi travaillé** : Pris en compte dans les calculs

---

## 🧪 Tests

```bash
# Vérifier le système
python manage.py check

# Tester les fonctionnalités
# 1. Créer un employé (RH)
# 2. Demander un congé (Employé)
# 3. Valider (Manager puis RH)
# 4. Pointer (Employé)
```

---

## 📝 Documentation

- `CONFIGURATION_EMAIL.md` - Configuration emails
- `MAILTRAP_SETUP.md` - Guide Mailtrap
- `NOTIFICATIONS_EXPLICATIONS.md` - Système de notifications

---

## 🎓 Pour la soutenance

### Démonstration recommandée

1. **Landing page** : Présentation du système
2. **Création employé** : Génération ID + Email
3. **Workflow congés** : Demande → Validation Manager → Validation RH
4. **Pointage GPS** : Démonstration géolocalisation
5. **Rapports** : Consultation des statistiques

### Arguments clés

- ✅ Conforme aux standards de l'industrie (SAP, Workday)
- ✅ Workflow de validation à 2 niveaux
- ✅ Sécurité renforcée (ID unique, changement mot de passe)
- ✅ Adapté au contexte togolais
- ✅ Design professionnel et responsive
- ✅ Notifications automatiques

---

## 👨‍💻 Auteur

**HUSUNUKPE Fabrice**  
Projet de fin de cycle - Licence en Architecture des Logiciels  
Année académique 2024-2025

---

## 📄 Licence

Projet académique - Tous droits réservés

---

**Version** : 1.0.0  
**Date** : Octobre 2025
