# 👥 GUIDE DES RÔLES - Système de Gestion de Présence

## 📋 Vue d'ensemble des acteurs

Le système comprend **4 types d'acteurs** avec des permissions distinctes :

| Acteur | Code | Employee ID | Peut pointer | Django Admin | Dashboard |
|--------|------|-------------|--------------|--------------|-----------|
| **Administrateur système** | `admin` | ❌ Aucun | ❌ Non | ✅ Full access | Admin |
| **RH/Direction Générale** | `rh_dg` | ✅ EMPXXX | ❌ Non | ⚠️ Limité | RH |
| **Manager/Chef de service** | `manager` | ✅ EMPXXX | ✅ Oui | ❌ Non | Manager |
| **Employé** | `employee` | ✅ EMPXXX | ✅ Oui | ❌ Non | Employé |

---

## 1️⃣ ADMINISTRATEUR SYSTÈME

### 🎯 Identité

**Compte type:** `admin`  
**Username:** `admin`  
**Employee ID:** Aucun (n'a pas de `EmployeeProfile`)  
**Accès Django Admin:** ✅ Complet (`is_superuser=True`, `is_staff=True`)  

### 📌 Responsabilités principales

#### 1. Gestion technique du système

**Accès Django Admin complet:**
```
/admin/
├── Authentication and Authorization
│   ├── Users (création, modification, suppression)
│   └── Groups (gestion des groupes)
├── Accounts
│   ├── EmployeeProfiles (tous les profils)
│   └── Departments (départements)
├── Attendance
│   ├── Attendances (tous les pointages)
│   ├── CompanySettings (configuration GPS + horaires)
│   └── OvertimeRecords (heures supplémentaires)
├── Leave
│   ├── LeaveRequests (toutes les demandes)
│   ├── LeaveTypes (types de congés)
│   ├── LeaveBalances (soldes)
│   └── Holidays (jours fériés)
└── Reports
    └── AttendanceReports (rapports)
```

#### 2. Configuration du système

**A. Configuration GPS (ACCÈS EXCLUSIF)**

```python
# Seul le superadmin peut modifier ces paramètres
CompanySettings:
├── site_center_latitude: 6.3654 (Cotonou par défaut)
├── site_center_longitude: 2.4183
├── allowed_radius_meters: 200 (rayon autorisé en mètres)
└── gps_accuracy_max_meters: 100 (précision max GPS)
```

**Exemples de coordonnées (villes africaines):**
```
Cotonou (Bénin):    6.3654°N, 2.4183°E
Abidjan (Côte d'Ivoire): 5.3600°N, -4.0083°W
Dakar (Sénégal):    14.6928°N, -17.4467°W
Paris (France):     48.8566°N, 2.3522°E
```

**B. Configuration horaires de travail**

```python
CompanySettings:
├── work_start_time: 08:00 (début journée)
├── work_end_time: 17:00 (fin journée)
├── late_tolerance_minutes: 15 (tolérance retard)
├── half_day_hours: 4.0 (heures demi-journée)
└── full_day_hours: 8.0 (heures journée complète)
```

#### 3. Gestion des utilisateurs

**Création de comptes:**
- Créer des utilisateurs via Django Admin
- Assigner rôles (`employee`, `manager`, `rh_dg`)
- Définir `is_staff`, `is_superuser`
- Réinitialiser mots de passe

**Modification de profils:**
- Changer département
- Assigner manager
- Activer/désactiver `can_punch`
- Activer/désactiver `is_active`

#### 4. Supervision globale

**Accès à toutes les données:**
```sql
-- Voir tous les pointages
SELECT * FROM attendance_attendance;

-- Voir toutes les demandes de congés
SELECT * FROM leave_leaverequest;

-- Statistiques globales
SELECT 
    COUNT(*) as total_pointages,
    COUNT(DISTINCT employee_id) as nb_employes,
    DATE(created_at) as date
FROM attendance_attendance
GROUP BY DATE(created_at);
```

**Rapports disponibles:**
- Pointages par département
- Retards par employé
- Congés par période
- Heures supplémentaires

### ❌ Limitations

**Ne peut PAS:**
- Pointer (pas d'EmployeeProfile)
- Soumettre demandes de congés
- Apparaître dans organigramme
- Recevoir notifications métier

**Pourquoi?**
L'admin est un **compte technique** pour la maintenance, pas un employé de l'entreprise.

### 🔐 Sécurité

**Protection configuration GPS:**

1. **Niveau Vue (`CompanySettingsView`):**
```python
def get_form_fields(self, request):
    if request.user.is_superuser:
        # Superuser: tous les champs
        return ['site_center_latitude', 'site_center_longitude', 
                'allowed_radius_meters', 'gps_accuracy_max_meters',
                'work_start_time', 'work_end_time', ...]
    elif request.user.employee_profile.role == 'rh_dg':
        # RH: uniquement horaires (pas GPS)
        return ['work_start_time', 'work_end_time', ...]
    else:
        # Autres: accès refusé
        return redirect('dashboard:dashboard')
```

2. **Niveau Admin (`CompanySettingsAdmin`):**
```python
def get_readonly_fields(self, request, obj=None):
    if request.user.is_superuser:
        return ('updated_at',)  # Tout modifiable
    else:
        # Non-superuser: GPS en lecture seule
        return ('updated_at', 'site_center_latitude', 
                'site_center_longitude', 'allowed_radius_meters',
                'gps_accuracy_max_meters')

def save_model(self, request, obj, form, change):
    if not request.user.is_superuser:
        # Vérifier si GPS modifié
        if change:
            old_obj = CompanySettings.objects.get(pk=obj.pk)
            if (old_obj.site_center_latitude != obj.site_center_latitude or
                old_obj.site_center_longitude != obj.site_center_longitude):
                # REFUSER la modification
                messages.error(request, 
                    "Seul le superadmin peut modifier les coordonnées GPS.")
                # Revenir aux anciennes valeurs
                obj.site_center_latitude = old_obj.site_center_latitude
                obj.site_center_longitude = old_obj.site_center_longitude
    
    super().save_model(request, obj, form, change)
```

### 📊 Dashboard Admin

**URL:** `/admin/`

**Fonctionnalités:**
- Vue d'ensemble des modèles
- Recherche/filtrage avancé
- Export CSV
- Actions groupées
- Historique des modifications (Django Admin History)

---

## 2️⃣ RH / DIRECTION GÉNÉRALE

### 🎯 Identité

**Compte type:** `rh_dg`  
**Username:** Généré depuis email (ex: `rh.dg`)  
**Employee ID:** Format EMPXXX (ex: `EMP365`)  
**Accès Django Admin:** ⚠️ Limité (peut voir CompanySettings en lecture seule)  

### 📌 Responsabilités principales

#### 1. Gestion des employés

**A. Création d'employés**

**URL:** `/hr/employees/create/`

**Formulaire de création:**
```python
Informations personnelles:
├── first_name: Prénom (requis)
├── last_name: Nom (requis)
├── email: Email professionnel (requis, unique)
└── phone: Téléphone (optionnel)

Informations professionnelles:
├── role: Choix (employee, manager, rh_dg)
├── department: Département (sélection)
├── manager: Manager direct (si role=employee)
└── hire_date: Date d'embauche

Génération automatique:
├── employee_id: EMPXXX (aléatoire 100-999)
├── username: Depuis email (avant @)
└── password: 8 caractères sécurisés
```

**Processus:**
```
1. RH remplit le formulaire
2. Soumission → UserService.create_employee_with_credentials()
3. Génération automatique:
   - employee_id = 'EMP472' (aléatoire)
   - username = 'fabrice.h' (depuis email)
   - password = 'Kz9@mT2p' (sécurisé)
4. Transaction atomique:
   - Création User
   - Mise à jour EmployeeProfile
   - force_password_change = True
5. Email de bienvenue envoyé à l'employé
6. Affichage des credentials (à communiquer)
```

**Exemple email de bienvenue:**
```
Objet: Bienvenue chez [Entreprise] - Vos identifiants

Bonjour Fabrice HUSUNUKPE,

Bienvenue dans notre entreprise !

Vos identifiants de connexion:
- ID Employé: EMP472
- Nom d'utilisateur: fabrice.h
- Mot de passe temporaire: Kz9@mT2p

Première connexion:
1. Accédez à https://presence.entreprise.com
2. Connectez-vous avec vos identifiants
3. Changez votre mot de passe (obligatoire)

Cordialement,
Service RH
```

**B. Modification d'employés**

**URL:** `/hr/employees/<id>/edit/`

**Champs modifiables:**
```python
Profil:
├── first_name, last_name
├── email, phone
├── department
├── manager
├── hire_date
└── is_active (activer/désactiver)

Permissions:
├── can_punch (autoriser pointage)
└── force_password_change (forcer changement)

⚠️ NON modifiables:
├── employee_id (fixe à vie)
├── username (fixe à vie)
└── role (nécessite validation admin)
```

**C. Liste des employés**

**URL:** `/hr/employees/`

**Fonctionnalités:**
- Vue tableau complète
- Recherche (nom, email, employee_id)
- Filtres (département, rôle, actif/inactif)
- Export CSV
- Actions groupées (désactiver, envoyer notification)

#### 2. Validation finale des congés

**A. Workflow de validation**

```
Employé soumet demande
        ↓
Manager approuve (si employé a manager)
        ↓
    ┌───────────────────┐
    │   RH/DG valide    │ ← DÉCISION FINALE
    │  (approved_rh)    │
    └─────────┬─────────┘
              │
    ┌─────────┴──────────┐
    │   ✅ Approuvé      │ ❌ Rejeté
    │                    │
    │ • Déduction solde  │ • Solde intact
    │ • Email employé    │ • Email raison
    └────────────────────┘
```

**URL:** `/leave/approval/`

**Liste des demandes à valider:**
```python
Filtres disponibles:
├── status = 'approved_manager' (en attente RH)
├── status = 'pending' (si manager a soumis directement)
└── Tous statuts (pour suivi)

Informations affichées:
├── Employé (nom, employee_id)
├── Période (start_date → end_date)
├── Durée (duration_days)
├── Type de congé (leave_type)
├── Solde disponible
├── Raison (reason)
├── Décision manager (si applicable)
└── Actions: [Approuver] [Rejeter]
```

**B. Approbation**

**Processus:**
```python
1. RH clique "Approuver" sur demande
2. Formulaire de validation:
   ├── action: 'approve'
   └── comment: Commentaire optionnel
3. Transaction atomique:
   ├── leave_request.rh_decision = 'approved_rh'
   ├── leave_request.rh_comment = comment
   ├── leave_request.status = 'approved_rh'
   └── DÉDUCTION SOLDE:
       └── balance.taken_balance += duration_days
4. Email employé: "Congé approuvé ✅"
```

**Validation du solde:**
```python
# Avant déduction
balance.allocated_balance = 20 jours/an
balance.taken_balance = 5 jours
balance.remaining_balance = 15 jours

# Demande: 5 jours
duration_days = 5

# Après approbation RH
balance.taken_balance = 10 jours
balance.remaining_balance = 10 jours
```

**C. Rejet**

**Processus:**
```python
1. RH clique "Rejeter"
2. Formulaire:
   ├── action: 'reject'
   └── comment: Raison du rejet (OBLIGATOIRE)
3. Transaction:
   ├── leave_request.rh_decision = 'rejected_rh'
   ├── leave_request.rh_comment = comment
   └── leave_request.status = 'rejected_rh'
4. Email employé: "Congé rejeté ❌ - Raison: [comment]"
5. Solde: NON déduit (reste intact)
```

#### 3. Configuration des horaires

**URL:** `/attendance/settings/` (ou `/admin/attendance/companysettings/`)

**Champs modifiables par RH:**
```python
✅ AUTORISÉ:
├── work_start_time: 08:00
├── work_end_time: 17:00
├── late_tolerance_minutes: 15
├── break_duration_minutes: 60
├── half_day_hours: 4.0
├── full_day_hours: 8.0
└── overtime_threshold_hours: 8.0

❌ LECTURE SEULE (GPS - Superuser uniquement):
├── site_center_latitude: 6.3654
├── site_center_longitude: 2.4183
├── allowed_radius_meters: 200
└── gps_accuracy_max_meters: 100
```

**Exemple de modification:**
```
Scénario: Entreprise passe à 35h/semaine

Avant:
- work_start_time: 08:00
- work_end_time: 17:00
- full_day_hours: 8.0 (8h × 5j = 40h/semaine)

Après (modification RH):
- work_start_time: 08:30 ← Modifié
- work_end_time: 16:30 ← Modifié
- full_day_hours: 7.0 ← Modifié (7h × 5j = 35h/semaine)

✅ Sauvegarde OK (pas de GPS modifié)
```

**Si RH tente de modifier GPS:**
```
Scénario: RH veut déplacer le bureau

Tentative:
- site_center_latitude: 6.3654 → 5.3600 (Abidjan)

Résultat:
❌ Erreur: "Seul le superadmin peut modifier les coordonnées GPS."
🔒 Valeurs GPS restaurées automatiquement
```

#### 4. Rapports et statistiques

**A. Rapports de présence**

**URL:** `/reports/attendance/`

**Filtres:**
```python
Période:
├── Aujourd'hui
├── Cette semaine
├── Ce mois
├── Personnalisée (start_date, end_date)

Par employé:
├── Employé spécifique (select)
└── Tous les employés

Par département:
├── Département spécifique
└── Tous départements

Par statut:
├── Présent
├── Absent
├── Retard
└── Sortie anticipée
```

**Données affichées:**
```python
Tableau:
├── Employé (nom, employee_id)
├── Date
├── Arrivée (time)
├── Sortie (time)
├── Durée (hours)
├── Statut (normal, late, early)
└── Distance GPS (meters)

Statistiques:
├── Taux présence: 95%
├── Nombre retards: 12
├── Heures travaillées: 1,280h
└── Heures supplémentaires: 45h
```

**Export:**
```
Formats disponibles:
├── CSV (Excel)
├── PDF (impression)
└── Excel (XLSX)
```

**B. Rapports de congés**

**URL:** `/reports/leave/`

**Données:**
```python
Par employé:
├── Solde alloué (allocated_balance)
├── Solde pris (taken_balance)
├── Solde restant (remaining_balance)
├── Congés en cours
└── Congés à venir

Statistiques globales:
├── Total jours congés pris (entreprise)
├── Moyenne jours/employé
├── Départements les plus absents
└── Prévisions (congés à venir)
```

**C. Tableau de bord RH**

**URL:** `/dashboard/rh/`

**Vue d'ensemble:**
```
┌─────────────────────────────────────────┐
│       TABLEAU DE BORD RH/DG             │
├─────────────────────────────────────────┤
│ Employés:                               │
│   ├─ Total: 45 employés                 │
│   ├─ Actifs: 42                         │
│   └─ Inactifs: 3                        │
├─────────────────────────────────────────┤
│ Présences aujourd'hui:                  │
│   ├─ Présents: 38/42 (90%)              │
│   ├─ Retards: 4                         │
│   └─ Absents: 4                         │
├─────────────────────────────────────────┤
│ Congés:                                 │
│   ├─ En attente validation: 7 demandes  │
│   ├─ Approuvées ce mois: 12             │
│   └─ En cours: 5 employés               │
├─────────────────────────────────────────┤
│ Alertes:                                │
│   ├─ ⚠️ Soldes congés épuisés: 2        │
│   ├─ ⚠️ Retards répétés: 3 employés     │
│   └─ ℹ️ Congés à venir (7j): 8          │
└─────────────────────────────────────────┘
```

### ❌ Limitations

**Ne peut PAS:**
- Pointer (can_punch = False dans init_database.py)
- Modifier configuration GPS (lecture seule)
- Accéder à Django Admin complet (seulement CompanySettings)
- Supprimer des utilisateurs (seulement désactiver)

### 🔐 Permissions

**Mixins appliqués:**
```python
class EmployeeCreateView(RHRequiredMixin, CreateView):
    # Seul RH peut accéder
    pass

class RHRequiredMixin(EmployeeRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.employee_profile.role != 'rh_dg':
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
```

---

## 3️⃣ MANAGER / CHEF DE SERVICE

### 🎯 Identité

**Compte type:** `manager`  
**Username:** Généré depuis email (ex: `manager.it`)  
**Employee ID:** Format EMPXXX (ex: `EMP197`)  
**Accès Django Admin:** ❌ Non  
**Peut pointer:** ✅ Oui (`can_punch = True`)  

### 📌 Responsabilités principales

#### 1. Gestion de l'équipe

**A. Vue d'ensemble de l'équipe**

**URL:** `/dashboard/manager/`

**Tableau de bord Manager:**
```
┌─────────────────────────────────────────┐
│     TABLEAU DE BORD MANAGER             │
├─────────────────────────────────────────┤
│ Mon équipe:                             │
│   ├─ Total: 8 employés                  │
│   ├─ Présents: 7/8 (87%)                │
│   └─ En congé: 1                        │
├─────────────────────────────────────────┤
│ Présences aujourd'hui:                  │
│   ├─ À l'heure: 6                       │
│   ├─ En retard: 1                       │
│   └─ Absents: 1                         │
├─────────────────────────────────────────┤
│ Congés à valider:                       │
│   ├─ En attente: 3 demandes             │
│   └─ Approuvées ce mois: 5              │
├─────────────────────────────────────────┤
│ Actions rapides:                        │
│   ├─ [Valider congés]                   │
│   ├─ [Voir présences équipe]            │
│   └─ [Pointer]                          │
└─────────────────────────────────────────┘
```

**B. Liste des employés managés**

**Requête:**
```python
# Employés dont manager = current_user
managed_employees = User.objects.filter(
    employee_profile__manager=request.user,
    employee_profile__is_active=True
).select_related('employee_profile__department')
```

**Affichage:**
```
Employé              | ID      | Département | Statut
---------------------|---------|-------------|--------
Fabrice HUSUNUKPE    | EMP472  | IT          | Présent
Marie KOUADIO        | EMP583  | IT          | Retard
Jean ATCHA           | EMP291  | IT          | Absent
...
```

#### 2. Validation des congés (1ère étape)

**A. Workflow Manager**

```
Employé (mon équipe) soumet demande
        ↓
    ┌───────────────────┐
    │  Manager valide   │ ← ÉTAPE 1
    │ (approved_manager)│
    └─────────┬─────────┘
              │
    ┌─────────┴──────────┐
    │ ✅ Approuvé        │ ❌ Rejeté
    │ → RH/DG valide     │ → Demande terminée
    └────────────────────┘
```

**URL:** `/leave/approval/`

**Liste des demandes:**
```python
# Requête: Employés managés par current_user
leave_requests = LeaveRequest.objects.filter(
    employee__employee_profile__manager=request.user,
    status='pending'
).select_related('employee', 'leave_type')
```

**Informations affichées:**
```
Employé: Fabrice HUSUNUKPE (EMP472)
Période: 01/02/2025 → 05/02/2025 (5 jours)
Type: Congé annuel
Raison: "Vacances familiales"
Solde: 15 jours disponibles

Actions:
[Approuver] [Rejeter]
```

**B. Approbation Manager**

**Processus:**
```python
1. Manager clique "Approuver"
2. Formulaire:
   ├── action: 'approve'
   └── comment: "Bon voyage !" (optionnel)
3. Transaction:
   ├── leave_request.manager_decision = 'approved_manager'
   ├── leave_request.manager_comment = comment
   ├── leave_request.manager_decision_at = timezone.now()
   └── leave_request.status = 'approved_manager'
4. Email employé: "Demande approuvée par manager ✅"
5. Email RH/DG: "Nouvelle demande à valider (validée par manager)"
6. SOLDE: Pas encore déduit (attente validation RH)
```

**C. Rejet Manager**

**Processus:**
```python
1. Manager clique "Rejeter"
2. Formulaire:
   ├── action: 'reject'
   └── comment: "Période trop chargée" (OBLIGATOIRE)
3. Transaction:
   ├── leave_request.manager_decision = 'rejected_manager'
   ├── leave_request.manager_comment = comment
   └── leave_request.status = 'rejected_manager'
4. Email employé: "Demande rejetée par manager ❌"
5. RH: NON notifié (demande terminée)
6. SOLDE: Intact
```

**Note importante:**
```
Si Manager rejette → Demande TERMINÉE
(RH ne voit jamais la demande)

Si Manager approuve → RH doit valider
(Décision finale à RH/DG)
```

#### 3. Suivi des présences de l'équipe

**URL:** `/attendance/team/`

**Filtres:**
```python
Période:
├── Aujourd'hui (par défaut)
├── Cette semaine
├── Ce mois
└── Personnalisée

Statut:
├── Tous
├── Présents
├── Retards
└── Absents
```

**Tableau:**
```
Date       | Employé           | Arrivée | Sortie | Durée | Statut
-----------|-------------------|---------|--------|-------|--------
22/10/2024 | Fabrice HUSUNUKPE | 08:05   | 17:10  | 9h05  | Normal
22/10/2024 | Marie KOUADIO     | 08:45   | 17:00  | 8h15  | Retard
22/10/2024 | Jean ATCHA        | --      | --     | --    | Absent
```

**Actions Manager:**
```python
Actions disponibles:
├── Export CSV (équipe)
├── Envoyer rappel (email absent)
├── Signaler à RH (retards répétés)
└── Commentaire (note sur pointage)
```

#### 4. Pointage personnel

**Le Manager est AUSSI un employé** → peut pointer comme les autres.

**URL:** `/attendance/punch/`

**Processus identique aux employés:**
```
1. Clic "Pointer"
2. GPS récupéré (navigateur)
3. Validation:
   ├── Distance < 200m ✅
   └── Précision < 100m ✅
4. Pointage créé
5. Message: "Pointage arrivée enregistré à 08:15"
```

**Données enregistrées:**
```python
Attendance:
├── employee = manager (User object)
├── date = today
├── time = current_time
├── punch_type = 'in' ou 'out'
├── latitude, longitude, gps_accuracy
├── distance_from_site (calculé Haversine)
├── status = 'normal', 'late', ou 'early'
└── source = 'web'
```

#### 5. Demandes de congés personnelles

**Le Manager peut soumettre ses propres demandes.**

**URL:** `/leave/request/create/`

**Particularité:**
```python
# Si role = 'manager'
if request.user.employee_profile.role == 'manager':
    # Auto-approbation Manager
    leave_request.status = 'approved_manager'
    leave_request.manager_decision = 'auto_approved'
    
    # Notification directe à RH/DG
    rh_users = User.objects.filter(
        employee_profile__role='rh_dg',
        employee_profile__is_active=True
    )
    for rh in rh_users:
        NotificationService.send_leave_pending_notification(
            leave_request, rh
        )
```

**Workflow:**
```
Manager soumet demande
        ↓
Status = 'approved_manager' (auto)
        ↓
RH/DG valide (décision finale)
        ↓
Approuvé/Rejeté
```

### ❌ Limitations

**Ne peut PAS:**
- Valider congés d'employés hors de son équipe
- Modifier configuration horaires (réservé à RH)
- Voir présences employés d'autres départements
- Créer/modifier des employés (réservé à RH)
- Accéder Django Admin

**Peut uniquement gérer:**
- Employés dont `manager = current_user`
- Ses propres pointages
- Ses propres demandes de congés

### 🔐 Permissions

**Mixins appliqués:**
```python
class LeaveApprovalListView(ManagerRequiredMixin, ListView):
    # Seul Manager (ou RH) peut accéder
    
    def get_queryset(self):
        # Filtrer: seulement employés managés
        managed_employees = User.objects.filter(
            employee_profile__manager=self.request.user
        )
        return LeaveRequest.objects.filter(
            employee__in=managed_employees,
            status='pending'
        )
```

---

## 4️⃣ EMPLOYÉ

### 🎯 Identité

**Compte type:** `employee`  
**Username:** Généré depuis email (ex: `fabrice.h`)  
**Employee ID:** Format EMPXXX (ex: `EMP472`)  
**Accès Django Admin:** ❌ Non  
**Peut pointer:** ✅ Oui (`can_punch = True`)  

### 📌 Responsabilités principales

#### 1. Pointage quotidien

**A. Interface de pointage**

**URL:** `/attendance/punch/`

**Écran:**
```
┌─────────────────────────────────────────┐
│          POINTAGE PRÉSENCE              │
├─────────────────────────────────────────┤
│ Employé: Fabrice HUSUNUKPE (EMP472)     │
│ Date: 22/10/2024                        │
│ Heure: 08:14:35                         │
├─────────────────────────────────────────┤
│ Dernier pointage:                       │
│   ✅ Arrivée à 08:05 (ce matin)         │
├─────────────────────────────────────────┤
│ Prochain pointage:                      │
│   📍 Sortie                             │
├─────────────────────────────────────────┤
│ Localisation:                           │
│   🌍 GPS activé                         │
│   📍 Position: 6.3670°N, 2.4200°E       │
│   📏 Distance bureau: 185m ✅           │
│   🎯 Précision: 12m ✅                  │
├─────────────────────────────────────────┤
│         [Pointer la sortie]             │
│                                         │
│   ☑️ Mode Démo (tests)                  │
└─────────────────────────────────────────┘
```

**B. Processus de pointage**

**Étape 1: Récupération GPS (JavaScript)**
```javascript
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        function(position) {
            // Succès
            document.getElementById('latitude').value = position.coords.latitude;
            document.getElementById('longitude').value = position.coords.longitude;
            document.getElementById('accuracy').value = position.coords.accuracy;
        },
        function(error) {
            // Échec → Fallback coordonnées bureau
            useFallbackCoordinates();
        }
    );
}
```

**Étape 2: Soumission formulaire**
```html
<form method="POST" action="/attendance/punch/">
    <input type="hidden" name="punch_type" value="out">
    <input type="hidden" name="latitude" value="6.3670">
    <input type="hidden" name="longitude" value="2.4200">
    <input type="hidden" name="accuracy" value="12">
    <button type="submit">Pointer</button>
</form>
```

**Étape 3: Validation serveur (PunchView.post())**
```python
# 1. Validation formulaire
form = PunchForm(request.POST)

# 2. Vérification permissions
can_punch = AttendanceBusinessRules.can_user_punch(user)

# 3. Parsing GPS
gps_parsed = GPSValidationService.parse_gps_data(...)

# 4. Validation GPS
validation = GPSValidationService.validate_location(
    latitude, longitude, accuracy,
    site_lat, site_lon,
    allowed_radius=200,  # mètres
    max_accuracy=100     # mètres
)

# 5. Calcul distance (Haversine)
distance = GPSValidationService.calculate_distance(
    6.3670, 2.4200,  # Position employé
    6.3654, 2.4183   # Position bureau
)
# Résultat: 185 mètres

# 6. Vérifications
if distance > 200:
    return Error("Trop loin du bureau")
if accuracy > 100:
    return Error("Précision GPS insuffisante")

# 7. Création pointage
attendance = AttendanceService.create_punch(
    user, 'out', gps_data, request_meta
)
```

**Étape 4: Confirmation**
```
✅ Pointage sortie enregistré à 17:05
Distance bureau: 185m
Bonne soirée !
```

**C. Modes de pointage**

**Mode Normal (GPS actif):**
```python
Données utilisées:
├── latitude: Depuis GPS navigateur
├── longitude: Depuis GPS navigateur
├── accuracy: Précision GPS (mètres)
└── Validation stricte (distance + précision)
```

**Mode Démo (tests sans GPS):**
```python
Données utilisées:
├── latitude: Coordonnées bureau (fallback)
├── longitude: Coordonnées bureau (fallback)
├── accuracy: 5m (parfait)
└── Validation assouplie
```

**Mode Fallback (GPS indisponible):**
```python
Si GPS désactivé/bloqué:
├── Utilise coordonnées bureau automatiquement
├── accuracy: 100m (moyenne)
└── Message: "⚠️ GPS non disponible, coordonnées bureau utilisées"
```

**D. Règles de pointage**

**Vérification doublons:**
```python
# Impossible de pointer 2 fois "arrivée" le même jour
existing = Attendance.objects.filter(
    employee=user,
    date=today,
    punch_type='in'
).exists()

if existing:
    return Error("Pointage d'entrée déjà effectué aujourd'hui")
```

**Ordre cohérent:**
```python
# Impossible de pointer "sortie" sans "arrivée"
if punch_type == 'out':
    has_entry = Attendance.objects.filter(
        employee=user,
        date=today,
        punch_type='in'
    ).exists()
    
    if not has_entry:
        return Error("Impossible de pointer sortie sans arrivée")
```

**Détection statut:**
```python
if punch_type == 'in':
    # Arrivée
    if current_time > (work_start + late_tolerance):
        status = 'late'  # Retard
        minutes_late = calcul_retard()
    else:
        status = 'normal'

elif punch_type == 'out':
    # Sortie
    if current_time < work_end:
        status = 'early'  # Sortie anticipée
    else:
        status = 'normal'
```

#### 2. Consultation historique des pointages

**URL:** `/attendance/history/`

**Filtres:**
```python
Période:
├── Aujourd'hui
├── Cette semaine
├── Ce mois
└── Personnalisée (start_date, end_date)

Statut:
├── Tous
├── Normal
├── Retard
└── Sortie anticipée
```

**Tableau:**
```
Date       | Arrivée | Sortie | Durée | Distance | Statut
-----------|---------|--------|-------|----------|--------
22/10/2024 | 08:05   | 17:05  | 9h00  | 185m     | Normal
21/10/2024 | 08:35   | 17:00  | 8h25  | 120m     | Retard
20/10/2024 | 08:10   | 16:45  | 8h35  | 95m      | Sortie anticipée
```

**Statistiques personnelles:**
```
Ce mois:
├── Jours travaillés: 18
├── Retards: 2 (11%)
├── Heures travaillées: 145h30
├── Moyenne journée: 8h05
└── Distance moyenne GPS: 132m
```

#### 3. Demandes de congés

**A. Soumission de demande**

**URL:** `/leave/request/create/`

**Formulaire:**
```python
Type de congé:
├── Congé annuel (20 jours alloués)
├── Maladie (illimité, justificatif)
├── Congé sans solde
└── Autre (maternité, paternité...)

Période:
├── start_date: 01/02/2025
├── end_date: 05/02/2025
└── duration_days: 5 jours (calculé auto)

Raison:
└── reason: "Vacances familiales" (textarea)

Pièce jointe (optionnel):
└── attachment: [Choisir fichier]
```

**Validations:**
```python
# 1. Solde disponible
balance = LeaveBalance.objects.get(
    employee=user,
    leave_type=selected_type,
    year=2025
)

if balance.remaining_balance < 5:
    return Error(f"Solde insuffisant: {balance.remaining_balance} jours")

# 2. Chevauchement
overlapping = LeaveRequest.objects.filter(
    employee=user,
    start_date__lte='05/02/2025',
    end_date__gte='01/02/2025',
    status__in=['pending', 'approved_manager', 'approved_rh']
).exists()

if overlapping:
    return Error("Vous avez déjà une demande sur cette période")

# 3. Dates cohérentes
if start_date > end_date:
    return Error("Date début > date fin")
```

**Soumission:**
```python
with transaction.atomic():
    leave_request = LeaveRequest.objects.create(
        employee=user,
        leave_type=selected_type,
        start_date='01/02/2025',
        end_date='05/02/2025',
        duration_days=5,
        reason="Vacances familiales",
        status='pending',
        manager=user.employee_profile.manager
    )

# Email manager
NotificationService.send_leave_pending_notification(
    leave_request, user.employee_profile.manager
)
```

**Confirmation:**
```
✅ Demande de congé créée avec succès ! (5 jours)

Statut: En attente validation manager
Validateur: Jean KOUADIO (Manager IT)

Votre demande sera traitée sous 48h.
Vous recevrez un email de notification.
```

**B. Suivi des demandes**

**URL:** `/leave/requests/`

**Liste:**
```
Demande #47
├── Période: 01/02/2025 → 05/02/2025 (5 jours)
├── Type: Congé annuel
├── Statut: ⏳ En attente validation manager
├── Soumise le: 22/10/2024 à 14:30
└── Actions: [Annuler]

Demande #42
├── Période: 15/01/2025 → 19/01/2025 (5 jours)
├── Type: Congé annuel
├── Statut: ✅ Approuvée (RH/DG)
├── Validée le: 10/10/2024
└── Commentaire RH: "Bon voyage !"

Demande #38
├── Période: 10/12/2024 → 14/12/2024 (5 jours)
├── Type: Congé annuel
├── Statut: ❌ Rejetée (Manager)
├── Rejetée le: 01/10/2024
└── Raison: "Période de fin d'année trop chargée"
```

**C. Consultation soldes**

**URL:** `/leave/balance/`

**Tableau:**
```
Type de congé     | Alloué | Pris | Restant | En attente
------------------|--------|------|---------|------------
Congé annuel      | 20j    | 10j  | 10j     | 5j
Maladie           | ∞      | 2j   | ∞       | 0j
Congé sans solde  | ∞      | 0j   | ∞       | 0j

Légende:
- Alloué: Total annuel
- Pris: Congés déjà consommés (approved_rh)
- Restant: Disponible (alloué - pris)
- En attente: Demandes pending/approved_manager
```

#### 4. Tableau de bord personnel

**URL:** `/dashboard/employee/`

**Vue:**
```
┌─────────────────────────────────────────┐
│      TABLEAU DE BORD EMPLOYÉ            │
├─────────────────────────────────────────┤
│ Bienvenue, Fabrice !                    │
│ Employee ID: EMP472                     │
├─────────────────────────────────────────┤
│ Aujourd'hui (22/10/2024):               │
│   ✅ Arrivée: 08:05 (à l'heure)         │
│   ⏳ Sortie: En attente                 │
│   ⏱️  Temps écoulé: 8h54                │
├─────────────────────────────────────────┤
│ Ce mois:                                │
│   ✅ Jours travaillés: 18/22            │
│   ⚠️  Retards: 2                        │
│   ✅ Heures: 145h30/176h                │
├─────────────────────────────────────────┤
│ Congés:                                 │
│   ✅ Solde disponible: 10 jours         │
│   ⏳ Demandes en attente: 1             │
│   📅 Prochains congés: 01/02/2025       │
├─────────────────────────────────────────┤
│ Actions rapides:                        │
│   [Pointer] [Nouvelle demande congé]    │
└─────────────────────────────────────────┘
```

#### 5. Changement de mot de passe

**A. Premier mot de passe (force_password_change)**

**Scénario:**
```
1. RH crée employé → password temporaire: 'Kz9@mT2p'
2. Employé se connecte → Redirection automatique
3. Formulaire changement:
   ├── old_password: 'Kz9@mT2p'
   ├── new_password1: 'MonPass@2024'
   └── new_password2: 'MonPass@2024' (confirmation)
4. Validation:
   ├── Longueur min: 8 caractères ✅
   ├── Pas trop commun ✅
   └── Pas entièrement numérique ✅
5. Mise à jour:
   ├── user.set_password('MonPass@2024')
   └── profile.force_password_change = False
6. Redirection: Dashboard employé
```

**B. Changement volontaire**

**URL:** `/accounts/password/change/`

**Formulaire standard Django:**
```python
Champs:
├── old_password: Mot de passe actuel
├── new_password1: Nouveau mot de passe
└── new_password2: Confirmation

Validations:
├── Ancien mot de passe correct
├── Nouveau ≠ ancien
├── Nouveau ≥ 8 caractères
└── new_password1 == new_password2
```

### ❌ Limitations

**Ne peut PAS:**
- Voir pointages d'autres employés
- Valider demandes de congés
- Modifier configuration (horaires, GPS)
- Créer d'autres utilisateurs
- Accéder Django Admin
- Modifier son employee_id, username

**Peut uniquement:**
- Pointer (ses propres pointages)
- Soumettre demandes de congés
- Consulter son historique
- Modifier son mot de passe

### 🔐 Permissions

**Mixins appliqués:**
```python
class PunchView(EmployeeRequiredMixin, TemplateView):
    # Tous les employés actifs peuvent pointer
    pass

class LeaveRequestCreateView(EmployeeRequiredMixin, CreateView):
    # Tous les employés peuvent demander congés
    
    def form_valid(self, form):
        leave_request = form.save(commit=False)
        leave_request.employee = self.request.user  # ← Forcé
        leave_request.save()
```

---

## 📊 Tableau récapitulatif des permissions

| Fonctionnalité | Admin | RH/DG | Manager | Employee |
|----------------|-------|-------|---------|----------|
| **Pointage GPS** | ❌ | ❌ | ✅ | ✅ |
| **Consulter ses pointages** | ❌ | ❌ | ✅ | ✅ |
| **Voir pointages équipe** | ❌ | ❌ | ✅ (équipe) | ❌ |
| **Voir tous les pointages** | ✅ (admin) | ✅ (rapports) | ❌ | ❌ |
| **Soumettre demande congé** | ❌ | ❌ | ✅ | ✅ |
| **Valider congés (étape 1)** | ❌ | ❌ | ✅ (équipe) | ❌ |
| **Valider congés (final)** | ❌ | ✅ | ❌ | ❌ |
| **Voir soldes congés** | ✅ (admin) | ✅ (tous) | ✅ (perso) | ✅ (perso) |
| **Créer employés** | ✅ (admin) | ✅ | ❌ | ❌ |
| **Modifier employés** | ✅ (admin) | ✅ | ❌ | ❌ |
| **Configurer GPS** | ✅ | ❌ (lecture) | ❌ | ❌ |
| **Configurer horaires** | ✅ | ✅ | ❌ | ❌ |
| **Rapports présence** | ✅ (admin) | ✅ (tous) | ✅ (équipe) | ✅ (perso) |
| **Rapports congés** | ✅ (admin) | ✅ (tous) | ✅ (équipe) | ✅ (perso) |
| **Django Admin complet** | ✅ | ❌ | ❌ | ❌ |
| **Changer mot de passe** | ✅ | ✅ | ✅ | ✅ |

---

## 🔄 Workflows complets

### Workflow 1: Création d'un employé

```
1. RH se connecte → /hr/employees/create/

2. RH remplit formulaire:
   ├── Nom: HUSUNUKPE
   ├── Prénom: Fabrice
   ├── Email: fabrice.h@entreprise.com
   ├── Rôle: employee
   ├── Département: IT
   └── Manager: manager.it

3. Soumission → UserService.create_employee_with_credentials()
   ├── Génération employee_id: EMP472 (aléatoire)
   ├── Génération username: fabrice.h (depuis email)
   ├── Génération password: Kz9@mT2p (sécurisé)
   ├── Création User + EmployeeProfile (transaction)
   └── force_password_change = True

4. Email envoyé à fabrice.h@entreprise.com:
   "Vos identifiants: EMP472 / fabrice.h / Kz9@mT2p"

5. RH voit confirmation:
   "✅ Employé créé avec succès
   Username: fabrice.h
   Password temporaire: Kz9@mT2p
   (À communiquer à l'employé)"

6. Employé se connecte → Redirection changement mot de passe

7. Employé change mot de passe → Accès dashboard
```

### Workflow 2: Pointage d'un employé

```
1. Employé ouvre /attendance/punch/
   └── Voit: Dernier pointage (arrivée à 08:05)
   └── Prochain: Sortie

2. Clic "Pointer la sortie"
   └── JavaScript récupère GPS:
       ├── latitude: 6.3670°N
       ├── longitude: 2.4200°E
       └── accuracy: 12m

3. Soumission formulaire → PunchView.post()

4. Validation PunchForm:
   ├── punch_type: 'out' ✅
   ├── latitude: 6.3670 (-90 à 90) ✅
   ├── longitude: 2.4200 (-180 à 180) ✅
   └── accuracy: 12 (< 100) ✅

5. Vérification permissions:
   └── AttendanceBusinessRules.can_user_punch(user)
       ├── has employee_profile ✅
       ├── can_punch = True ✅
       └── is_active = True ✅

6. Parsing GPS:
   └── GPSValidationService.parse_gps_data()
       ├── Mode: Normal (pas démo)
       ├── lat: 6.3670 ✅
       ├── lon: 2.4200 ✅
       └── acc: 12m ✅

7. Validation GPS:
   └── GPSValidationService.validate_location()
       ├── Calcul distance (Haversine):
       │   └── distance = 185m
       ├── Vérif distance < 200m ✅
       └── Vérif accuracy < 100m ✅

8. Création pointage:
   └── AttendanceService.create_punch() [transaction atomic]
       └── Attendance.objects.create(
           employee=user,
           date=22/10/2024,
           time=17:05,
           punch_type='out',
           latitude=6.3670,
           longitude=2.4200,
           gps_accuracy=12,
           distance_from_site=185,
           status='normal',
           source='web'
       )

9. Message succès:
   "✅ Pointage sortie enregistré à 17:05"

10. Redirection → /attendance/punch/
```

### Workflow 3: Demande de congé (employé)

```
1. Employé: /leave/request/create/

2. Formulaire:
   ├── Type: Congé annuel
   ├── Début: 01/02/2025
   ├── Fin: 05/02/2025
   ├── Durée: 5 jours (auto)
   └── Raison: "Vacances familiales"

3. Soumission → LeaveRequestCreateView.form_valid()

4. Vérifications pré-transaction:
   ├── Solde disponible:
   │   └── balance.remaining_balance = 15 jours
   │   └── duration = 5 jours ✅ (15 ≥ 5)
   └── Chevauchement:
       └── Aucune demande sur période ✅

5. Transaction atomique:
   └── LeaveRequest.objects.create(
       employee=user,
       leave_type=conge_annuel,
       start_date=01/02/2025,
       end_date=05/02/2025,
       duration_days=5,
       reason="Vacances familiales",
       status='pending',
       manager=user.employee_profile.manager
   )

6. Email manager:
   "Nouvelle demande de congé à valider
   Employé: Fabrice HUSUNUKPE (EMP472)
   Période: 01/02 - 05/02 (5j)
   [Consulter demande]"

7. Message employé:
   "✅ Demande créée avec succès ! (5 jours)
   Statut: En attente validation manager"

--- Manager valide ---

8. Manager: /leave/approval/
   └── Voit demande (status='pending')

9. Manager clique "Approuver" + commentaire "Bon voyage !"

10. Transaction:
    ├── leave_request.manager_decision = 'approved_manager'
    ├── leave_request.manager_comment = "Bon voyage !"
    ├── leave_request.status = 'approved_manager'
    └── leave_request.manager_decision_at = now()

11. Email employé:
    "✅ Demande approuvée par manager
    Commentaire: Bon voyage !"

12. Email RH:
    "Nouvelle demande à valider (validée par manager)
    [Consulter]"

--- RH valide ---

13. RH: /leave/approval/
    └── Voit demande (status='approved_manager')

14. RH clique "Approuver définitivement"

15. Transaction atomique:
    ├── leave_request.rh_decision = 'approved_rh'
    ├── leave_request.status = 'approved_rh'
    ├── leave_request.rh_decision_at = now()
    └── Déduction solde:
        ├── balance.taken_balance = 10 → 15
        └── balance.remaining_balance = 15 → 10

16. Email employé:
    "✅ Demande approuvée définitivement (RH/DG)
    Période: 01/02 - 05/02 (5j)
    Nouveau solde: 10 jours"

17. Employé: /leave/requests/
    └── Voit demande (status='approved_rh' ✅)
```

---

## 📞 Support et aide

**Pour chaque acteur:**

| Acteur | Contact support | Documentation |
|--------|----------------|---------------|
| **Admin** | admin@entreprise.com | ARCHITECTURE.md, Django Admin docs |
| **RH/DG** | support@entreprise.com | GUIDE_INSTALLATION.md, FAQ RH |
| **Manager** | support@entreprise.com | Guide Manager (ce document) |
| **Employee** | support@entreprise.com | Guide Employé (section 4) |

---

## 📄 Conclusion

Ce guide détaille les **4 rôles** du système avec :
- ✅ **Responsabilités** de chaque acteur
- ✅ **Permissions** (ce qu'il peut/ne peut pas faire)
- ✅ **Workflows** complets (création employé, pointage, congés)
- ✅ **Limitations** et sécurité
- ✅ **Tableaux récapitulatifs**

**Architecture basée sur:**
- 🔐 Principe du moindre privilège
- 🎯 Séparation claire des responsabilités
- 🔄 Workflows de validation multi-niveaux
- 📊 Traçabilité complète (qui fait quoi, quand)

---

© 2024 - Système de Gestion de Présence  
Guide des rôles et permissions - Version 2.0
