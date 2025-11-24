# Guide de Modification : Workflow Manager → RH

## 📋 Objectif

Modifier le workflow pour que les demandes de congé créées par un **Manager** passent directement au **RH** avec le statut `'pending'` (sans auto-validation), exactement comme les demandes d'**Employé** passent au **Manager**.

---

## 🔄 Workflow Actuel vs Nouveau Workflow

### Workflow Actuel

```
EMPLOYÉ :
  Demande → status='pending' → Manager valide → status='approved_manager' → RH valide → status='approved_rh'

MANAGER :
  Demande → status='approved_manager' (auto) → RH valide → status='approved_rh'
  ⚠️ Bypass de l'étape Manager (auto-validation)
```

### Nouveau Workflow (Objectif)

```
EMPLOYÉ :
  Demande → status='pending' → Manager valide → status='approved_manager' → RH valide → status='approved_rh'

MANAGER :
  Demande → status='pending' → RH valide → status='approved_rh'
  ✅ Pas d'auto-validation, workflow cohérent
```

---

## 📝 Étapes de Modification

### Étape 1 : Modifier la création de demande

**Fichier** : `attendance_system/leave/workflow_views.py`  
**Ligne** : ~195-199  
**Méthode** : `LeaveRequestCreateView.form_valid()`

**Changement :**
```python
# AVANT :
elif profile.role == 'manager':
    # MANAGER : Bypass pré-validation, va DIRECTEMENT au RH
    # Status 'approved_manager' = "Prêt pour validation RH finale"
    leave_request.status = 'approved_manager'

# APRÈS :
elif profile.role == 'manager':
    # MANAGER : Passe directement au RH avec status 'pending' (comme les employés)
    leave_request.status = 'pending'
    leave_request.manager = None  # Pas de manager pour les managers
```

---

### Étape 2 : Modifier les notifications lors de la création

**Fichier** : `attendance_system/leave/workflow_views.py`  
**Ligne** : ~238-246  
**Méthode** : `LeaveRequestCreateView.form_valid()` → `send_notifications()`

**Changement :**
```python
# AVANT :
elif saved_request.status == 'approved_manager':
    # Notifier les RH
    rh_users = User.objects.filter(employee_profile__role='rh', employee_profile__is_active=True)
    for rh_user in rh_users:
        NotificationService.send_leave_pending_notification(saved_request, rh_user)

# APRÈS :
elif saved_request.status == 'pending':
    # Vérifier si c'est une demande de manager ou d'employé
    if saved_request.employee.employee_profile.role == 'manager':
        # Manager : notifier directement les RH
        rh_users = User.objects.filter(employee_profile__role='rh', employee_profile__is_active=True)
        for rh_user in rh_users:
            NotificationService.send_leave_pending_notification(saved_request, rh_user)
    elif hasattr(saved_request, 'manager') and saved_request.manager:
        # Employé : notifier le manager
        NotificationService.send_leave_pending_notification(saved_request, saved_request.manager)
```

---

### Étape 3 : Modifier la vue RH (liste des demandes)

**Fichier** : `attendance_system/leave/workflow_views.py`  
**Ligne** : ~383-403  
**Méthode** : `LeaveApprovalListView.get_queryset()`

**Changement :**
```python
# AVANT :
elif profile.role == 'rh':
    # RH : voir les demandes 'approved_manager' qui attendent validation finale
    # 1. Demandes des employés validées par leur manager (status='approved_manager' avec manager_decision)
    # 2. Demandes des managers directement (status='approved_manager' sans manager_decision)
    if status_filter == 'pending':
        queryset = LeaveRequest.objects.filter(status='approved_manager')

# APRÈS :
elif profile.role == 'rh':
    # RH : voir les demandes en attente de validation finale
    # 1. Demandes des employés validées par leur manager (status='approved_manager')
    # 2. Demandes des managers directement (status='pending' avec role='manager')
    if status_filter == 'pending':
        queryset = LeaveRequest.objects.filter(
            Q(status='pending', employee__employee_profile__role='manager') |  # Managers directs
            Q(status='approved_manager')  # Employés validés par manager
        )
```

---

### Étape 4 : Modifier les statistiques RH

**Fichier** : `attendance_system/leave/workflow_views.py`  
**Ligne** : ~468  
**Méthode** : `LeaveApprovalListView.get_context_data()`

**Changement :**
```python
# AVANT :
elif profile.role == 'rh':
    context['pending_count'] = LeaveRequest.objects.filter(status='approved_manager').count()

# APRÈS :
elif profile.role == 'rh':
    context['pending_count'] = LeaveRequest.objects.filter(
        Q(status='pending', employee__employee_profile__role='manager') |  # Managers directs
        Q(status='approved_manager')  # Employés validés par manager
    ).count()
```

---

### Étape 5 : Modifier les autres filtres de statistiques

**Fichier** : `attendance_system/leave/workflow_views.py`  
**Lignes** : ~64, 157, 323, 403, 473, 699, 721, 728

**Action** : Remplacer tous les filtres `status='approved_manager'` ou `status__in=['approved_manager', ...]` par une logique qui inclut :
- `status='pending'` ET `employee__employee_profile__role='manager'` (managers directs)
- OU `status='approved_manager'` (employés validés par manager)

**Exemple :**
```python
# AVANT :
context['approved_count'] = all_requests.filter(status__in=['approved_manager', 'approved_rh']).count()

# APRÈS :
context['approved_count'] = all_requests.filter(
    Q(status='pending', employee__employee_profile__role='manager') |
    Q(status='approved_manager') |
    Q(status='approved_rh')
).count()
```

---

### Étape 6 : Modifier les templates

**Fichiers à modifier :**

#### 6.1. `templates/leave/rh_leave_management_ultra_modern.html`
**Ligne** : ~37, 119, 139

**Changement :**
```html
<!-- AVANT : -->
<option value="approved_manager" {% if request.GET.status == 'approved_manager' %}selected{% endif %}>Validé Manager (en attente RH)</option>
{% if request.status == 'approved_manager' %}
    {% include 'components/status_badge.html' with status='pending' icon='bi-clock' text='À valider' %}
{% endif %}

<!-- APRÈS : -->
<option value="pending_manager" {% if request.GET.status == 'pending_manager' %}selected{% endif %}>Managers (en attente RH)</option>
<option value="approved_manager" {% if request.GET.status == 'approved_manager' %}selected{% endif %}>Validé Manager (en attente RH)</option>
{% if request.status == 'pending' and request.employee.employee_profile.role == 'manager' %}
    {% include 'components/status_badge.html' with status='pending' icon='bi-clock' text='À valider' %}
{% elif request.status == 'approved_manager' %}
    {% include 'components/status_badge.html' with status='pending' icon='bi-clock' text='À valider' %}
{% endif %}
```

#### 6.2. `templates/leave/leave_request_list_ultra_modern.html`
**Ligne** : ~195-202

**Changement :**
```html
<!-- AVANT : -->
{% if request.status == 'pending' or request.status == 'approved_manager' %}border-amber-500{% endif %}
{% if request.status == 'pending' or request.status == 'approved_manager' %}⏳{% endif %}

<!-- APRÈS : -->
<!-- Pas de changement nécessaire, car 'pending' est déjà géré -->
{% if request.status == 'pending' or request.status == 'approved_manager' %}border-amber-500{% endif %}
{% if request.status == 'pending' or request.status == 'approved_manager' %}⏳{% endif %}
```

#### 6.3. `templates/leave/leave_approval_list.html`
**Ligne** : ~113, 134, 138

**Changement :**
```html
<!-- AVANT : -->
data-status="{% if request.status == 'approved_manager' %}pending{% endif %}">
{% elif request.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}

<!-- APRÈS : -->
data-status="{% if request.status == 'pending' or request.status == 'approved_manager' %}pending{% endif %}">
{% elif request.status == 'pending' or request.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}
```

#### 6.4. `templates/leave/leave_approval_detail.html`
**Ligne** : ~33, 197

**Changement :**
```html
<!-- AVANT : -->
{% elif object.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}
{% if is_manager and object.status == 'pending' or is_rh and object.status == 'approved_manager' %}

<!-- APRÈS : -->
{% elif object.status == 'pending' or object.status == 'approved_manager' %}bg-blue-100 text-blue-800{% endif %}
{% if is_manager and object.status == 'pending' or is_rh and (object.status == 'pending' and object.employee.employee_profile.role == 'manager' or object.status == 'approved_manager') %}
```

---

### Étape 7 : Vérifier les autres vues

**Fichier** : `attendance_system/leave/views.py`  
**Lignes** : ~75, 261, 368, 403

**Action** : Mettre à jour les compteurs/statistiques pour inclure les managers avec `status='pending'`.

**Exemple :**
```python
# AVANT :
'pending_count': all_requests.filter(status='approved_manager').count()

# APRÈS :
'pending_count': all_requests.filter(
    Q(status='pending', employee__employee_profile__role='manager') |
    Q(status='approved_manager')
).count()
```

---

### Étape 8 : Vérifier la méthode `can_be_approved_by`

**Fichier** : `attendance_system/leave/models.py`  
**Ligne** : ~336-355

**Action** : Vérifier que la logique permet au RH d'approuver les demandes de managers avec `status='pending'`.

**Vérification :**
```python
def can_be_approved_by(self, user):
    # Si c'est le RH, il peut toujours approuver
    if profile.is_rh():
        return True  # ✅ Fonctionne pour 'pending' (managers) et 'approved_manager' (employés)
    
    # Si c'est un manager, il peut approuver les demandes de son équipe
    if profile.is_manager() and self.employee.employee_profile.manager == user:
        return True  # ✅ Fonctionne pour 'pending' (employés)
    
    return False
```

**✅ Aucune modification nécessaire** - La logique actuelle fonctionne déjà.

---

### Étape 9 : Tester le workflow complet

**Scénarios à tester :**

1. ✅ **Manager crée une demande**
   - Statut doit être `'pending'`
   - RH doit voir la demande dans sa liste
   - Notification doit être envoyée au RH

2. ✅ **Employé crée une demande**
   - Statut doit être `'pending'`
   - Manager doit voir la demande dans sa liste
   - Notification doit être envoyée au manager

3. ✅ **Manager approuve une demande d'employé**
   - Statut doit passer à `'approved_manager'`
   - RH doit voir la demande dans sa liste
   - Notification doit être envoyée au RH

4. ✅ **RH approuve une demande de manager**
   - Statut doit passer à `'approved_rh'`
   - Solde doit être déduit

5. ✅ **RH approuve une demande d'employé (après manager)**
   - Statut doit passer à `'approved_rh'`
   - Solde doit être déduit

6. ✅ **Statistiques et compteurs**
   - Les compteurs doivent être corrects pour tous les rôles
   - Les filtres doivent fonctionner correctement

---

## ⚠️ Analyse des Risques Potentiels

### 🔴 Risque 1 : Confusion entre deux types de `'pending'`

**Problème :**
- `status='pending'` peut maintenant signifier :
  - Une demande d'**employé** en attente de validation par son **manager**
  - Une demande de **manager** en attente de validation par le **RH**

**Impact :** ⚠️ **MOYEN**
- Les filtres peuvent mélanger les deux types de demandes
- Les statistiques peuvent être incorrectes
- Les managers peuvent voir les demandes d'autres managers (même département)

**Solution :**
- Toujours vérifier `employee__employee_profile__role` pour distinguer :
  ```python
  Q(status='pending', employee__employee_profile__role='manager')  # Managers
  Q(status='pending', employee__employee_profile__role='employee')  # Employés
  ```

**Fichiers à modifier :**
- `workflow_views.py` ligne 336 : Exclure les managers du filtre `status='pending'` pour les managers
- `workflow_views.py` ligne 431 : Exclure les managers du filtre `status='pending'` pour les managers

---

### 🔴 Risque 2 : Filtres incomplets dans les vues

**Problème :**
- Si un filtre oublie d'inclure `status='pending'` pour les managers, les demandes de managers ne seront pas visibles.
- Les managers verront les demandes d'autres managers dans leur liste (même département avec `status='pending'`)

**Impact :** ⚠️ **ÉLEVÉ**
- Les demandes de managers peuvent disparaître de la vue RH
- Les managers peuvent voir des demandes qu'ils ne devraient pas voir
- Les statistiques seront incorrectes

**Solution :**
- Vérifier **tous** les endroits qui filtrent `status='approved_manager'`
- Les remplacer par une logique qui inclut les deux cas :
  ```python
  Q(status='pending', employee__employee_profile__role='manager') | Q(status='approved_manager')
  ```
- **IMPORTANT** : Pour les vues Manager, exclure les managers du filtre `status='pending'` :
  ```python
  # Pour les managers : seulement les employés
  queryset = base_queryset.filter(
      status='pending',
      employee__employee_profile__role='employee'  # Exclure les managers
  )
  ```

**Fichiers critiques :**
- `workflow_views.py` ligne 336 : Filtre Manager doit exclure `role='manager'`
- `workflow_views.py` ligne 431 : Statistiques Manager doivent exclure `role='manager'`

---

### 🔴 Risque 3 : Templates affichant incorrectement les statuts

**Problème :**
- Les templates peuvent afficher incorrectement les badges de statut si la logique n'est pas mise à jour.

**Solution :**
- Tester **tous** les templates qui affichent des statuts
- Vérifier que les badges s'affichent correctement pour :
  - `status='pending'` + `role='manager'` → "À valider" (RH)
  - `status='pending'` + `role='employee'` → "En attente" (Manager)
  - `status='approved_manager'` → "Validé Manager" (RH)

---

### 🔴 Risque 4 : Statistiques incorrectes

**Problème :**
- Les compteurs peuvent être incorrects si la logique n'est pas mise à jour partout.

**Solution :**
- Vérifier **tous** les endroits qui calculent des statistiques :
  - `pending_count`
  - `approved_count`
  - `rejected_count`
  - `total_count`

---

### 🔴 Risque 5 : Notifications manquantes ou dupliquées

**Problème :**
- Les notifications peuvent ne pas être envoyées ou être envoyées deux fois.

**Solution :**
- Tester les notifications pour chaque scénario :
  - Manager crée demande → RH doit recevoir notification
  - Employé crée demande → Manager doit recevoir notification
  - Manager approuve employé → RH doit recevoir notification

---

### 🔴 Risque 6 : Données existantes (migration)

**Problème :**
- Les demandes existantes créées par des managers ont `status='approved_manager'`.
- Après la modification, les nouvelles demandes de managers auront `status='pending'`.
- **Incohérence** : Deux statuts différents pour le même type de demande

**Impact :** ⚠️ **MOYEN**
- Les anciennes demandes continueront de fonctionner (visibles par RH avec `status='approved_manager'`)
- Les nouvelles demandes utiliseront `status='pending'`
- Peut créer de la confusion dans les statistiques et les filtres

**Solution :**
- **Option 1** : Laisser les anciennes demandes telles quelles (elles fonctionneront toujours)
  - ✅ Simple, pas de migration
  - ❌ Incohérence dans les données
- **Option 2** : Créer une migration pour mettre à jour les anciennes demandes :
  ```python
  # Migration Django
  LeaveRequest.objects.filter(
      status='approved_manager',
      employee__employee_profile__role='manager',
      manager_decision__isnull=True  # Pas de manager_decision = auto-validé
  ).update(status='pending')
  ```
  - ✅ Cohérence dans les données
  - ❌ Nécessite une migration et des tests

**Recommandation :** Option 2 pour la cohérence à long terme.

---

### 🔴 Risque 7 : Performance des requêtes

**Problème :**
- Les requêtes avec `Q()` et `employee__employee_profile__role` peuvent être plus lentes.
- Les jointures supplémentaires peuvent ralentir les listes

**Impact :** ⚠️ **FAIBLE à MOYEN**
- Impact minimal si les index sont corrects
- Peut être plus lent avec beaucoup de données

**Solution :**
- Utiliser `select_related()` et `prefetch_related()` :
  ```python
  queryset = LeaveRequest.objects.filter(...).select_related(
      'employee', 'employee__employee_profile'
  )
  ```
- Vérifier les index de base de données sur `employee__employee_profile__role`

---

### 🔴 Risque 8 : Managers voyant les demandes d'autres managers

**Problème :**
- Actuellement, les managers voient les demandes `status='pending'` de leur département
- Si un manager crée une demande avec `status='pending'`, un autre manager du même département pourrait la voir

**Impact :** ⚠️ **ÉLEVÉ**
- Violation de la confidentialité
- Les managers ne devraient voir que les demandes de leurs employés directs

**Solution :**
- **IMPORTANT** : Toujours filtrer par `employee__employee_profile__manager=user` pour les managers :
  ```python
  # Pour les managers : seulement leurs employés directs
  queryset = LeaveRequest.objects.filter(
      status='pending',
      employee__employee_profile__manager=user,  # Seulement leurs employés
      employee__employee_profile__role='employee'  # Exclure les managers
  )
  ```

**Fichiers critiques :**
- `workflow_views.py` ligne 336 : Ajouter filtre `employee__employee_profile__manager=user`
- `workflow_views.py` ligne 431 : Ajouter filtre `employee__employee_profile__manager=user`

---

## 🚨 Résumé des Risques Critiques

### ⚠️ Risques ÉLEVÉS (à corriger absolument)

1. **Managers voyant les demandes d'autres managers** (Risque 8)
   - **Impact** : Confidentialité, sécurité
   - **Solution** : Filtrer par `employee__employee_profile__manager=user`

2. **Filtres incomplets dans les vues** (Risque 2)
   - **Impact** : Demandes invisibles, statistiques incorrectes
   - **Solution** : Vérifier tous les filtres et exclure les managers des vues Manager

### ⚠️ Risques MOYENS (à vérifier)

3. **Confusion entre deux types de `'pending'`** (Risque 1)
   - **Impact** : Filtres mélangés, statistiques incorrectes
   - **Solution** : Toujours distinguer par `employee__employee_profile__role`

4. **Données existantes incohérentes** (Risque 6)
   - **Impact** : Incohérence dans les données
   - **Solution** : Migration pour mettre à jour les anciennes demandes

### ⚠️ Risques FAIBLES (à optimiser)

5. **Performance des requêtes** (Risque 7)
   - **Impact** : Lenteur possible
   - **Solution** : Utiliser `select_related()` et vérifier les index

---

## ✅ Checklist de Validation

- [ ] Étape 1 : Modification de la création de demande
- [ ] Étape 2 : Modification des notifications
- [ ] Étape 3 : Modification de la vue RH
- [ ] Étape 4 : Modification des statistiques RH
- [ ] Étape 5 : Modification des autres filtres
- [ ] Étape 6 : Modification des templates
- [ ] Étape 7 : Vérification des autres vues
- [ ] Étape 8 : Vérification de `can_be_approved_by`
- [ ] Étape 9 : Tests complets du workflow
- [ ] Vérification des risques 1-7
- [ ] Tests de performance
- [ ] Tests de notifications
- [ ] Tests de statistiques

---

## 📌 Notes Importantes

1. **Cohérence** : Tous les endroits qui filtrent `'approved_manager'` doivent être mis à jour pour inclure `'pending'` (managers).

2. **Distinction** : Toujours distinguer les managers des employés en vérifiant `employee__employee_profile__role`.

3. **Tests** : Tester **tous** les scénarios avant de déployer en production.

4. **Migration** : Considérer une migration pour les données existantes si nécessaire.

5. **Documentation** : Mettre à jour la documentation du projet après les modifications.

---

## 🔗 Fichiers Impactés

### Backend
- `attendance_system/leave/workflow_views.py` (principal)
- `attendance_system/leave/views.py` (statistiques)
- `attendance_system/leave/models.py` (vérification)

### Templates
- `templates/leave/rh_leave_management_ultra_modern.html`
- `templates/leave/leave_request_list_ultra_modern.html`
- `templates/leave/leave_approval_list.html`
- `templates/leave/leave_approval_detail.html`
- `templates/leave/leave_request_detail.html`
- `templates/components/status_badge.html`

### Services
- `attendance_system/accounts/notification_service.py` (vérification)

---

**Date de création** : Novembre 2025  
**Branche** : `full-project-snapshot`

