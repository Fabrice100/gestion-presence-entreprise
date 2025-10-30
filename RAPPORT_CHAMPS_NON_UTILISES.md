# 📊 RAPPORT : CHAMPS ET DONNÉES NON UTILISÉS

## 🔍 ANALYSE DE LA BASE DE DONNÉES

### ✅ Champs UTILISÉS (à conserver)

#### Attendance (Pointage)

| Champ | Utilisation | Commentaire |
|-------|------------|-------------|
| `employee` | ✅ Partout | Clé primaire relationnelle |
| `date` | ✅ Partout | Utilisé pour filtrage et calculs |
| `time` | ✅ Partout | Utilisé pour calculs d'heures |
| `punch_type` | ✅ Partout | 'in' ou 'out' - essentiel |
| `latitude` | ✅ Utilisé | Requis pour géolocalisation |
| `longitude` | ✅ Utilisé | Requis pour géolocalisation |
| `accuracy` | ✅ Utilisé | Validation GPS |
| `worked_hours` | ✅ Utilisé | Calcul des heures travaillées |
| `status` | ✅ Utilisé | 'normal', 'late', 'early' assignés |
| `created_at` | ✅ Utilisé | Traçabilité |
| `updated_at` | ✅ Utilisé | Traçabilité |
| `notes` | ✅ Utilisé | Affiché dans dashboard (templates) |
| `distance_from_site` | ✅ Utilisé | Calculé automatiquement, affiché admin |
| `get_duration_with_previous()` | ✅ Utilisé | Utilisé dans `dashboard_views.py` |

---

### ⚠️ Champs PARTIELLEMENT UTILISÉS

#### Attendance (Pointage)

| Champ | Assigné ? | Affiché ? | Utilisé métier ? | Recommandation |
|-------|-----------|-----------|------------------|----------------|
| `user_agent` | ✅ Oui (`attendance_service.py:364`) | ✅ Admin Django | ❌ Non (pas de logique métier) | **Peut être supprimé** si pas nécessaire pour audit |
| `ip_address` | ✅ Oui (`attendance_service.py:363`) | ✅ Admin Django | ❌ Non (pas de logique métier) | **Peut être supprimé** si pas nécessaire pour audit |
| `source` | ⚠️ Toujours 'web' | ✅ Admin (filtre) | ❌ Non (jamais varié) | **Peut être supprimé** - système web uniquement |

**Détails :**
- `user_agent` et `ip_address` : Enregistrés lors de la création du pointage mais **jamais utilisés dans la logique métier**
- `source` : Toujours assigné à `'web'` par défaut, jamais changé (pas de mobile/kiosk/admin réellement)
- Ces champs peuvent être utiles pour **audit/forensics** mais pas pour le fonctionnement de l'application

---

### ❌ Champs/Méthodes NON UTILISÉS (à supprimer)

#### Attendance (Pointage)

| Champ/Méthode | Défini ? | Utilisé ? | Action |
|---------------|----------|-----------|-------|
| `is_within_zone()` | ✅ Oui | ❌ **Jamais appelé** | **Supprimer** |
| `is_accurate()` | ✅ Oui | ❌ **Jamais appelé** | **Supprimer** |

**Statuts dans `STATUS_CHOICES` jamais assignés :**
| Statut | Défini ? | Assigné ? | Action |
|--------|----------|-----------|--------|
| `'missing_out'` | ✅ | ❌ Jamais | **Retirer des choix** |
| `'double_punch'` | ✅ | ❌ Jamais | **Retirer des choix** |
| `'outside_zone'` | ✅ | ❌ Jamais | **Retirer des choix** |
| `'low_accuracy'` | ✅ | ❌ Jamais | **Retirer des choix** |

**Source jamais utilisée :**
| Source | Défini ? | Utilisé ? | Action |
|-------|----------|-----------|--------|
| `'mobile'` | ✅ | ❌ Jamais | **Retirer** si pas de version mobile |
| `'kiosk'` | ✅ | ❌ Jamais | **Retirer** si pas de kiosque |
| `'admin'` | ✅ | ❌ Jamais | **Retirer** si pas de création admin manuelle |

---

#### AttendanceAnomaly (Anomalies)

| Type d'anomalie | Dans choix ? | Créée ? | Action |
|-----------------|--------------|---------|--------|
| `'late_arrival'` | ✅ | ❌ **Jamais créée** | **Conserver** (décision de conception) |
| `'early_departure'` | ✅ | ❌ **Jamais créée** | **Conserver** (décision de conception) |

**Note :** Ces types sont conservés car c'est une décision de conception (détection sans création d'anomalie).

---

#### LeaveRequest (Demande de congé)

| Champ | Assigné ? | Affiché ? | Utilisé métier ? | Recommandation |
|-------|-----------|-----------|------------------|----------------|
| `priority` | ⚠️ **Jamais assigné** | ✅ Admin + 1 template | ❌ Non (pas de logique métier) | **Peut être supprimé** |
| `medical_certificate` | ❌ **Jamais** | ❌ Non | ❌ Non | **Supprimer** si pas utilisé |

**Détails :**
- `priority` : Défaut `'normal'`, mais **jamais changé** lors de la création de demande
- Utilisé dans `leave_approval_list_modern.html` pour affichage mais valeur toujours identique
- `medical_certificate` : Champ FileField jamais utilisé, pas d'upload de fichier dans les formulaires

---

### 📊 RÉSUMÉ PAR MODÈLE

#### 1. Attendance (Pointage)

**Champs à SUPPRIMER :**
- ❌ Méthode `is_within_zone()` (jamais appelée)
- ❌ Méthode `is_accurate()` (jamais appelée)

**Champs à CONSIDÉRER pour suppression :**
- ⚠️ `user_agent` (utile pour audit, pas pour logique métier)
- ⚠️ `ip_address` (utile pour audit, pas pour logique métier)
- ⚠️ `source` (toujours 'web', pas de variante)

**Choix à NETTOYER dans STATUS_CHOICES :**
- ❌ `'missing_out'` (jamais assigné)
- ❌ `'double_punch'` (jamais assigné)
- ❌ `'outside_zone'` (jamais assigné)
- ❌ `'low_accuracy'` (jamais assigné)

**Choix à NETTOYER dans SOURCE_CHOICES :**
- ❌ `'mobile'` (si pas de version mobile)
- ❌ `'kiosk'` (si pas de kiosque)
- ❌ `'admin'` (si pas de création manuelle admin)

---

#### 2. AttendanceAnomaly (Anomalies)

**Tout est utilisé** ✅ (les choix `late_arrival` et `early_departure` sont conservés par décision)

---

#### 3. LeaveRequest (Demande de congé)

**Champs à SUPPRIMER :**
- ❌ `priority` (défaut 'normal', jamais changé, pas de logique métier)
- ❌ `medical_certificate` (FileField jamais utilisé)

---

## 🎯 RECOMMANDATIONS

### Nettoyage prioritaire (impact faible)

1. **Supprimer méthodes inutilisées dans `Attendance` :**
   - `is_within_zone()`
   - `is_accurate()`

2. **Nettoyer `STATUS_CHOICES` dans `Attendance` :**
   - Retirer `'missing_out'`, `'double_punch'`, `'outside_zone'`, `'low_accuracy'`
   - Garder seulement : `'normal'`, `'late'`, `'early'`

3. **Nettoyer `SOURCE_CHOICES` dans `Attendance` :**
   - Si système web uniquement : garder seulement `'web'`
   - Sinon : retirer les choix non utilisés

### Nettoyage optionnel (impact moyen)

4. **Supprimer `priority` dans `LeaveRequest` :**
   - Champ jamais modifié, toujours 'normal'
   - Pas de logique métier basée dessus
   - Impact : Modification template `leave_approval_list_modern.html`

5. **Supprimer `medical_certificate` dans `LeaveRequest` :**
   - FileField jamais utilisé
   - Pas de formulaire d'upload

### Audit/Sécurité (à CONSERVER si nécessaire)

6. **Conserver `user_agent` et `ip_address` :**
   - Utiles pour audit/forensics
   - Traçabilité des actions
   - Peuvent aider en cas d'incident de sécurité
   - **Recommandation : CONSERVER** pour audit

---

## 📝 FICHIERS À MODIFIER (si nettoyage)

### Suppression méthodes inutilisées

```python
# attendance_system/attendance/models.py
# Supprimer :
- def is_within_zone(self):
- def is_accurate(self):
```

### Nettoyage STATUS_CHOICES

```python
# attendance_system/attendance/models.py
STATUS_CHOICES = [
    ('normal', 'Normal'),
    ('late', 'En retard'),
    ('early', 'Sortie anticipée'),
    # SUPPRIMER :
    # ('missing_out', 'Sortie oubliée'),
    # ('double_punch', 'Double pointage'),
    # ('outside_zone', 'Hors zone'),
    # ('low_accuracy', 'Précision faible'),
]
```

### Suppression priority dans LeaveRequest

```python
# attendance_system/leave/models.py
# Supprimer :
- PRIORITY_CHOICES
- priority = models.CharField(...)
```

### Suppression medical_certificate

```python
# attendance_system/leave/models.py
# Supprimer :
- medical_certificate = models.FileField(...)
```

---

## ✅ CONCLUSION

### Impact du nettoyage

**Niveau 1 (Sûr, sans risque) :**
- ✅ Supprimer `is_within_zone()` et `is_accurate()`
- ✅ Nettoyer `STATUS_CHOICES` (retirer choix non utilisés)
- ✅ Nettoyer `SOURCE_CHOICES` (retirer choix non utilisés)

**Niveau 2 (Impact templates) :**
- ⚠️ Supprimer `priority` dans `LeaveRequest` (modifier template)
- ⚠️ Supprimer `medical_certificate` (pas d'impact visible)

**Niveau 3 (Utilité audit) :**
- ⚠️ `user_agent` et `ip_address` : **CONSERVER** pour audit/forensics

### Résultat

- **Code plus propre** : Moins de méthodes/champs inutilisés
- **Base de données allégée** : Moins de colonnes vides/redondantes
- **Choix nettoyés** : Seulement les valeurs réellement utilisées
- **Maintenance facilitée** : Code plus simple à comprendre

---

**Date :** 2025-01-27  
**Version :** 1.0  
**Statut :** Analyse complète

