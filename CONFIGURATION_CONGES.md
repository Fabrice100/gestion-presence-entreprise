# Configuration des Congés - Système de Gestion des Présences

## 📋 Vue d'ensemble

Le système utilise un **SOLDE UNIQUE de 30 JOURS** pour tous les congés payés. Tous les types de congés payés (vacances, maladie, événements familiaux) déduisent du même solde annuel de 30 jours.

## ✅ Configuration Actuelle - SOLDE UNIQUE

### 🎯 Principe : 30 JOURS TOTAL pour l'année

Chaque employé dispose de **30 jours de congés payés par an**, utilisables pour :

### 1. Congés Payés (Annual Leave / Vacances)
- **Déduit du solde** : ✓ OUI
- **Solde annuel** : Déduit des 30 jours
- **Payé** : Oui
- **Usage** : Vacances, congés annuels standards

### 2. Congé Maladie (Sick Leave)
- **Déduit du solde** : ✓ OUI
- **Solde annuel** : Déduit des 30 jours
- **Payé** : Oui
- **Usage** : Maladie, raisons médicales

### 3. Événements Familiaux (Family Events)
- **Déduit du solde** : ✓ OUI
- **Solde annuel** : Déduit des 30 jours
- **Payé** : Oui
- **Usage** : Mariage, naissance, décès familial, etc.

### 4. Congé sans Solde (Unpaid Leave)
- **Déduit du solde** : ✗ NON
- **Solde annuel** : N/A (ne touche pas aux 30 jours)
- **Payé** : Non
- **Usage** : Congés personnels non rémunérés

## 📊 Exemple d'Utilisation

```
Employé A - Début d'année : 30 jours disponibles

✓ Prend 10 jours de vacances (Congés payés)
  → Solde restant : 20 jours

✓ Prend 3 jours de maladie (Congé maladie)
  → Solde restant : 17 jours

✓ Prend 2 jours pour un mariage (Événements familiaux)
  → Solde restant : 15 jours

TOTAL utilisé : 15 jours sur les 30 jours annuels
SOLDE restant : 15 jours
```

## 🔧 Configuration Technique

### Base de Données - Modèle LeaveType

```python
class LeaveType(models.Model):
    name = models.CharField(max_length=100)
    deducts_balance = models.BooleanField(
        default=True,
        verbose_name="Déduit du solde",
        help_text="Ce type de congé déduit-il du solde annuel de 30 jours?"
    )
    is_paid = models.BooleanField(default=True)
    allocation_amount = models.DecimalField(max_digits=5, decimal_places=2)
```

### Configuration par Type - SOLDE UNIQUE

| Type de Congé | deducts_balance | Déduit des 30j | Payé |
|---------------|-----------------|----------------|------|
| Congés payés | `True` | ✓ OUI | ✓ Oui |
| Congé maladie | `True` | ✓ OUI | ✓ Oui |
| Événements familiaux | `True` | ✓ OUI | ✓ Oui |
| Congé sans solde | `False` | ✗ NON | ✗ Non |

**Important** : Tous les congés PAYÉS déduisent du même solde de 30 jours.

## 🎯 Logique d'Application

### 1. Création de Demande de Congé (workflow_views.py)

```python
# Ligne 122-140 : Validation du solde
if leave_type.deducts_balance:
    # Vérifier le solde disponible pour tous les congés payés
    balance, created = LeaveBalance.objects.get_or_create(...)
    
    if balance.remaining_balance < days_requested:
        # Erreur : solde insuffisant (sur les 30 jours)
        form.add_error(None, 'Solde insuffisant')
else:
    # Congé sans solde uniquement : PAS de vérification
    pass
```

### 2. Déduction du Solde (workflow_views.py)

```python
# Ligne 360-362 : Déduction conditionnelle
def _deduct_leave_balance(self, leave_request):
    if not leave_request.leave_type.deducts_balance:
        # Congé sans solde : NE PAS déduire
        return
    
    # Tous les congés payés : déduire des 30 jours
    working_days = holiday_service.get_working_days_in_period(...)
    balance.taken_balance += working_days
    balance.save()
```

## 📊 Flux de Validation

```
Employé soumet demande de congé
         ↓
   Type de congé ?
         ↓
    ┌────┴────────┐
    ↓             ↓
Congé Payé   Congé sans solde
    ↓             ↓
Vérifier      Pas de
solde (30j)   vérification
    ↓             ↓
Solde OK? ──→ Approuver
    ↓
Insuffisant
    ↓
  Rejeter
```

**Note** : Congé Payé = Vacances + Maladie + Événements familiaux (tous déduisent des 30 jours)

## 🔍 Vérification de la Configuration

Pour vérifier la configuration actuelle, exécutez :

```python
from leave.models import LeaveType

for lt in LeaveType.objects.all():
    print(f"{lt.name}: deducts_balance={lt.deducts_balance}")
```

**Résultat attendu :**
```
Congés payés: deducts_balance=True (déduit des 30j)
Congé maladie: deducts_balance=True (déduit des 30j)
Événements familiaux: deducts_balance=True (déduit des 30j)
Congé sans solde: deducts_balance=False (ne déduit pas)
```

## 🛠️ Modification de la Configuration

Pour ajouter un nouveau type de congé :

```python
# Dans le shell Django
from leave.models import LeaveType

# Exemple : Congé de formation (déduit des 30 jours)
LeaveType.objects.create(
    name="Congé de formation",
    deducts_balance=True,  # Déduit du solde de 30j
    is_paid=True,
    allocation_amount=5
)
```

## ⚠️ Points d'Attention

1. **SOLDE UNIQUE de 30 jours** pour tous les congés payés
2. **Tous les types payés** (vacances, maladie, événements) déduisent du même compteur
3. **Seul le "Congé sans solde"** ne déduit pas (car non rémunéré)
4. **Les jours fériés sont automatiquement exclus** du calcul de déduction
5. **Le champ `deducts_balance`** est critique pour la logique métier

## 📝 Historique des Modifications

- **2025-10-27 (v2)** : Passage au système de SOLDE UNIQUE
  - TOUS les congés payés déduisent maintenant du même solde de 30 jours
  - Congé maladie : `deducts_balance=False` → `True`
  - Événements familiaux : `deducts_balance=False` → `True`
  - Seul le "Congé sans solde" reste à `False`

- **2025-10-27 (v1)** : Correction de la validation dans `LeaveRequestCreateView.form_valid()`
  - Ajout de la vérification `if leave_type.deducts_balance:` avant validation du solde

## ✅ Tests de Vérification

### Test 1 : Congé Payé avec Solde Insuffisant
```python
# Solde : 5 jours restants
# Demande : 10 jours de congés payés
# Résultat attendu : REJET avec message "Solde insuffisant"
```

### Test 2 : Congé Maladie déduit du solde (NOUVELLE LOGIQUE)
```python
# Solde : 5 jours restants
# Demande : 10 jours de congé maladie
# Résultat attendu : REJET avec message "Solde insuffisant"
# (Avant : validation OK, Maintenant : vérifie le solde)
```

### Test 3 : Événements Familiaux déduit du solde (NOUVELLE LOGIQUE)
```python
# Solde : 2 jours restants
# Demande : 5 jours pour événement familial
# Résultat attendu : REJET avec message "Solde insuffisant"
# (Tous les congés payés partagent le même solde de 30j)
```

### Test 4 : Congé sans solde
```python
# Solde : 0 jours restants
# Demande : 10 jours de congé sans solde
# Résultat attendu : VALIDATION OK (ne vérifie pas le solde, non payé)
```

## 🔗 Fichiers Concernés

- `leave/models.py` : Définition du modèle `LeaveType` avec `deducts_balance`
- `leave/workflow_views.py` : Logique de validation et déduction
  - Ligne 122-140 : Validation conditionnelle
  - Ligne 360-362 : Déduction conditionnelle
- `leave/forms.py` : Formulaire de demande de congé

---

**Date de dernière mise à jour** : 27 octobre 2025  
**Version** : 1.0  
**Auteur** : Système de Gestion des Présences
