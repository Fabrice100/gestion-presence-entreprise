# Résumé des Modifications dans les Templates

## 📋 Vue d'Ensemble

**Objectif** : Adapter les templates pour que les demandes de **Manager** avec `status='pending'` soient affichées correctement, en plus des demandes d'**Employé** validées avec `status='approved_manager'`.

---

## 📁 Fichiers à Modifier (5 templates)

### 1. `templates/leave/rh_leave_management_ultra_modern.html`

**Ligne 37** : Filtre de sélection (dropdown)
```html
<!-- AVANT : -->
<option value="approved_manager" {% if request.GET.status == 'approved_manager' %}selected{% endif %}>Validé Manager (en attente RH)</option>

<!-- APRÈS : -->
<option value="pending_manager" {% if request.GET.status == 'pending_manager' %}selected{% endif %}>Managers (en attente RH)</option>
<option value="approved_manager" {% if request.GET.status == 'approved_manager' %}selected{% endif %}>Validé Manager (en attente RH)</option>
```
**Impact** : Le RH peut maintenant filtrer séparément les demandes de managers et celles validées par manager.

---

**Ligne 119** : Affichage du badge de statut
```html
<!-- AVANT : -->
{% if request.status == 'approved_manager' %}
    {% include 'components/status_badge.html' with status='pending' icon='bi-clock' text='À valider' %}
{% endif %}

<!-- APRÈS : -->
{% if request.status == 'pending' and request.employee.employee_profile.role == 'manager' %}
    {% include 'components/status_badge.html' with status='pending' icon='bi-clock' text='À valider' %}
{% elif request.status == 'approved_manager' %}
    {% include 'components/status_badge.html' with status='pending' icon='bi-clock' text='À valider' %}
{% endif %}
```
**Impact** : Affiche "À valider" pour les managers avec `status='pending'` ET pour les employés avec `status='approved_manager'`.

---

**Ligne 139** : Bouton d'action (Approuver/Rejeter)
```html
<!-- AVANT : -->
{% if request.status == 'approved_manager' %}
    <form method="post" action="{% url 'leave:leave_approval_process' request.pk %}">
        <!-- Boutons Approuver/Rejeter -->
    </form>
{% endif %}

<!-- APRÈS : -->
{% if request.status == 'pending' and request.employee.employee_profile.role == 'manager' or request.status == 'approved_manager' %}
    <form method="post" action="{% url 'leave:leave_approval_process' request.pk %}">
        <!-- Boutons Approuver/Rejeter -->
    </form>
{% endif %}
```
**Impact** : Les boutons d'action apparaissent pour les deux types de demandes (managers `pending` + employés `approved_manager`).

---

### 2. `templates/leave/leave_request_list_ultra_modern.html`

**Lignes 195-202** : Affichage des cartes de demande

**AVANT** (déjà correct, mais vérification) :
```html
{% if request.status == 'pending' or request.status == 'approved_manager' %}border-amber-500{% endif %}
data-status="{% if request.status == 'pending' or request.status == 'approved_manager' %}pending{% endif %}">
{% if request.status == 'pending' or request.status == 'approved_manager' %}bg-amber-100{% endif %}
{% if request.status == 'pending' or request.status == 'approved_manager' %}⏳{% endif %}
```

**APRÈS** : 
✅ **Aucun changement nécessaire** - Le template gère déjà `status='pending'` correctement.

**Impact** : Les demandes de managers avec `status='pending'` seront automatiquement affichées avec le bon style (bordure ambre, emoji ⏳).

---

### 3. `templates/leave/leave_approval_list.html`

**Ligne 113** : Attribut data-status (pour filtres JavaScript)
```html
<!-- AVANT : -->
data-status="{% if request.status == 'approved_manager' %}pending{% endif %}">

<!-- APRÈS : -->
data-status="{% if request.status == 'pending' or request.status == 'approved_manager' %}pending{% endif %}">
```
**Impact** : Les filtres JavaScript fonctionneront pour les deux types de demandes.

---

**Ligne 134** : Couleur de fond du badge
```html
<!-- AVANT : -->
{% elif request.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}

<!-- APRÈS : -->
{% elif request.status == 'pending' or request.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}
```
**Impact** : Même couleur de badge pour les deux types de demandes.

---

**Ligne 138** : Affichage conditionnel
```html
<!-- AVANT : -->
{% if request.status == 'approved_manager' %}
    <!-- Contenu -->
{% endif %}

<!-- APRÈS : -->
{% if request.status == 'pending' or request.status == 'approved_manager' %}
    <!-- Contenu -->
{% endif %}
```
**Impact** : Le contenu s'affiche pour les deux types de demandes.

---

### 4. `templates/leave/leave_approval_detail.html`

**Ligne 33** : Couleur de fond du header
```html
<!-- AVANT : -->
{% elif object.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}

<!-- APRÈS : -->
{% elif object.status == 'pending' or object.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}
```
**Impact** : Même couleur de header pour les deux types de demandes.

---

**Ligne 197** : Affichage des boutons d'action
```html
<!-- AVANT : -->
{% if is_manager and object.status == 'pending' or is_rh and object.status == 'approved_manager' %}
    <!-- Boutons Approuver/Rejeter -->
{% endif %}

<!-- APRÈS : -->
{% if is_manager and object.status == 'pending' or is_rh and (object.status == 'pending' and object.employee.employee_profile.role == 'manager' or object.status == 'approved_manager') %}
    <!-- Boutons Approuver/Rejeter -->
{% endif %}
```
**Impact** : Les boutons d'action apparaissent pour le RH quand :
- `status='pending'` ET `role='manager'` (managers directs)
- OU `status='approved_manager'` (employés validés par manager)

---

### 5. `templates/leave/leave_request_detail.html`

**Ligne 33** : Couleur de fond du header
```html
<!-- AVANT : -->
{% elif object.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}

<!-- APRÈS : -->
{% elif object.status == 'pending' or object.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}
```
**Impact** : Même couleur de header pour les deux types de demandes.

---

**Lignes 120-121** : Indicateur visuel de workflow
```html
<!-- AVANT : -->
<div class="... {% if object.status in 'approved_manager,approved_rh' %}bg-green-100{% endif %}">
    {% if object.status in 'approved_manager,approved_rh' %}
        <!-- Icône check -->
    {% endif %}
</div>

<!-- APRÈS : -->
<!-- Pas de changement nécessaire - 'approved_manager' reste géré -->
<!-- Les managers avec 'pending' n'ont pas encore été validés, donc pas de check vert -->
```
**Impact** : ✅ **Aucun changement nécessaire** - Le template gère déjà correctement les statuts.

---

### 6. `templates/components/status_badge.html` (Vérification)

**Ligne 7** : Gestion des statuts
```html
<!-- ACTUEL : -->
{% elif status == 'pending' or status == 'approved_manager' %}bg-yellow-100 text-yellow-800{% endif %}
```

**Impact** : ✅ **Aucun changement nécessaire** - Le composant gère déjà `status='pending'` correctement.

---

## 📊 Résumé des Modifications

| Template | Lignes Modifiées | Type de Changement | Complexité |
|----------|------------------|-------------------|------------|
| `rh_leave_management_ultra_modern.html` | 37, 119, 139 | Ajout conditions + nouveau filtre | ⚠️ Moyenne |
| `leave_request_list_ultra_modern.html` | 195-202 | ✅ Aucun changement | ✅ Aucune |
| `leave_approval_list.html` | 113, 134, 138 | Ajout `or status == 'pending'` | ✅ Simple |
| `leave_approval_detail.html` | 33, 197 | Ajout conditions | ⚠️ Moyenne |
| `leave_request_detail.html` | 33 | Ajout `or status == 'pending'` | ✅ Simple |
| `components/status_badge.html` | - | ✅ Aucun changement | ✅ Aucune |

**Total** : 4 templates à modifier réellement (1 template avec 3 modifications, 3 templates avec modifications simples)

---

## 🎯 Principe des Modifications

### Pattern Général

**AVANT** : Vérifier seulement `status == 'approved_manager'`

**APRÈS** : Vérifier `status == 'pending'` ET `role == 'manager'` OU `status == 'approved_manager'`

```html
<!-- Pattern général -->
{% if request.status == 'pending' and request.employee.employee_profile.role == 'manager' or request.status == 'approved_manager' %}
    <!-- Contenu -->
{% endif %}
```

### Cas Spéciaux

1. **Filtre dropdown** : Ajouter une option séparée pour les managers
2. **Boutons d'action** : Afficher pour les deux types de demandes
3. **Badges de statut** : Afficher "À valider" pour les deux types

---

## ⏱️ Temps Estimé

- **Template 1** (`rh_leave_management_ultra_modern.html`) : 15-20 min (3 modifications)
- **Template 2** (`leave_approval_list.html`) : 10 min (3 modifications simples)
- **Template 3** (`leave_approval_detail.html`) : 10-15 min (2 modifications)
- **Template 4** (`leave_request_detail.html`) : 5 min (1 modification simple)

**Total** : ~40-50 minutes

---

## ✅ Vérifications Après Modifications

1. ✅ Les demandes de managers avec `status='pending'` s'affichent dans la liste RH
2. ✅ Les badges de statut sont corrects pour les deux types
3. ✅ Les boutons d'action (Approuver/Rejeter) apparaissent pour les deux types
4. ✅ Les filtres fonctionnent correctement
5. ✅ Les couleurs et styles sont cohérents

---

**Date de création** : Novembre 2025  
**Branche** : `workflow-manager-coherent`

