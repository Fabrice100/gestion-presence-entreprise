# 📋 Documentation Complète du Système de Gestion de Présence

**Date de création :** Décembre 2024  
**Version :** 1.0  
**Branche :** `full-project-snapshot`

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

Le système distingue **3 rôles principaux** :

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
   - Format d'affichage : "XhYYmin"

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
- Format d'affichage : "XhYYmin"

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
- `approved` : Approuvé définitivement
- `rejected` : Refusé (par manager ou RH)

**Déduction du Solde :**
- Se fait uniquement après validation RH finale
- Selon le type de congé (certains types déduisent, d'autres non)

---

### 👥 Workflow de Gestion Utilisateur (RH)

#### Création d'Utilisateur

```
1. RH clique sur "Nouveau Manager" ou "Nouvel Employé"
   ↓
2. Formulaire de création :
   - Nom, Prénom
   - Email (utilisé comme username)
   - Mot de passe (généré automatiquement ou défini)
   - Département
   - Manager (si employé)
   - Rôle (Manager ou Employé)
   - Profil horaire
   ↓
3. Système crée :
   - User Django
   - EmployeeProfile lié
   - Solde de congés initialisé
   ↓
4. Confirmation et affichage dans la liste
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
   - Format PDF (via bouton "Export PDF")
   - Format Excel (via bouton "Export Excel")
   ↓
6. Fichier téléchargé avec :
   - En-tête avec période
   - Tableau détaillé par employé
   - Totaux par département
   - Format : "XhYYmin"
```

**Exports Disponibles :**
- ✅ Rapport Heures travaillées (PDF/Excel) - **ACTIF**
- ❌ Rapport Anomalies - **DÉSACTIVÉ**
- ❌ Rapport Solde Congés - **DÉSACTIVÉ**

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
- ✅ Export Heures Travaillées : Actif (PDF et Excel)

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

### ✅ Fonctionnalités Actives
- Pointage entrée/sortie avec calcul automatique
- Gestion des demandes de congés
- Workflow de validation à deux niveaux (Manager → RH)
- Tableaux de bord par rôle
- Gestion RH complète (utilisateurs, départements, horaires)
- Export rapport heures travaillées (PDF/Excel)
- Désactivation/Réactivation d'utilisateurs
- Suppression conditionnelle d'utilisateurs

### ❌ Fonctionnalités Désactivées
- Gestion des anomalies de pointage
- Export rapport anomalies
- Export rapport solde congés
- Gestion des heures supplémentaires

---

**Document généré le :** Décembre 2024  
**Branche :** `full-project-snapshot`  
**Version du projet :** 1.0

