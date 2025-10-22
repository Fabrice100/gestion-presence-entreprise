# 🏗️ Documentation d'Architecture - Système de Gestion de Présence

## Vue d'ensemble

Le système utilise une **architecture Django modulaire** avec séparation des responsabilités selon les principes **SOLID**.

### Architecture globale

```
┌─────────────────────────────────────────────────────────┐
│                    NAVIGATEUR WEB                       │
│  (HTML5 Geolocation API, Bootstrap 5, JavaScript)      │
└────────────┬────────────────────────────────────────────┘
             │ HTTPS
             ▼
┌─────────────────────────────────────────────────────────┐
│              DJANGO APPLICATION SERVER                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Middleware Layer                        │   │
│  │  • Authentication                               │   │
│  │  • ForcePasswordChange                          │   │
│  │  • CSRF Protection                              │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         URL Routing                             │   │
│  │  • accounts/     → Authentification             │   │
│  │  • attendance/   → Pointages                    │   │
│  │  • leave/        → Congés                       │   │
│  │  • reports/      → Rapports                     │   │
│  │  • dashboard/    → Tableaux de bord             │   │
│  │  • hr/           → Interface RH                 │   │
│  │  • admin/        → Django Admin                 │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Views Layer (MTV Pattern)               │   │
│  │  • PunchView (pointage GPS)                     │   │
│  │  • LeaveRequestCreateView (demandes congé)      │   │
│  │  • DashboardView (tableaux de bord)             │   │
│  │  • CompanySettingsView (configuration)          │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Service Layer (Business Logic)          │   │
│  │  • UserService (génération ID, credentials)     │   │
│  │  • GPSValidationService (calcul Haversine)      │   │
│  │  • AttendanceBusinessRules (règles métier)      │   │
│  │  • AttendanceService (orchestration)            │   │
│  │  • NotificationService (emails)                 │   │
│  │  • OvertimeCalculationService (heures sup)      │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Forms Layer (Validation)                │   │
│  │  • PunchForm (validation GPS)                   │   │
│  │  • LeaveRequestForm (validation congés)         │   │
│  │  • CompanySettingsForm (validation config)      │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Models Layer (ORM)                      │   │
│  │  • User (Django Auth)                           │   │
│  │  • EmployeeProfile                              │   │
│  │  • Attendance                                   │   │
│  │  • LeaveRequest, LeaveType, LeaveBalance        │   │
│  │  • CompanySettings                              │   │
│  └─────────────────────────────────────────────────┘   │
└────────────┬────────────────────────────────────────────┘
             │ ORM
             ▼
┌─────────────────────────────────────────────────────────┐
│              DATABASE (SQLite / PostgreSQL)              │
│  • auth_user, accounts_employeeprofile                  │
│  • attendance_attendance                                │
│  • leave_leaverequest, leave_leavetype, leave_leavebal  │
│  • attendance_companysettings                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Modules principaux

### 1. Module `accounts` - Authentification & Utilisateurs

**Responsabilité:** Gestion des utilisateurs, profils employés, permissions

**Fichiers clés:**
```
accounts/
├── models.py              # EmployeeProfile (rôle, can_punch, employee_id)
├── views.py               # Connexion, déconnexion, changement mot de passe
├── dashboard_views.py     # Tableaux de bord par rôle
├── hr_views.py            # Interface RH (création employés)
├── user_services.py       # Services métier
│   ├── generate_employee_id()      # Format EMPXXX
│   ├── generate_random_password()  # 8 chars sécurisés
│   ├── create_employee_with_credentials()  # Transaction atomique
├── notification_service.py # Envoi d'emails
└── middleware.py          # ForcePasswordChangeMiddleware
```

**Modèle de données:**
```python
# User (Django built-in)
- username: CharField (unique)
- email: EmailField
- first_name, last_name: CharField
- is_staff, is_superuser: BooleanField

# EmployeeProfile (One-to-One avec User)
- employee_id: CharField (EMPXXX, unique)
- role: CharField (employee, manager, rh_dg)
- department: ForeignKey(Department)
- manager: ForeignKey(User, null=True)
- can_punch: BooleanField (True pour employee/manager)
- is_active: BooleanField
- force_password_change: BooleanField
```

**Flux de création d'employé:**
```
1. RH remplit le formulaire → hr_views.EmployeeCreateView
2. Validation du formulaire → forms.EmployeeCreationForm
3. Appel du service → UserService.create_employee_with_credentials()
   ├─ Génération employee_id (EMPXXX aléatoire)
   ├─ Génération username (from email)
   ├─ Génération password (8 chars sécurisé)
   ├─ Création User (transaction atomique)
   └─ Mise à jour EmployeeProfile (auto-créé par signal)
4. Envoi email → NotificationService.send_welcome_email()
5. Redirection + message succès
```

---

### 2. Module `attendance` - Gestion des pointages

**Responsabilité:** Pointage GPS, validation localisation, calcul heures

**Fichiers clés:**
```
attendance/
├── models.py              # Attendance (date, time, punch_type, GPS)
├── views.py               # PunchView (interface pointage)
├── forms.py               # PunchForm, PunchAPIForm (validation)
├── attendance_service.py  # Services métier
│   ├── GPSValidationService
│   │   ├── calculate_distance()    # Formule Haversine
│   │   ├── validate_accuracy()     # Vérif précision
│   │   ├── validate_location()     # Vérif distance + précision
│   │   └── parse_gps_data()        # Parsing + demo mode
│   ├── AttendanceBusinessRules
│   │   ├── can_user_punch()        # Permissions
│   │   └── get_next_punch_type()   # in/out
│   └── AttendanceService
│       ├── create_punch()          # Création avec transaction
│       └── get_today_attendances() # Requête optimisée
├── admin_models.py        # CompanySettings (configuration GPS)
├── settings_views.py      # CompanySettingsView (sécurité superuser)
├── overtime_service.py    # Calcul heures supplémentaires
└── admin.py               # Django Admin avec sécurité GPS
```

**Modèle de données:**
```python
# Attendance
- employee: ForeignKey(User)
- date: DateField
- time: TimeField
- punch_type: CharField (choices: 'in', 'out')
- latitude: DecimalField (nullable)
- longitude: DecimalField (nullable)
- gps_accuracy: DecimalField (nullable)
- distance_from_site: DecimalField (nullable)
- status: CharField (normal, late, early)
- source: CharField (web, mobile, api)
- ip_address: GenericIPAddressField
- user_agent: CharField

# CompanySettings (Singleton)
- site_center_latitude: DecimalField
- site_center_longitude: DecimalField
- allowed_radius_meters: IntegerField (200m par défaut)
- gps_accuracy_max_meters: IntegerField (100m par défaut)
- work_start_time: TimeField (08:00)
- work_end_time: TimeField (17:00)
- late_tolerance_minutes: IntegerField (15)
```

**Flux de pointage GPS:**
```
1. Employé clique "Pointer" → PunchView.get()
   └─ Charge CompanySettings (coordonnées bureau)

2. Navigateur récupère GPS → JavaScript Geolocation API
   ├─ Si succès: envoie latitude, longitude, accuracy
   └─ Si échec: fallback coordonnées bureau OU mode démo

3. Soumission formulaire → PunchView.post()
   ├─ Validation formulaire → PunchForm.is_valid()
   │   ├─ punch_type: 'in' ou 'out' (required)
   │   ├─ latitude: -90 à 90 (optional)
   │   ├─ longitude: -180 à 180 (optional)
   │   └─ accuracy: 0 à 10000 (optional)
   │
   ├─ Vérification permissions → AttendanceBusinessRules.can_user_punch()
   │   └─ Vérifie: employee_profile.can_punch == True
   │
   ├─ Parsing GPS → GPSValidationService.parse_gps_data()
   │   ├─ Mode démo: utilise coordonnées bureau (lat/lon site)
   │   └─ Mode normal: parse les coordonnées fournies
   │
   ├─ Validation GPS → GPSValidationService.validate_location()
   │   ├─ Calcul distance → calculate_distance() [Haversine]
   │   │   └─ d = 2 × R × arcsin(√(sin²(Δφ/2) + cos(φ1)×cos(φ2)×sin²(Δλ/2)))
   │   ├─ Vérif distance < allowed_radius_meters (200m)
   │   └─ Vérif accuracy < gps_accuracy_max_meters (100m)
   │
   ├─ Création pointage → AttendanceService.create_punch()
   │   └─ Transaction atomique: Attendance.objects.create()
   │
   └─ Redirection + message succès

4. Affichage confirmation → "Pointage arrivée enregistré à 08:15"
```

**Formule Haversine (calcul distance):**
```python
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance entre deux points GPS en mètres.
    
    Formule:
    a = sin²(Δφ/2) + cos(φ1) × cos(φ2) × sin²(Δλ/2)
    c = 2 × atan2(√a, √(1−a))
    d = R × c
    
    où:
    - φ = latitude (en radians)
    - λ = longitude (en radians)
    - R = 6371000 mètres (rayon de la Terre)
    """
    R = 6371000  # Rayon terrestre en mètres
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c  # Distance en mètres
```

**Sécurité GPS (multi-couches):**
```
Niveau 1: Vue CompanySettingsView (settings_views.py)
├─ get_form_fields(): 
│   ├─ Si superuser → retourne tous les champs (GPS + horaires)
│   └─ Si RH → retourne uniquement horaires (pas GPS)
└─ dispatch():
    ├─ Si superuser → autorise accès
    ├─ Si RH → autorise accès (lecture seule GPS)
    └─ Sinon → redirige dashboard

Niveau 2: Admin CompanySettingsAdmin (admin.py)
├─ get_readonly_fields():
│   ├─ Si superuser → readonly = ('updated_at',)
│   └─ Si non-superuser → readonly += ('site_center_latitude', ...)
└─ save_model():
    ├─ Si modification GPS ET non-superuser
    │   ├─ Revenir aux anciennes valeurs
    │   └─ Ajouter message d'erreur
    └─ Sinon → sauvegarder normalement
```

---

### 3. Module `leave` - Gestion des congés

**Responsabilité:** Demandes, workflow de validation, soldes

**Fichiers clés:**
```
leave/
├── models.py              # LeaveRequest, LeaveType, LeaveBalance
├── workflow_views.py      # Workflow de validation
│   ├── LeaveRequestCreateView         # Création demande
│   ├── LeaveApprovalListView          # Liste demandes à valider
│   └── LeaveApprovalUpdateView        # Traitement approbation/rejet
├── forms.py               # LeaveRequestForm, LeaveApprovalForm
└── signals.py             # Auto-création soldes
```

**Modèle de données:**
```python
# LeaveType (Types de congés)
- name: CharField (ex: "Congé annuel", "Maladie")
- code: CharField (unique)
- allocation_amount: IntegerField (jours/an)
- requires_rh_approval: BooleanField
- is_paid: BooleanField

# LeaveRequest (Demandes)
- employee: ForeignKey(User)
- leave_type: ForeignKey(LeaveType)
- start_date, end_date: DateField
- duration_days: IntegerField
- reason: TextField
- status: CharField (pending, approved_manager, approved_rh, rejected_*)
- manager: ForeignKey(User, null=True)
- manager_decision: CharField (null=True)
- manager_comment: TextField
- rh_decision: CharField (null=True)
- rh_comment: TextField

# LeaveBalance (Soldes)
- employee: ForeignKey(User)
- leave_type: ForeignKey(LeaveType)
- year: IntegerField
- allocated_balance: IntegerField
- taken_balance: IntegerField
- remaining_balance: IntegerField (calculé)
```

**Workflow de validation:**
```
                    ┌───────────────┐
                    │   Employé     │
                    │ crée demande  │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  status =     │
                    │  'pending'    │
                    └───────┬───────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
    ┌──────────────┐              ┌──────────────┐
    │   Manager    │              │  Employé =   │
    │  approuve    │              │  Manager     │
    └──────┬───────┘              └──────┬───────┘
           │                             │
           ▼                             ▼
    ┌──────────────┐              ┌──────────────┐
    │  status =    │              │  status =    │
    │'approved_mgr'│              │'approved_mgr'│
    └──────┬───────┘              └──────┬───────┘
           │                             │
           └──────────────┬──────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │    RH/DG     │
                  │  approuve    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  status =    │
                  │'approved_rh' │
                  │  Déduction   │
                  │    solde     │
                  └──────────────┘

À chaque étape, possibilité de REJET → status = 'rejected_*'
```

**Transaction atomique (création):**
```python
with transaction.atomic():
    # 1. Vérifier solde disponible
    balance = LeaveBalance.objects.get_or_create(...)
    if balance.remaining_balance < days_requested:
        raise ValidationError("Solde insuffisant")
    
    # 2. Vérifier chevauchements
    overlapping = LeaveRequest.objects.filter(...)
    if overlapping.exists():
        raise ValidationError("Chevauchement détecté")
    
    # 3. Créer la demande
    leave_request = LeaveRequest.objects.create(...)
    
    # 4. Déterminer workflow (selon rôle)
    if role == 'employee':
        leave_request.status = 'pending'
    elif role == 'manager':
        leave_request.status = 'approved_manager'
    elif role == 'rh_dg':
        leave_request.status = 'approved_rh'
    
    leave_request.save()
    
# 5. Envoyer notifications (HORS TRANSACTION)
NotificationService.send_leave_pending_notification(...)
```

---

## 🔐 Sécurité & Permissions

### Système de rôles

| Rôle | Peut pointer | Peut approuver congés | Peut configurer GPS | Django Admin |
|------|--------------|----------------------|---------------------|--------------|
| **admin** | ❌ Non | ❌ Non | ✅ Oui (full) | ✅ Full access |
| **rh_dg** | ❌ Non | ✅ Oui (final) | ⚠️ Lecture seule | ⚠️ Limité |
| **manager** | ✅ Oui | ✅ Oui (équipe) | ❌ Non | ❌ Non |
| **employee** | ✅ Oui | ❌ Non | ❌ Non | ❌ Non |

### Mixins de permission

```python
# common/mixins.py

class EmployeeRequiredMixin:
    """Requiert un profil employé actif."""
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'employee_profile'):
            return redirect('dashboard:dashboard')
        if not request.user.employee_profile.is_active:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)

class ManagerRequiredMixin(EmployeeRequiredMixin):
    """Requiert rôle Manager ou supérieur."""
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.user.employee_profile.role not in ['manager', 'rh_dg']:
            return redirect('dashboard:dashboard')
        return response

class RHRequiredMixin(EmployeeRequiredMixin):
    """Requiert rôle RH/DG."""
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.user.employee_profile.role != 'rh_dg':
            return redirect('dashboard:dashboard')
        return response
```

---

## 📊 Base de données

### Schéma relationnel

```sql
-- Utilisateurs et profils
auth_user (Django built-in)
├── id: INTEGER PRIMARY KEY
├── username: VARCHAR(150) UNIQUE
├── email: VARCHAR(254)
├── password: VARCHAR(128)
└── ...

accounts_employeeprofile
├── id: INTEGER PRIMARY KEY
├── user_id: INTEGER UNIQUE → auth_user.id
├── employee_id: VARCHAR(20) UNIQUE  -- EMPXXX
├── role: VARCHAR(20)  -- employee, manager, rh_dg
├── department_id: INTEGER → accounts_department.id
├── manager_id: INTEGER → auth_user.id
├── can_punch: BOOLEAN
└── is_active: BOOLEAN

-- Pointages
attendance_attendance
├── id: INTEGER PRIMARY KEY
├── employee_id: INTEGER → auth_user.id
├── date: DATE
├── time: TIME
├── punch_type: VARCHAR(3)  -- 'in', 'out'
├── latitude: DECIMAL(9,6)
├── longitude: DECIMAL(9,6)
├── gps_accuracy: DECIMAL(6,2)
├── distance_from_site: DECIMAL(8,2)
├── status: VARCHAR(20)
└── UNIQUE(employee_id, date, punch_type)

-- Congés
leave_leaverequest
├── id: INTEGER PRIMARY KEY
├── employee_id: INTEGER → auth_user.id
├── leave_type_id: INTEGER → leave_leavetype.id
├── start_date, end_date: DATE
├── duration_days: INTEGER
├── status: VARCHAR(20)
├── manager_id: INTEGER → auth_user.id
├── manager_decision: VARCHAR(20)
└── rh_decision: VARCHAR(20)

leave_leavebalance
├── id: INTEGER PRIMARY KEY
├── employee_id: INTEGER → auth_user.id
├── leave_type_id: INTEGER → leave_leavetype.id
├── year: INTEGER
├── allocated_balance: INTEGER
├── taken_balance: INTEGER
└── UNIQUE(employee_id, leave_type_id, year)

-- Configuration
attendance_companysettings (Singleton)
├── id: INTEGER PRIMARY KEY (toujours = 1)
├── site_center_latitude: DECIMAL(9,6)
├── site_center_longitude: DECIMAL(9,6)
├── allowed_radius_meters: INTEGER
├── gps_accuracy_max_meters: INTEGER
├── work_start_time: TIME
├── work_end_time: TIME
└── late_tolerance_minutes: INTEGER
```

### Indexation recommandée

```sql
-- Performance queries
CREATE INDEX idx_attendance_employee_date ON attendance_attendance(employee_id, date);
CREATE INDEX idx_attendance_date ON attendance_attendance(date);
CREATE INDEX idx_leave_employee_status ON leave_leaverequest(employee_id, status);
CREATE INDEX idx_leave_dates ON leave_leaverequest(start_date, end_date);
```

---

## 🧪 Tests

### Structure des tests

```
tests/
├── base.py                      # TestCase de base
├── factories.py                 # Factories pour données test
├── test_user_service.py         # Tests UserService (20 tests)
│   ├── TestEmployeeIDGeneration
│   ├── TestUsernameGeneration
│   ├── TestPasswordGeneration
│   └── TestEmployeeCreation
├── test_permissions.py          # Tests Mixins (20 tests)
│   ├── TestEmployeeRequiredMixin
│   ├── TestManagerRequiredMixin
│   └── TestRHRequiredMixin
└── test_gps_validation.py       # Tests GPS (15 tests)
    ├── TestHaversineCalculation
    ├── TestGPSValidation
    └── TestEdgeCases

Total: ~55 tests unitaires
```

**Commandes:**
```bash
# Tous les tests
python manage.py test

# Module spécifique
python manage.py test tests.test_gps_validation

# Test spécifique
python manage.py test tests.test_gps_validation.TestHaversineCalculation.test_paris_london_distance

# Avec couverture
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

---

## 📈 Performance

### Optimisations implémentées

1. **select_related / prefetch_related:**
```python
# Évite N+1 queries
leave_requests = LeaveRequest.objects.select_related(
    'employee', 'leave_type', 'employee__employee_profile'
).filter(status='pending')
```

2. **Database indexes:**
```python
class Attendance(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date']),
        ]
```

3. **Caching CompanySettings (Singleton):**
```python
@classmethod
def load(cls):
    """Charge (ou crée) la configuration unique."""
    settings, created = cls.objects.get_or_create(pk=1)
    return settings
```

4. **Lazy loading services:**
```python
# attendance/lazy_imports.py
# Import services uniquement quand nécessaire
```

---

## 🔄 Intégration Continue (Recommandé)

### Exemple GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run migrations
        run: python manage.py migrate
      - name: Run tests
        run: python manage.py test
```

---

## 📚 Références

### Technologies utilisées

- **Django 5.1.3:** https://docs.djangoproject.com/
- **Bootstrap 5.3.2:** https://getbootstrap.com/docs/5.3/
- **Geolocation API:** https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API
- **Haversine Formula:** https://en.wikipedia.org/wiki/Haversine_formula

### Documents complémentaires

- `GUIDE_INSTALLATION.md` - Installation pas à pas
- `ANALYSE_BONNES_PRATIQUES.md` - Analyse code qualité (score 7.1/10)
- `GUIDE_RESOLUTION_GPS.md` - Dépannage GPS
- `RESUME_COMPLET_PROJET.md` - Vue d'ensemble fonctionnalités

---

© 2024 - Système de Gestion de Présence
Projet de fin de cycle - Architecture Django modulaire
