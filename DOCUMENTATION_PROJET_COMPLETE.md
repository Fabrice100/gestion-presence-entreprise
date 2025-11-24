# 📋 Documentation Complète du Système de Gestion de Présence

**Date de création :** Novembre 2025  
**Dernière mise à jour :** Novembre 2025  
**Version :** 1.0  
**Branche :** `full-project-snapshot`  
**État :** Fonctionnel complet - Prêt pour génération de diagrammes UML

---

## 📑 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du Système](#architecture-du-système)
3. [Acteurs et Rôles](#acteurs-et-rôles)
4. [Fonctionnalités par Rôle](#fonctionnalités-par-rôle)
5. [Workflows Détaillés](#workflows-détaillés)
6. [Modèles de Données](#modèles-de-données)
7. [Structure Technique](#structure-technique)
8. [Sécurité et Permissions](#sécurité-et-permissions)

---

## 🎯 Vue d'ensemble

**PresencePro** est un système de gestion de présence et de congés pour entreprises. Il permet aux employés de pointer, de demander des congés, et aux managers/RH de gérer et valider ces demandes.

### Objectifs Principaux
- ✅ Gestion du pointage (entrée/sortie) avec calcul automatique des heures travaillées
- ✅ Gestion des demandes de congés avec workflow de validation à deux niveaux
- ✅ Tableaux de bord adaptés par rôle (Employé, Manager, RH)
- ✅ Rapports et exports pour la paie
- ✅ Gestion des ressources humaines (utilisateurs, départements, horaires)

---

## 🏗️ Architecture du Système

### Stack Technologique
- **Backend :** Django 4.x (Python)
- **Base de données :** PostgreSQL (production) / SQLite (tests)
- **Frontend :** HTML5, TailwindCSS, Alpine.js
- **Exports :** ReportLab (PDF), OpenPyXL (Excel)

### Structure des Applications Django

```
attendance_system/
├── accounts/          # Gestion des utilisateurs et authentification
├── attendance/        # Module de pointage
├── leave/             # Module de gestion des congés
├── reports/           # Module de rapports et exports
└── common/            # Utilitaires partagés
```

---

## 👥 Acteurs et Rôles

Le système distingue **4 types d'acteurs** :

### 1. 👤 **EMPLOYÉ (Employee)**
- **Profil :** Utilisateur standard du système
- **Permissions :** 
  - Pointer (entrée/sortie)
  - Consulter ses propres présences
  - Demander des congés
  - Consulter ses propres demandes de congés

### 2. 👔 **MANAGER**
- **Profil :** Employé avec responsabilités managériales
- **Permissions :** 
  - Toutes les permissions d'un employé
  - Consulter les présences de son équipe
  - Valider les demandes de congés de son équipe (première validation)
  - Accéder au tableau de bord manager

### 3. 🏢 **RH (Ressources Humaines)**
- **Profil :** Administrateur RH avec accès complet
- **Permissions :** 
  - Toutes les permissions d'un manager
  - Validation finale des congés (après validation manager)
  - Gestion des utilisateurs (création, modification, désactivation, suppression)
  - Gestion des départements
  - Gestion des profils horaires
  - Accès aux rapports et exports
  - Tableau de bord RH avec statistiques globales

### 4. 🔧 **ADMIN (Administrateur Django)**
- **Profil :** Superutilisateur Django avec accès à l'interface d'administration
- **Accès :** `/admin/` (interface d'administration Django)
- **Permissions :** 
  - Accès complet à tous les modèles via l'interface admin Django
  - Gestion directe de la base de données
  - Configuration système avancée
  - Généralement utilisé pour la maintenance et la configuration initiale

**Note :** L'admin Django est distinct du rôle RH. Il s'agit d'un superutilisateur système, tandis que RH est un rôle métier dans l'application.

---

## 🎯 Fonctionnalités par Rôle

### 👤 EMPLOYÉ

#### Menu Disponible
- **Présence**
  - `Pointer` : Pointage entrée/sortie
  - `Mes Présences` : Historique des pointages
- **Congés**
  - `Mes Congés` : Gestion des demandes de congés

#### Actions Possibles
1. **Pointage**
   - Cliquer sur "Pointer" pour enregistrer une entrée ou sortie
   - Le système calcule automatiquement les heures travaillées
   - Affichage du dernier pointage et des heures du jour

2. **Consultation Présences**
   - Voir l'historique de ses pointages
   - Voir les heures travaillées par jour/semaine/mois
   - Format d'affichage : "X.XXh" (format décimal avec 2 décimales, ex: "8.50h")

3. **Demande de Congés**
   - Créer une nouvelle demande
   - Choisir le type de congé (Congés payés, Maladie, Autre)
   - Spécifier les dates de début et fin
   - Pour "Autre" : motif obligatoire
   - Suivre le statut de la demande (En attente, Validé manager, Validé RH, Refusé)

---

### 👔 MANAGER

#### Menu Disponible
- **Présence**
  - `Pointer` : Pointage personnel
  - `Mes Présences` : Présences personnelles
  - `Mon équipe` : Tableau de bord manager
- **Congés**
  - `Mes Congés` : Congés personnels
- **Validation**
  - `Valider Congés` : Validation des demandes de l'équipe

#### Actions Possibles
1. **Toutes les actions d'un employé** (pointage, congés personnels)

2. **Gestion de l'Équipe**
   - Voir les présences de l'équipe aujourd'hui
   - Voir les demandes de congés en attente de validation
   - Statistiques de l'équipe

3. **Validation des Congés**
   - Voir les demandes de congés de son équipe avec statut "En attente"
   - Approuver ou refuser les demandes
   - Commenter la décision
   - Après validation manager → statut passe à "Validé manager"

---

### 🏢 RH (Ressources Humaines)

#### Menu Disponible
- **Congés**
  - `Validation Finale` : Validation finale des congés
- **Ressources Humaines**
  - `Employés` : Liste et gestion des utilisateurs
  - `Départements` : Gestion des départements
  - `Profils Horaires` : Gestion des horaires de travail
- **Rapports**
  - `Heures travaillées` : Rapport et export des heures

#### Actions Possibles

1. **Validation Finale des Congés**
   - Voir les demandes avec statut "Validé manager"
   - Approuver ou refuser (validation finale)
   - Après validation RH → statut passe à "Approuvé" ou "Refusé"

2. **Gestion des Utilisateurs**
   - **Créer** : Nouveau manager ou nouvel employé
   - **Modifier** : Département, Manager, Rôle, Profil horaire
   - **Désactiver/Réactiver** : Activer ou désactiver un compte
   - **Supprimer** : Supprimer un utilisateur (uniquement s'il n'a pas de données : pointages ou demandes de congés)
   - **Affichage conditionnel** :
     - Utilisateurs avec données : 2 icônes (Modifier, Désactiver/Réactiver)
     - Utilisateurs sans données : 3 icônes (Modifier, Désactiver/Réactiver, Supprimer)

3. **Gestion des Départements**
   - Créer un département
   - Modifier un département (nom, description, manager)
   - Supprimer un département
   - Voir le nombre d'employés par département

4. **Gestion des Profils Horaires**
   - Créer des profils horaires (ex: 9h-17h, 8h-16h)
   - Modifier les horaires
   - Assigner un profil à un employé
   - Historique des changements de profil

5. **Rapports et Exports**
   - Consulter le rapport des heures travaillées
   - Exporter en PDF ou Excel (format : "XhYYmin")
   - Filtres par période, département, employé

---

## 🔄 Workflows Détaillés

### 📍 Workflow de Pointage

```
1. EMPLOYÉ accède à "Pointer"
   ↓
2. Système détecte le dernier pointage :
   - Si pas de pointage aujourd'hui → Bouton "Pointage Entrée"
   - Si pointage entrée existe → Bouton "Pointage Sortie"
   ↓
3. EMPLOYÉ clique sur le bouton
   ↓
4. Système enregistre :
   - Date et heure du pointage
   - Type (entrée/sortie)
   - Coordonnées GPS (si disponibles)
   ↓
5. Si pointage sortie :
   - Calcul automatique des heures travaillées
   - Prise en compte des pauses configurées
   - Application des caps horaires (min/max)
   ↓
6. Affichage de confirmation avec heures calculées
```

**Règles de Calcul :**
- Heures travaillées = Sortie - Entrée - Pauses
- Caps appliqués selon le profil horaire
- Format d'affichage : "X.XXh" (format décimal avec 2 décimales, ex: "8.50h")

**Validation GPS (ACTUELLEMENT ACTIVE) :**
- **Calcul de distance** : Formule de Haversine pour calculer la distance entre la position GPS de l'employé et le site de travail
- **Rayon autorisé** : 200 mètres par défaut (configurable dans `CompanySettings`)
- **Précision GPS** : Maximum 100 mètres (refus si précision insuffisante)
- **Mode démo** : Si GPS indisponible ou en mode démo, utilise automatiquement les coordonnées du bureau configurées
- **Fallback automatique** : Si les coordonnées GPS ne sont pas disponibles (0.0 ou vide), le système utilise les coordonnées du site configurées
- **Stockage** : Toutes les coordonnées GPS sont stockées dans `Attendance` (latitude, longitude, accuracy, distance_from_site)

**Validation de Zone :**
```
1. Récupération des coordonnées GPS (latitude, longitude, accuracy)
   ↓
2. Vérification de précision GPS :
   - Si accuracy > 100m → Refus avec message d'erreur
   - Sinon → Continuer
   ↓
3. Calcul distance (formule Haversine) :
   distance = 2 × R × arcsin(√(sin²(Δφ/2) + cos(φ1)×cos(φ2)×sin²(Δλ/2)))
   où R = 6371000 mètres (rayon de la Terre)
   ↓
4. Vérification rayon autorisé :
   - Si distance > 200m → Refus avec message d'erreur
   - Sinon → Pointage accepté
   ↓
5. Enregistrement avec coordonnées et distance
```

---

### 🏖️ Workflow de Demande de Congés

```
1. EMPLOYÉ crée une demande de congés
   ↓
2. Remplit le formulaire :
   - Type de congé (obligatoire)
   - Date début (obligatoire)
   - Date fin (obligatoire)
   - Motif (obligatoire si type = "Autre")
   ↓
3. Système vérifie :
   - Solde de congés disponible
   - Dates valides (début < fin)
   - Pas de chevauchement avec autres demandes
   ↓
4. Statut initial : "En attente"
   ↓
5. MANAGER reçoit notification (dans "Valider Congés")
   ↓
6. MANAGER décide :
   - ✅ Approuver → Statut : "Validé manager"
   - ❌ Refuser → Statut : "Refusé" (FIN)
   ↓
7. Si approuvé par manager :
   - RH reçoit notification (dans "Validation Finale")
   ↓
8. RH décide :
   - ✅ Approuver → Statut : "Approuvé" (FIN)
   - ❌ Refuser → Statut : "Refusé" (FIN)
   ↓
9. Si approuvé :
   - Déduction automatique du solde de congés
   - Notification à l'employé
```

**États Possibles :**
- `pending` : En attente de validation manager
- `approved_manager` : Validé par le manager, en attente RH
- `approved_rh` : Approuvé définitivement par RH
- `rejected_manager` : Refusé par le manager
- `rejected_rh` : Refusé par RH (rejet final)

**Déduction du Solde :**
- Se fait uniquement après validation RH finale (`approved_rh`)
- Selon le type de congé (champ `deducts_balance` dans `LeaveType`)
- Les types de congés qui déduisent : Congés payés, etc.
- Les types qui ne déduisent pas : Maladie (selon configuration)

**Notifications Email Automatiques (ACTUELLEMENT ACTIVES) :**
- ✅ **Email de bienvenue** : Envoyé automatiquement lors de la création de compte avec :
  - ID employé (format EMPXXX)
  - Mot de passe temporaire généré automatiquement
  - Lien de connexion
- ✅ **Notification d'approbation** : Envoyée automatiquement lorsque :
  - Manager approuve → Email "Demande validée par votre manager"
  - RH approuve → Email "Demande définitivement approuvée" avec solde restant
- ✅ **Notification de rejet** : Envoyée automatiquement avec :
  - Motif du rejet (commentaire obligatoire)
  - Niveau de rejet (manager ou RH)
  - Date de décision

**Gestion des Jours Fériés du Togo (ACTUELLEMENT ACTIVE) :**
- **Jours fériés fixes** : Jour de l'An (01-01), Fête du Travail (05-01), Fête Nationale (27-04), Noël (25-12)
- **Jours fériés variables (calculés automatiquement)** :
  - Lundi de Pâques (calculé selon algorithme de Pâques)
  - Ascension (39 jours après Pâques)
  - Lundi de Pentecôte (50 jours après Pâques)
  - Assomption (15-08)
  - Toussaint (01-11)
- **Vérification automatique** : Le système vérifie automatiquement si une période de congé chevauche un jour férié
- **Types de jours fériés** : `national`, `regional`, `company`, `religious`
- **Jours fériés récurrents** : Support des jours fériés qui se répètent chaque année

---

### 👥 Workflow de Gestion Utilisateur (RH)

#### Création d'Utilisateur

```
1. RH clique sur "Nouveau Manager" ou "Nouvel Employé"
   ↓
2. Formulaire de création :
   - Nom, Prénom
   - Email (utilisé comme username - partie avant @)
   - Mot de passe : GÉNÉRÉ AUTOMATIQUEMENT (8 caractères aléatoires sécurisés)
   - Département
   - Manager (si employé)
   - Rôle (Manager ou Employé)
   - Profil horaire
   ↓
3. Système crée (TRANSACTION ATOMIQUE) :
   - Génération ID employé unique : EMPXXX (XXX = nombre aléatoire 100-999)
   - User Django avec username généré depuis email
   - EmployeeProfile lié avec :
     - employee_id = EMPXXX
     - force_password_change = True (OBLIGATOIRE)
     - is_active = True
     - can_punch = True (si role = employee ou manager)
   - Solde de congés initialisé (LeaveBalance)
   ↓
4. Envoi automatique email de bienvenue avec :
   - ID employé (EMPXXX)
   - Mot de passe temporaire
   - Lien de connexion
   ↓
5. Confirmation et affichage dans la liste
```

#### Modification d'Utilisateur

```
1. RH clique sur l'icône "Modifier" (crayon bleu)
   ↓
2. Formulaire pré-rempli avec :
   - Département (modifiable)
   - Manager (modifiable)
   - Rôle (modifiable)
   - Profil horaire (modifiable)
   ↓
3. RH modifie et sauvegarde
   ↓
4. Mise à jour immédiate dans la liste
```

#### Désactivation/Réactivation

```
1. RH clique sur l'icône "Désactiver" (power rouge) ou "Réactiver" (+ vert)
   ↓
2. POST direct vers l'endpoint toggle-active
   ↓
3. Système change is_active :
   - Désactiver : is_active = False
   - Réactiver : is_active = True
   ↓
4. Utilisateur ne peut plus se connecter si désactivé
```

#### Suppression d'Utilisateur

```
1. RH clique sur l'icône "Supprimer" (poubelle rouge)
   ↓
2. Modal JavaScript de confirmation
   ↓
3. Si confirmé :
   - POST direct vers l'endpoint delete
   ↓
4. Système vérifie :
   - A-t-il des pointages ? → Bloque suppression
   - A-t-il des demandes de congés ? → Bloque suppression
   ↓
5. Si aucune donnée :
   - Suppression de EmployeeProfile
   - Suppression du User Django
   - Message de succès
   ↓
6. Si données existent :
   - Message d'erreur : "Impossible de supprimer, désactivez à la place"
   - Redirection vers la liste
```

**Règles de Suppression :**
- ✅ Peut supprimer : Utilisateur sans pointages ET sans demandes de congés
- ❌ Ne peut pas supprimer : Utilisateur avec pointages OU demandes de congés
- 💡 Alternative : Désactiver au lieu de supprimer

**Génération Automatique d'ID Employé (ACTUELLEMENT ACTIVE) :**
- **Format** : EMPXXX où XXX est un nombre aléatoire entre 100 et 999
- **Génération** : Algorithme qui génère un nombre aléatoire et vérifie l'unicité dans la base de données
- **Fallback** : Si tous les IDs 100-999 sont pris, utilise 001-099 avec padding zéro
- **Rôles** : Tous les rôles utilisent le même format EMPXXX (pas de distinction MGR/RH dans l'ID)
- **Exemples** : EMP472, EMP819, EMP156, EMP003
- **Implémentation** : Méthode `UserService.generate_employee_id(role)` dans `accounts/user_services.py`

**Changement de Mot de Passe Obligatoire (ACTUELLEMENT ACTIF) :**
- **Flag** : `force_password_change = True` sur `EmployeeProfile` lors de la création
- **Middleware** : `ForcePasswordChangeMiddleware` intercepte toutes les requêtes authentifiées
- **Comportement** :
  - Si `force_password_change = True` → Redirection automatique vers `/accounts/force-password-change/`
  - Bloque l'accès à toutes les pages sauf : logout, changement MDP, static files, media
  - Après changement réussi → `force_password_change = False` et accès normal au système
- **Sécurité** : Empêche l'utilisation de comptes avec mot de passe temporaire
- **Implémentation** : Middleware dans `accounts/force_password_middleware.py`, Vue dans `accounts/force_password_views.py`

---

### 📊 Workflow de Génération de Rapport

```
1. RH accède à "Heures travaillées"
   ↓
2. Sélectionne les filtres :
   - Période (début, fin)
   - Département (optionnel)
   - Employé (optionnel)
   ↓
3. Système calcule :
   - Heures travaillées par employé
   - Total par département
   - Total global
   ↓
4. Affichage du rapport dans l'interface
   ↓
5. RH peut exporter :
   - **Dashboard rapports** : Format PDF ou Excel (via boutons "Export Paie (PDF)" et "Export Paie (Excel)")
   - **Rapport heures travaillées** : Format Excel uniquement (via bouton "Excel")
   - **Backend** : Support complet PDF et Excel (PayrollReportExportView)
   ↓
6. Fichier téléchargé avec :
   - En-tête avec période
   - Tableau détaillé par employé
   - Format heures : "X.XXh" (format décimal avec 2 décimales, ex: "8.50h")
   - Note : Sans ligne TOTAL (conformité PME)
```

**Exports Disponibles :**
- ✅ Rapport Heures travaillées - **ACTIF**
  - **Backend** : Support PDF et Excel (PayrollReportExportView)
  - **Interface Dashboard** : Boutons "Export Paie (PDF)" et "Export Paie (Excel)" dans le dashboard rapports
  - **Interface Rapport** : Bouton "Excel" uniquement dans le rapport heures travaillées
  - Formats : PDF (.pdf) et Excel (.xlsx)
  - Note : Sans heures supplémentaires, sans ligne TOTAL (conformité PME)
- ❌ Rapport Anomalies - **DÉSACTIVÉ** (code commenté dans report_exports.py)
- ❌ Rapport Solde Congés - **DÉSACTIVÉ** (code commenté dans report_exports.py, lien commenté dans leave_report.html)

---

## 🗄️ Modèles de Données

### Core Models

#### `User` (Django Auth)
- Champs standards Django : username, email, password, etc.
- Relation : `OneToOne` avec `EmployeeProfile`

#### `EmployeeProfile`
- `user` : OneToOne avec User
- `employee_id` : Identifiant unique employé
- `department` : ForeignKey vers Department
- `manager` : ForeignKey vers User (peut être null)
- `role` : CharField (choices: 'employee', 'manager', 'rh')
- `is_active` : Boolean (actif/désactivé)
- `current_work_schedule` : ForeignKey vers WorkSchedule

#### `Department`
- `name` : Nom du département
- `description` : Description
- `manager` : ForeignKey vers User (manager du département)

#### `WorkSchedule`
- `name` : Nom du profil (ex: "9h-17h")
- `start_time` : Heure de début
- `end_time` : Heure de fin
- `break_duration` : Durée de pause
- `min_hours` : Heures minimum
- `max_hours` : Heures maximum

#### `EmployeeScheduleHistory`
- Historique des changements de profil horaire
- `employee` : ForeignKey vers User
- `work_schedule` : ForeignKey vers WorkSchedule
- `start_date` : Date de début
- `end_date` : Date de fin (null si actuel)

### Attendance Models

#### `Attendance`
- `employee` : ForeignKey vers User
- `date` : Date du pointage
- `punch_in` : Heure d'entrée
- `punch_out` : Heure de sortie (null si pas encore sorti)
- `punch_type` : 'in' ou 'out'
- `worked_hours` : Decimal (heures travaillées calculées)
- `gps_latitude` : Latitude GPS (optionnel)
- `gps_longitude` : Longitude GPS (optionnel)

### Leave Models

#### `LeaveType`
- `name` : Nom du type (ex: "Congés payés", "Maladie")
- `deducts_balance` : Boolean (déduit-il du solde ?)
- `requires_reason` : Boolean (motif obligatoire ?)

#### `LeaveRequest`
- `employee` : ForeignKey vers User
- `leave_type` : ForeignKey vers LeaveType
- `start_date` : Date de début
- `end_date` : Date de fin
- `reason` : TextField (motif, optionnel selon type)
- `status` : CharField (choices: 'pending', 'approved_manager', 'approved', 'rejected')
- `manager_comment` : Commentaire du manager
- `rh_comment` : Commentaire du RH
- `created_at` : Date de création
- `updated_at` : Date de mise à jour

#### `LeaveBalance`
- `employee` : ForeignKey vers User
- `leave_type` : ForeignKey vers LeaveType
- `balance` : Decimal (solde disponible)
- `year` : Année du solde

---

## 🛠️ Structure Technique

### URLs Principales

#### Accounts
- `/accounts/login/` : Connexion
- `/accounts/logout/` : Déconnexion
- `/accounts/password-change/` : Changement de mot de passe

#### Dashboard
- `/dashboard/employee/` : Dashboard employé
- `/dashboard/manager/` : Dashboard manager
- `/dashboard/rh/` : Dashboard RH

#### Attendance
- `/attendance/punch/` : Pointage
- `/attendance/my-attendance/` : Mes présences

#### Leave
- `/leave/` : Mes congés (vue unifiée)
- `/leave/approval/` : Validation congés (manager)
- `/leave/approval/final/` : Validation finale (RH)

#### HR
- `/hr/users/` : Liste utilisateurs
- `/hr/users/managers/create/` : Créer manager
- `/hr/users/employees/create/` : Créer employé
- `/hr/users/<id>/edit/` : Modifier utilisateur
- `/hr/users/<id>/delete/` : Supprimer utilisateur
- `/hr/users/<id>/toggle-active/` : Désactiver/Réactiver
- `/hr/departments/` : Liste départements
- `/hr/departments/create/` : Créer département
- `/hr/departments/<id>/edit/` : Modifier département
- `/hr/departments/<id>/delete/` : Supprimer département
- `/hr/schedules/` : Liste profils horaires
- `/hr/schedules/create/` : Créer profil horaire
- `/hr/schedules/<id>/edit/` : Modifier profil horaire
- `/hr/schedules/<id>/delete/` : Supprimer profil horaire

#### Reports
- `/reports/` : Tableau de bord rapports
- `/reports/attendance/` : Rapport heures travaillées
- `/reports/export/payroll/<format>/` : Export (pdf/excel)

### Mixins de Sécurité

#### `LoginRequiredMixin`
- Vérifie que l'utilisateur est authentifié
- Redirige vers login si non authentifié

#### `HRRequiredMixin` (alias de `RHRequiredMixin`)
- Vérifie que l'utilisateur a le rôle 'rh'
- Redirige vers dashboard si non autorisé
- Utilisé pour toutes les vues HR

### Services Métier

#### `UserService`
- `create_employee_with_credentials()` : Création employé avec credentials
- `create_manager_with_credentials()` : Création manager avec credentials

#### `LeaveService`
- `create_leave_request()` : Création demande de congés
- `approve_leave_request()` : Approbation demande
- `reject_leave_request()` : Refus demande
- `deduct_leave_balance()` : Déduction solde

#### `AttendanceService`
- `punch_in()` : Pointage entrée
- `punch_out()` : Pointage sortie
- `calculate_worked_hours()` : Calcul heures travaillées

---

## 🔒 Sécurité et Permissions

### Contrôles d'Accès

1. **Authentification Requise**
   - Toutes les pages (sauf login) nécessitent une authentification
   - Redirection automatique vers `/accounts/login/` si non authentifié

2. **Contrôle par Rôle**
   - Vérification du rôle dans les vues sensibles
   - Mixins dédiés (`HRRequiredMixin`)
   - Templates conditionnels (`{% if user.employee_profile.role == 'rh' %}`)

3. **Protection CSRF**
   - Tous les formulaires incluent `{% csrf_token %}`
   - Middleware CSRF activé

4. **Validation des Données**
   - Validation côté serveur pour tous les formulaires
   - Vérification des permissions avant actions critiques (suppression, validation)

### Règles Métier

1. **Suppression Utilisateur**
   - Bloquée si présence de données (pointages ou demandes de congés)
   - Alternative : désactivation

2. **Validation Congés**
   - Workflow à deux niveaux obligatoire (Manager → RH)
   - Pas de validation directe RH sauf si pas de manager

3. **Pointage**
   - Un seul pointage entrée par jour
   - Pointage sortie nécessite un pointage entrée
   - Calcul automatique avec règles métier

---

## 📝 Notes Importantes

### Exports Désactivés
- ❌ Export Anomalies : Désactivé (fonctionnalité non utilisée)
- ❌ Export Solde Congés : Désactivé (fonctionnalité non utilisée)
- ✅ Export Heures Travaillées : Actif (Excel uniquement dans l'interface)

### Interface Utilisateur
- **Framework CSS :** TailwindCSS (pas Bootstrap)
- **JavaScript :** Alpine.js pour l'interactivité
- **Icons :** SVG inline (pas de dépendance externe)
- **Design :** Moderne, responsive, dark mode supporté

### Base de Données
- **Production :** PostgreSQL
- **Tests :** SQLite (automatique)
- **Migrations :** Toutes appliquées et à jour

---

## 🎯 Résumé des Fonctionnalités Actives

### ✅ Fonctionnalités Actives (État Fonctionnel Actuel)

#### 📍 Pointage
- ✅ Pointage entrée/sortie avec calcul automatique des heures travaillées
- ✅ Validation GPS avec calcul de distance (formule Haversine)
- ✅ Validation de zone autorisée (rayon 200m par défaut)
- ✅ Vérification de précision GPS (max 100m)
- ✅ Mode démo / Fallback automatique si GPS indisponible
- ✅ Stockage des coordonnées GPS (latitude, longitude, accuracy, distance)

#### 🏖️ Congés
- ✅ Gestion des demandes de congés
- ✅ Workflow de validation à deux niveaux (Manager → RH)
- ✅ Vérification automatique du solde disponible
- ✅ Détection des chevauchements
- ✅ Gestion des jours fériés du Togo (fixes et variables)
- ✅ Calcul automatique des jours fériés religieux (Pâques, Ascension, Pentecôte)
- ✅ Déduction automatique du solde après validation RH finale

#### 📧 Notifications
- ✅ Email de bienvenue automatique avec credentials
- ✅ Notification d'approbation (manager et RH)
- ✅ Notification de rejet avec motif

#### 👥 Gestion Utilisateurs
- ✅ Création automatique avec génération d'ID (EMPXXX)
- ✅ Génération automatique de mot de passe sécurisé (8 caractères)
- ✅ Changement de mot de passe obligatoire à la première connexion
- ✅ Envoi automatique des credentials par email
- ✅ Gestion RH complète (utilisateurs, départements, horaires)
- ✅ Désactivation/Réactivation d'utilisateurs
- ✅ Suppression conditionnelle d'utilisateurs (sans données)

#### 📊 Rapports
- ✅ Tableaux de bord par rôle
- ✅ Export rapport heures travaillées :
  - **Dashboard rapports** : PDF et Excel disponibles
  - **Rapport heures travaillées** : Excel uniquement dans l'interface
  - **Backend** : Support complet PDF et Excel (PayrollReportExportView)

### ❌ Fonctionnalités Désactivées
- ❌ Gestion des anomalies de pointage (module désactivé)
- ❌ Export rapport anomalies
- ❌ Export rapport solde congés
- ❌ Gestion des heures supplémentaires (fonctionnalité non active)

---

---

## 📊 Structure pour Diagrammes UML

Ce document décrit l'état fonctionnel actuel du système. Il peut être utilisé pour générer les diagrammes suivants :

### Diagrammes de Cas d'Utilisation
**Acteurs identifiés :**
- Employé
- Manager
- RH (Ressources Humaines)
- Admin (Superutilisateur Django)

**Cas d'utilisation principaux :**
1. **Pointage**
   - Pointer entrée (Employé, Manager, RH)
   - Pointer sortie (Employé, Manager, RH)
   - Consulter ses présences (Employé, Manager, RH)

2. **Gestion Congés**
   - Demander congé (Employé, Manager, RH)
   - Valider congé manager (Manager)
   - Valider congé RH (RH)
   - Consulter ses congés (Employé, Manager, RH)

3. **Gestion Utilisateurs**
   - Créer utilisateur (RH)
   - Modifier utilisateur (RH)
   - Désactiver/Réactiver utilisateur (RH)
   - Supprimer utilisateur (RH)

4. **Rapports**
   - Consulter rapport heures travaillées (RH)
   - Exporter rapport PDF (RH) - Dashboard uniquement
   - Exporter rapport Excel (RH) - Dashboard et Rapport heures

### Diagrammes de Séquence
**Workflows détaillés décrits :**
- Workflow de Pointage (avec validation GPS)
- Workflow de Demande de Congés (2 niveaux de validation)
- Workflow de Création d'Utilisateur (avec génération ID et envoi email)
- Workflow de Validation Congés (Manager → RH)

### Diagrammes d'Activité
**Processus métier décrits :**
- Processus de pointage avec validation GPS
- Processus de demande et validation de congés
- Processus de création de compte utilisateur

### Diagrammes de Classes
**Modèles de données documentés :**
- User, EmployeeProfile, Department, WorkSchedule
- Attendance (avec champs GPS)
- LeaveRequest, LeaveType, LeaveBalance, Holiday
- Relations et contraintes détaillées

---

**Document généré le :** Novembre 2025  
**Branche :** `full-project-snapshot`  
**Version du projet :** 1.0  
**Dernière mise à jour :** Novembre 2025  
**État :** Fonctionnel complet - Prêt pour génération de diagrammes UML

