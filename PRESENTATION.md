# 🎓 Présentation - Système de Gestion de Présence

## Projet de fin de cycle

**Auteur:** HUSUNUKPE Fabrice  
**Date:** Décembre 2024  
**Technologies:** Django 5.1.3, Bootstrap 5, SQLite/PostgreSQL  

---

## 📋 Vue d'ensemble

### Problématique

Les entreprises ont besoin d'un système fiable pour :
- ✅ Suivre les présences des employés
- ✅ Gérer les demandes de congés
- ✅ Valider la localisation des pointages (anti-fraude)
- ✅ Générer des rapports RH

### Solution développée

Application web Django complète avec :
- 🌍 **Pointage GPS** (validation géolocalisation)
- 📅 **Gestion congés** (workflow de validation)
- 👥 **4 rôles** (Admin, RH/DG, Manager, Employé)
- 📊 **Rapports** (présences, absences, retards)
- 🔒 **Sécurité** (authentification, permissions, transactions)

---

## 🏗️ Architecture technique

### Stack technologique

```
┌─────────────────────────────────────┐
│         FRONTEND                    │
│  • Bootstrap 5.3.2                  │
│  • HTML5 Geolocation API            │
│  • JavaScript (Vanilla)             │
└──────────────┬──────────────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────────────┐
│         BACKEND                     │
│  • Django 5.1.3 (Python 3.11+)      │
│  • Services métier (SOLID)          │
│  • Forms validation                 │
│  • ORM (migrations)                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         DATABASE                    │
│  • SQLite (dev)                     │
│  • PostgreSQL (production)          │
└─────────────────────────────────────┘
```

### Modules principaux

| Module | Responsabilité | Fichiers clés |
|--------|----------------|---------------|
| **accounts/** | Authentification, profils | `user_services.py`, `middleware.py` |
| **attendance/** | Pointages GPS | `attendance_service.py`, `forms.py` |
| **leave/** | Congés, workflow | `workflow_views.py`, `models.py` |
| **reports/** | Rapports, exports | `export_services.py` |

---

## 🎯 Fonctionnalités clés

### 1. Pointage GPS avec validation

**Caractéristiques:**
- Géolocalisation HTML5 (navigateur)
- Validation distance bureau (Formule Haversine)
- Validation précision GPS (< 100m)
- Mode démo pour tests
- Anti-fraude (IP, User Agent)

**Formule Haversine:**
```
Distance = 2 × R × arcsin(√(sin²(Δφ/2) + cos(φ1)×cos(φ2)×sin²(Δλ/2)))

où:
- R = 6371000 mètres (rayon Terre)
- φ = latitude (radians)
- λ = longitude (radians)
```

**Exemple:**
```
Bureau: 6.3654°N, 2.4183°E (Cotonou)
Employé: 6.3670°N, 2.4200°E
Distance calculée: 185 mètres ✅ (< 200m autorisés)
Pointage accepté!
```

**Sécurité GPS (2 niveaux):**
1. **Vue web:** RH ne voit pas les champs GPS
2. **Admin Django:** Champs GPS en lecture seule pour non-superusers

---

### 2. Gestion des congés avec workflow

**Workflow de validation:**

```
Employé soumet demande
        ↓
Manager approuve/rejette
        ↓
RH/DG approuve/rejette (décision finale)
        ↓
Déduction automatique du solde
```

**Validations:**
- ✅ Solde suffisant
- ✅ Pas de chevauchement avec demandes existantes
- ✅ Dates cohérentes (début < fin)
- ✅ Notifications email à chaque étape

**Exemple:**
```
Employé: emp1 demande 5 jours (01/02 - 05/02)
Solde: 15 jours disponibles ✅
Manager: Approuve → status = 'approved_manager'
RH: Approuve → status = 'approved_rh'
Nouveau solde: 10 jours (15 - 5)
```

---

### 3. Système de rôles et permissions

| Rôle | Employee ID | Peut pointer | Approuver congés | Config GPS |
|------|-------------|--------------|------------------|------------|
| **Admin** | Aucun | ❌ Non | ❌ Non | ✅ Oui (full) |
| **RH/DG** | EMP### | ❌ Non | ✅ Oui (final) | ⚠️ Lecture seule |
| **Manager** | EMP### | ✅ Oui | ✅ Oui (équipe) | ❌ Non |
| **Employee** | EMP### | ✅ Oui | ❌ Non | ❌ Non |

**Génération automatique:**
- **Employee ID:** EMPXXX (numéro aléatoire 100-999)
- **Username:** Généré depuis email (ex: `fabrice.h@example.com` → `fabrice.h`)
- **Password:** 8 caractères sécurisés (majuscule, minuscule, chiffre, spécial)

**Exemple:**
```python
# Création employé
user_data = {
    'first_name': 'Fabrice',
    'last_name': 'HUSUNUKPE',
    'email': 'fabrice.h@example.com'
}

profile_data = {
    'role': 'employee',
    'department': dept_it,
    'manager': user_manager
}

# Service génère automatiquement
user, employee_id, password = UserService.create_employee_with_credentials(
    user_data, profile_data
)

# Résultat:
# employee_id = 'EMP472' (aléatoire)
# username = 'fabrice.h'
# password = 'Kz9@mT2p' (sécurisé)
```

---

## 🔧 Améliorations techniques (Option 5)

### Refactoring selon principes SOLID

**Score initial:** 7.1/10  
**Score final:** 9.0/10 (+26%)  

#### 1. Single Responsibility Principle ✅

**Avant (200 lignes):**
```python
def post(self, request):
    # Parsing GPS (30 lignes)
    # Calcul Haversine (20 lignes)
    # Validations (80 lignes)
    # Vérifications métier (50 lignes)
    # Création pointage (20 lignes)
```

**Après (80 lignes):**
```python
def post(self, request):
    form = PunchForm(request.POST)  # Validation
    can_punch = AttendanceBusinessRules.can_user_punch(...)  # Permissions
    gps_parsed = GPSValidationService.parse_gps_data(...)  # Parsing
    validation = GPSValidationService.validate_location(...)  # Validation GPS
    attendance = AttendanceService.create_punch(...)  # Création
```

**Réduction:** -60% de code  
**Services créés:** 6 services métier  

#### 2. Validation centralisée (Forms) ✅

```python
class PunchForm(forms.Form):
    latitude = forms.DecimalField(min_value=-90, max_value=90)
    longitude = forms.DecimalField(min_value=-180, max_value=180)
    accuracy = forms.DecimalField(max_value=10000)
    
    def clean_accuracy(self):
        """Validation contre CompanySettings."""
        accuracy = self.cleaned_data['accuracy']
        settings = CompanySettings.load()
        if accuracy > settings.gps_accuracy_max_meters:
            raise ValidationError(f'Précision trop faible: {accuracy}m')
        return accuracy
```

#### 3. Transactions atomiques ✅

```python
from django.db import transaction

@staticmethod
def create_punch(user, punch_type, gps_data, request_meta=None):
    try:
        with transaction.atomic():
            attendance = Attendance.objects.create(
                employee=user,
                date=timezone.now().date(),
                punch_type=punch_type,
                latitude=gps_data['latitude'],
                # ...
            )
            return attendance, None
    except Exception as e:
        # Rollback automatique
        return None, str(e)
```

**Garantie:** Cohérence des données (tout ou rien)

#### 4. Tests unitaires ✅

```
tests/
├── test_user_service.py         (20 tests)
│   ├── TestEmployeeIDGeneration
│   ├── TestUsernameGeneration
│   ├── TestPasswordGeneration
│   └── TestEmployeeCreation
├── test_permissions.py          (20 tests)
│   ├── TestEmployeeRequiredMixin
│   ├── TestManagerRequiredMixin
│   └── TestRHRequiredMixin
└── test_gps_validation.py       (9 tests)
    ├── TestHaversineCalculation
    ├── TestGPSValidation
    └── TestEdgeCases

Total: 49 tests
```

**Commande:** `python manage.py test`

---

## 📊 Métriques du projet

### Code

| Métrique | Valeur |
|----------|--------|
| **Lignes de code Python** | ~8,000 lignes |
| **Templates HTML** | 45 fichiers |
| **Services métier** | 6 services |
| **Tests unitaires** | 49 tests |
| **Documentation** | 2,500+ lignes (3 guides) |

### Base de données

| Table | Enregistrements (démo) |
|-------|------------------------|
| `auth_user` | 14 utilisateurs |
| `accounts_employeeprofile` | 13 profils |
| `attendance_attendance` | ~200 pointages |
| `leave_leaverequest` | ~30 demandes |
| `leave_leavebalance` | ~40 soldes |

### Performance

| Opération | Temps moyen |
|-----------|-------------|
| **Pointage GPS** | < 500ms |
| **Création congé** | < 200ms |
| **Rapport mensuel** | < 2s (100 employés) |
| **Chargement dashboard** | < 300ms |

---

## 🔒 Sécurité

### Mesures implémentées

1. **Authentification Django** (sessions sécurisées)
2. **CSRF Protection** (tous les formulaires)
3. **Permissions par rôle** (mixins de vérification)
4. **Changement mot de passe forcé** (première connexion)
5. **Validation GPS multi-niveaux** (vue + admin)
6. **Transactions atomiques** (cohérence données)
7. **IDs aléatoires** (anti-prédiction)

### Checklist production

- [x] `DEBUG=False`
- [x] `SECRET_KEY` complexe (50+ chars)
- [x] `ALLOWED_HOSTS` configuré
- [x] HTTPS activé (Let's Encrypt)
- [x] PostgreSQL (pas SQLite)
- [x] Backup automatique BDD
- [x] Logs rotatifs
- [x] Firewall (UFW)

---

## 📚 Documentation livrée

### Guides techniques (2,500+ lignes)

1. **GUIDE_INSTALLATION.md** (500 lignes)
   - Prérequis (Python, Git)
   - Installation 7 étapes
   - Configuration GPS
   - Tests manuels
   - Déploiement production
   - Dépannage

2. **ARCHITECTURE.md** (800 lignes)
   - Architecture globale (diagrammes)
   - 3 modules détaillés
   - Schéma BDD relationnel
   - Workflow congés
   - Flux pointage GPS (10 étapes)
   - Formule Haversine expliquée
   - Sécurité multi-couches

3. **RAPPORT_AMELIORATIONS.md** (1,200 lignes)
   - 7 tâches accomplies
   - Métriques avant/après
   - Principes SOLID appliqués
   - Recommandations futures
   - Checklist déploiement

### Autres documents

- `ANALYSE_BONNES_PRATIQUES.md` (analyse code qualité)
- `GUIDE_RESOLUTION_GPS.md` (dépannage GPS)
- `RESUME_COMPLET_PROJET.md` (vue d'ensemble)
- `CAS_UTILISATION.md` (user stories)

---

## 🚀 Démonstration

### Scénario 1: Pointage d'un employé

```
1. Connexion: username='emp1', password='password123'
2. Redirection: Changement mot de passe obligatoire
3. Nouveau password: 'MonPass@2024'
4. Dashboard: Affichage résumé (pointages, congés)
5. Menu: "Pointer"
6. Activation: Mode Démo (pour tests)
7. Clic: "Pointer l'arrivée"
8. Validation: GPS (coordonnées bureau)
   - Distance: 0m (mode démo)
   - Précision: 5m
9. Création: Pointage enregistré
10. Message: "✅ Pointage arrivée enregistré à 08:15"
```

### Scénario 2: Demande de congé

```
1. Connexion: emp1
2. Menu: "Mes congés" → "Nouvelle demande"
3. Formulaire:
   - Type: Congé annuel
   - Dates: 01/02/2025 - 05/02/2025 (5 jours)
   - Raison: "Vacances familiales"
4. Soumission: Vérification solde (15 jours disponibles ✅)
5. Création: status = 'pending'
6. Email: Notification envoyée au manager

---

7. Connexion: manager.it (manager de emp1)
8. Menu: "Demandes à approuver"
9. Liste: Demande de emp1 visible
10. Clic: "Approuver"
11. Commentaire: "Bon voyage !"
12. Validation: status = 'approved_manager'
13. Email: Notification RH

---

14. Connexion: rh.dg
15. Menu: "Validation finale"
16. Clic: "Approuver définitivement"
17. Transaction atomique:
    - status = 'approved_rh'
    - Solde: 15 → 10 jours
18. Email: Confirmation emp1
```

### Scénario 3: Tentative fraude GPS

```
1. Connexion: emp1
2. Menu: "Pointer"
3. GPS: Position réelle (5km du bureau)
4. Clic: "Pointer l'arrivée"
5. Validation GPS:
   - Calcul Haversine: distance = 5000m
   - Rayon autorisé: 200m
   - Résultat: distance > rayon ❌
6. Erreur: "🚫 Vous êtes trop loin du bureau (5000m)"
7. Pointage: REFUSÉ
8. Log: IP, coordonnées, timestamp enregistrés
```

---

## 🎓 Compétences démontrées

### Développement backend

- ✅ Django (MTV pattern, ORM, migrations)
- ✅ Python 3.11 (POO, services, decorators)
- ✅ SQL (requêtes optimisées, transactions)
- ✅ Architecture logicielle (SOLID, DRY, KISS)

### Développement frontend

- ✅ HTML5 (semantic markup, Geolocation API)
- ✅ CSS3 (Bootstrap 5, responsive design)
- ✅ JavaScript (async/await, fetch API)

### DevOps & Qualité

- ✅ Git (branches, commits, merges)
- ✅ Tests unitaires (Django TestCase, factories)
- ✅ Documentation (Markdown, diagrammes ASCII)
- ✅ Déploiement (Gunicorn, Nginx, PostgreSQL)

### Sécurité

- ✅ Authentification (Django Auth, sessions)
- ✅ Autorisations (permissions par rôle)
- ✅ Validation (Forms, business rules)
- ✅ HTTPS, CSRF, transactions atomiques

---

## 🏆 Points forts du projet

### Technique

1. **Architecture SOLID** (score 9/10)
2. **Services réutilisables** (web + API)
3. **Tests automatisés** (49 tests)
4. **Documentation complète** (2,500+ lignes)
5. **Sécurité multi-niveaux** (GPS, permissions, transactions)

### Fonctionnel

1. **GPS anti-fraude** (Haversine, précision)
2. **Workflow congés** (3 niveaux validation)
3. **Génération automatique** (IDs, passwords)
4. **Rapports RH** (présences, absences, retards)
5. **Interface moderne** (Bootstrap 5, responsive)

### Gestion de projet

1. **Méthodologie Agile** (sprints, user stories)
2. **Versioning Git** (commits clairs)
3. **Documentation** (installation, architecture)
4. **Tests** (validation fonctionnalités)
5. **Déploiement** (production-ready)

---

## 📞 Contact

**Auteur:** HUSUNUKPE Fabrice  
**Email:** fabrice.husunukpe@example.com  
**GitHub:** https://github.com/fabrice-husunukpe  
**LinkedIn:** linkedin.com/in/fabrice-husunukpe  

**Projet:** Système de Gestion de Présence  
**Institution:** [Votre université/école]  
**Année:** 2024  

---

## 📄 Licence

Projet académique - Projet de fin de cycle  
© 2024 HUSUNUKPE Fabrice

---

# 🎉 Merci pour votre attention !

**Questions ?**
