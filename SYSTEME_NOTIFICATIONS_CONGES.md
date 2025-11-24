# Système de Notifications pour les Demandes de Congés

**Date** : 23 Novembre 2025  
**Branche** : `full-project-snapshot`

---

## 📧 Workflow de Notifications

### 1. Employé crée une demande de congé

**Qui reçoit une notification ?**
- ✅ **Manager** de l'employé

**Quand ?**
- Immédiatement après la création de la demande
- Status de la demande : `pending`

**Code** (`leave/workflow_views.py` lignes 238-241) :
```python
if saved_request.status == 'pending' and hasattr(saved_request, 'manager') and saved_request.manager:
    # Notifier le manager
    NotificationService.send_leave_pending_notification(saved_request, saved_request.manager)
```

**Email envoyé au Manager** :
- Sujet : "⏳ Nouvelle demande de congé à valider"
- Contenu : Détails de la demande, solde de congés de l'employé
- Action : Lien vers la page de validation

---

### 2. Manager crée une demande de congé

**Qui reçoit une notification ?**
- ✅ **RH** (tous les comptes RH actifs)

**Quand ?**
- Immédiatement après la création de la demande
- Status de la demande : `approved_manager` (auto-approbation manager)

**Code** (`leave/workflow_views.py` lignes 242-246) :
```python
elif saved_request.status == 'approved_manager':
    # Notifier les RH
    rh_users = User.objects.filter(employee_profile__role='rh', employee_profile__is_active=True)
    for rh_user in rh_users:
        NotificationService.send_leave_pending_notification(saved_request, rh_user)
```

**Email envoyé au RH** :
- Sujet : "⏳ Nouvelle demande de congé à valider (validation finale RH)"
- Contenu : Détails de la demande, validation précédente du manager
- Action : Lien vers la page de validation

---

### 3. Manager approuve une demande d'employé

**Qui reçoit une notification ?**
- ✅ **Employé** (demandeur)
- ✅ **RH** (tous les comptes RH actifs)

**Quand ?**
- Immédiatement après l'approbation par le manager
- Status de la demande : `approved_manager`

**Code** (`leave/workflow_views.py` lignes 584-592) :
```python
if action == 'approve':
    NotificationService.send_leave_approved_notification(leave_request, user)
    
    # Si c'est un manager qui approuve, notifier les RH
    if profile.role == 'manager':
        rh_users = User.objects.filter(employee_profile__role='rh', employee_profile__is_active=True)
        for rh_user in rh_users:
            NotificationService.send_leave_pending_notification(leave_request, rh_user)
```

**Emails envoyés** :

1. **À l'Employé** :
   - Sujet : "✅ Demande de congé validée par votre manager"
   - Contenu : Détails de la demande, commentaire du manager
   - Note : "⚠️ IMPORTANT : Votre demande nécessite encore la validation finale des Ressources Humaines"

2. **Au RH** :
   - Sujet : "⏳ Nouvelle demande de congé à valider (validation finale RH)"
   - Contenu : Détails de la demande, validation précédente du manager
   - Action : Lien vers la page de validation

---

### 4. Manager rejette une demande d'employé

**Qui reçoit une notification ?**
- ✅ **Employé** (demandeur)

**Quand ?**
- Immédiatement après le rejet par le manager
- Status de la demande : `rejected_manager`

**Code** (`leave/workflow_views.py` ligne 594) :
```python
else:  # reject
    NotificationService.send_leave_rejected_notification(leave_request, user, comment)
```

**Email envoyé à l'Employé** :
- Sujet : "❌ Demande de congé rejetée par votre manager"
- Contenu : Détails de la demande, motif du rejet (commentaire obligatoire)

---

### 5. RH approuve une demande (validation finale)

**Qui reçoit une notification ?**
- ✅ **Employé** (demandeur)

**Quand ?**
- Immédiatement après l'approbation finale par le RH
- Status de la demande : `approved_rh`

**Code** (`leave/workflow_views.py` ligne 585) :
```python
if action == 'approve':
    NotificationService.send_leave_approved_notification(leave_request, user)
```

**Email envoyé à l'Employé** :
- Sujet : "✅ Demande de congé définitivement approuvée"
- Contenu : Détails de la demande, solde de congés restant, commentaire RH

---

### 6. RH rejette une demande (décision finale)

**Qui reçoit une notification ?**
- ✅ **Employé** (demandeur)

**Quand ?**
- Immédiatement après le rejet final par le RH
- Status de la demande : `rejected_rh`

**Code** (`leave/workflow_views.py` ligne 594) :
```python
else:  # reject
    NotificationService.send_leave_rejected_notification(leave_request, user, comment)
```

**Email envoyé à l'Employé** :
- Sujet : "❌ Demande de congé rejetée (décision finale RH)"
- Contenu : Détails de la demande, motif du rejet (commentaire obligatoire)

---

## 📊 Tableau Récapitulatif

| Action | Demandeur | Qui reçoit notification ? | Type d'email |
|--------|-----------|----------------------------|--------------|
| **Employé crée demande** | Employé | Manager | ⏳ Pending (à valider) |
| **Manager crée demande** | Manager | RH | ⏳ Pending (validation finale) |
| **Manager approuve** | Employé | Employé + RH | ✅ Approuvé (employé) + ⏳ Pending (RH) |
| **Manager rejette** | Employé | Employé | ❌ Rejeté |
| **RH approuve** | Employé/Manager | Employé/Manager | ✅ Approuvé définitivement |
| **RH rejette** | Employé/Manager | Employé/Manager | ❌ Rejeté définitivement |

---

## 🔄 Workflow Complet (Exemple)

### Scénario 1 : Employé → Manager → RH

```
1. Employé crée demande
   └─> Status: 'pending'
   └─> 📧 Email au Manager : "Nouvelle demande à valider"

2. Manager approuve
   └─> Status: 'approved_manager'
   └─> 📧 Email à l'Employé : "Validée par manager (en attente RH)"
   └─> 📧 Email au RH : "Nouvelle demande à valider (validation finale)"

3. RH approuve définitivement
   └─> Status: 'approved_rh'
   └─> 📧 Email à l'Employé : "Définitivement approuvée"
```

### Scénario 2 : Manager → RH

```
1. Manager crée demande
   └─> Status: 'approved_manager' (auto-approbation)
   └─> 📧 Email au RH : "Nouvelle demande à valider (validation finale)"

2. RH approuve définitivement
   └─> Status: 'approved_rh'
   └─> 📧 Email au Manager : "Définitivement approuvée"
```

---

## ⚙️ Configuration

**Fichiers concernés** :
- `leave/workflow_views.py` : Logique de création et validation
- `accounts/notification_service.py` : Envoi des emails

**Types de notifications** :
1. `send_leave_pending_notification` : Notification pour validation en attente
2. `send_leave_approved_notification` : Notification d'approbation
3. `send_leave_rejected_notification` : Notification de rejet

---

## ✅ Résumé des Réponses

**Q : Quand un employé fait une demande, est-ce que son supérieur reçoit une notification ?**
- ✅ **OUI** - Le manager reçoit immédiatement un email

**Q : Si le manager fait une demande, le RH reçoit une notification ?**
- ✅ **OUI** - Le RH reçoit immédiatement un email (la demande est auto-approuvée par le manager)

**Q : Si c'est l'employé, le manager reçoit une notification ?**
- ✅ **OUI** - Le manager reçoit immédiatement un email

**Q : Dans le cas où le manager valide la demande d'un employé, le RH reçoit une notification ?**
- ✅ **OUI** - Le RH reçoit un email pour la validation finale

---

**Date de création** : 23 Novembre 2025

