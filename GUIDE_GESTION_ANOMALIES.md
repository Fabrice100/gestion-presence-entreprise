# 🚨 GUIDE DE GESTION DES ANOMALIES

## 📋 Vue d'ensemble

Le système gère automatiquement **2 types d'anomalies critiques** de pointage :

1. ✅ **Oubli de sortie** (`missing_punch_out`)
2. ✅ **Oubli d'entrée** (`missing_punch_in`)

**Note :** Les retards (`late_arrival`) et départs anticipés (`early_departure`) sont détectés et pris en compte dans le calcul des heures travaillées, mais ne génèrent **pas** d'anomalies dans la liste. Cela permet de ne créer des anomalies que pour les cas critiques nécessitant une action (oubli de pointage).

---

## 🔍 1. DÉTECTION DES ANOMALIES

### A. Oubli d'Entrée (`missing_punch_in`)

**Quand :** Lorsqu'un employé pointe la sortie sans avoir pointé l'entrée.

**Détection :** Automatique lors du calcul des heures travaillées.

**Où :** `hours_calculation_service.py` - Méthode `update_worked_hours_on_punch_out()`

```python
# Si pas d'entrée trouvée pour la sortie
if not attendance_in:
    # Créer anomalie automatiquement
    AttendanceAnomaly.objects.get_or_create(
        attendance=attendance_out,
        anomaly_type='missing_punch_in',
        defaults={
            'description': f"Sortie pointée sans entrée correspondante le {attendance_out.date}",
            'status': 'pending'
        }
    )
```

**Action automatique :**
- ✅ Anomalie créée dans la base de données
- ✅ `worked_hours` mis à `NULL`
- ✅ Statut : `pending`

---

### B. Oubli de Sortie (`missing_punch_out`)

**Quand :** Lorsqu'un employé pointe l'entrée le matin mais oublie de pointer la sortie le soir.

**Détection :** Via commande Django (à exécuter quotidiennement).

**Où :** `hours_calculation_service.py` - Méthode `detect_missing_punch_outs()`

**Exécution :**
```bash
python manage.py detect_missing_punches
# Par défaut vérifie la veille
```

**Ce qui se passe :**
1. Recherche toutes les entrées sans sortie correspondante pour la date cible
2. Pour chaque entrée sans sortie :
   - Met `worked_hours = NULL`
   - Crée une anomalie `missing_punch_out` avec statut `pending`

**À planifier :** Cette commande devrait être exécutée chaque jour (par exemple à 01:00 via Task Scheduler).

---

### C. Arrivée en Retard (`late_arrival`)

**Décision de conception :** ✅ **NE CRÉE PAS D'ANOMALIE**

**Comportement :**
- Le système détecte les retards et met le statut du pointage à `'late'`
- **MAIS** : Aucune anomalie n'est créée dans `AttendanceAnomaly`

**Raison :**
- Le calcul des heures travaillées prend déjà en compte les retards/départs
- Le système utilise les horaires contractuels (WorkSchedule) pour calculer les heures réellement travaillées
- Pas besoin d'anomalie car le calcul automatique gère déjà ces cas
- Les anomalies ne sont créées que pour les cas critiques nécessitant une action manuelle (oubli de pointage)

**Statut du pointage :**
- Le champ `status` du pointage indique `'late'` ou `'early'`
- Cela permet de voir dans l'historique si un pointage était en retard/départ anticipé
- Mais pas besoin d'alimenter la liste des anomalies pour ces cas

---

### D. Départ Anticipé (`early_departure`)

**Décision de conception :** ✅ **NE CRÉE PAS D'ANOMALIE**

**Comportement :**
- Le système détecte les départs anticipés et met le statut à `'early'`
- **MAIS** : Aucune anomalie n'est créée dans `AttendanceAnomaly`

**Raison :**
- Identique aux retards : le calcul des heures gère déjà ces cas
- Les horaires contractuels sont respectés dans le calcul
- Seulement les oublis de pointage créent des anomalies (action manuelle nécessaire)

---

## 👥 2. VISUALISATION ET GESTION DES ANOMALIES

### A. Pour les Managers

**URL :** `/attendance/anomalies/manager/`

**Filtrage :**
- ✅ Voir **UNIQUEMENT** les anomalies de son département
- ✅ Statistiques par statut (pending, justified, resolved)
- ✅ Filtrage par type d'anomalie
- ✅ Filtrage par statut

**Actions possibles :**
- Voir les détails d'une anomalie
- Résoudre/Justifier/Ignorer avec justification obligatoire

**Permissions :**
- Peut gérer uniquement les anomalies de son département
- Blocage si tentative d'accès à une anomalie d'un autre département

---

### B. Pour les RH

**URL :** `/attendance/anomalies/rh/`

**Filtrage :**
- ✅ Voir **TOUTES** les anomalies de tous les départements
- ✅ Statistiques globales
- ✅ Filtrage par département
- ✅ Filtrage par type d'anomalie
- ✅ Filtrage par statut
- ✅ Recherche par nom/ID employé

**Actions possibles :**
- Voir les détails de toutes les anomalies
- Résoudre/Justifier/Ignorer avec justification obligatoire
- Vue globale de l'entreprise

**Permissions :**
- Accès complet à toutes les anomalies
- Peut résoudre n'importe quelle anomalie

---

### C. Pour les Employés

**Accès :** Les employés peuvent voir leurs propres anomalies dans leur dashboard, mais ne peuvent pas les résoudre (réservé aux managers et RH).

---

## ✅ 3. RÉSOLUTION DES ANOMALIES

### Workflow de Résolution

```
Anomalie détectée
     ↓
Statut: pending
     ↓
Manager ou RH examine
     ↓
Choisit une action :
  ├─ Justifier (justified)
  ├─ Résoudre (resolved)
  └─ Ignorer (ignored)
     ↓
Statut final + Justification enregistrée
```

### Actions possibles

**1. Justifier (`justified`)**
- L'anomalie est expliquée (ex: "Retard justifié par transport en panne")
- Statut : `justified`
- Justification obligatoire
- Pas de sanction

**2. Résoudre (`resolved`)**
- L'anomalie a été corrigée (ex: "Pointage manuel ajouté")
- Statut : `resolved`
- Justification obligatoire
- Traçabilité : `resolved_by` et `resolved_at` enregistrés

**3. Ignorer (`ignored`)**
- L'anomalie n'est pas importante (ex: "Retard de 2 minutes, négligeable")
- Statut : `ignored`
- Justification obligatoire
- Pas d'action requise

---

## 📊 4. STATISTIQUES ET RAPPORTS

### Pour Manager

- **Nombre d'anomalies en attente** dans son département
- **Nombre d'anomalies justifiées**
- **Nombre d'anomalies résolues**
- **Total d'anomalies** de son équipe

### Pour RH

- **Vue globale** de toutes les anomalies
- **Statistiques par département**
- **Statistiques par type d'anomalie**
- **Tendances temporelles**

---

## ⚙️ 5. CONFIGURATION ET PARAMÈTRES

### Types d'Anomalies Actifs

Le système gère **2 types d'anomalies critiques** qui nécessitent une action manuelle :

```python
ANOMALY_TYPE_CHOICES = [
    ('missing_punch_out', 'Oubli de sortie'),    # ✅ Créée automatiquement
    ('missing_punch_in', 'Oubli d\'entrée'),      # ✅ Créée automatiquement
]
```

**Note :** Les types `late_arrival` et `early_departure` existent dans les choix mais ne sont **pas** créés automatiquement car :
- Le calcul des heures travaillées les prend déjà en compte
- Le système utilise les horaires contractuels (WorkSchedule) pour calculer correctement
- Seules les anomalies nécessitant une action manuelle (oubli de pointage) sont créées

### Statuts des Anomalies

```python
STATUS_CHOICES = [
    ('pending', 'En attente'),      # Nouvelle anomalie non traitée
    ('justified', 'Justifiée'),    # Expliquée et acceptée
    ('resolved', 'Résolue'),        # Corrigée ou traitée
    ('ignored', 'Ignorée'),         # Non importante, ignorée
]
```

---

## 🔧 6. COMMANDES DE DÉTECTION

### Commande pour Détecter les Oublis de Sortie

```bash
# Détecter les oublis de la veille
python manage.py detect_missing_punches

# Détecter pour une date spécifique
python manage.py detect_missing_punches --date 2025-10-28

# Détecter pour les 7 derniers jours
python manage.py detect_missing_punches --days 7

# Avec notifications email (si configuré)
python manage.py detect_missing_punches --notify
```

**⚠️ IMPORTANT :** Cette commande doit être planifiée pour s'exécuter quotidiennement (ex: Task Scheduler Windows à 01:00).

---

## 📝 7. EXEMPLE DE WORKFLOW COMPLET

### Scénario : Employé oublie de pointer la sortie

**Jour 1 - 8h00 :** Employé pointe l'entrée ✅
- Pointage créé : `punch_type='in'`, `time='08:00'`

**Jour 1 - 17h00 :** Employé oublie de pointer la sortie ❌
- Aucun pointage de sortie

**Jour 2 - 01:00 :** Commande de détection exécutée (automatique)
```bash
python manage.py detect_missing_punches
```

**Résultat :**
1. ✅ Anomalie créée :
   ```python
   AttendanceAnomaly(
       attendance=<pointage entrée du jour 1>,
       anomaly_type='missing_punch_out',
       description="Oubli de pointer la sortie le 2025-10-28...",
       status='pending'
   )
   ```
2. ✅ `worked_hours` mis à `NULL` sur le pointage d'entrée

**Jour 2 - Matin :** Manager voit l'anomalie
- Aller dans `/attendance/anomalies/manager/`
- Voir l'anomalie dans la liste avec statut "En attente"
- Cliquer pour voir les détails

**Manager choisit :**
- **Action :** "Résoudre"
- **Justification :** "Pointage manuel ajouté à 17h30"
- Cliquer sur "Valider"

**Résultat :**
- ✅ Statut : `resolved`
- ✅ `resolved_by` = Manager
- ✅ `resolved_at` = Date/heure de résolution
- ✅ Justification enregistrée

---

## ⚠️ 8. LIMITES ACTUELLES

### Ce qui fonctionne ✅

1. ✅ **Détection automatique de `missing_punch_in`** (sortie sans entrée)
   - Créée automatiquement lors du pointage de sortie
   - Fonctionne parfaitement

2. ✅ **Détection de `missing_punch_out`** (via commande quotidienne)
   - Créée via `python manage.py detect_missing_punches`
   - Fonctionne parfaitement (à planifier quotidiennement)

3. ✅ **Création d'anomalies dans la base de données**
   - Seulement pour les cas critiques (oubli de pointage)
   - Pas pour les retards/départs (gérés par calcul automatique)

4. ✅ **Visualisation par Manager** (département) et RH (global)
   - Filtrage correct par département
   - Statistiques et filtres fonctionnels

5. ✅ **Résolution avec justification obligatoire**
   - Workflow complet : Justifier/Résoudre/Ignorer
   - Traçabilité complète

6. ✅ **Calcul automatique des heures travaillées**
   - Les retards et départs anticipés sont pris en compte
   - Utilise les horaires contractuels (WorkSchedule)
   - **Pas besoin d'anomalie** car le calcul gère déjà ces cas

### Décisions de conception ✅

1. ✅ **Retards et départs anticipés : Pas d'anomalie créée**
   - **Raison :** Le calcul des heures travaillées les gère automatiquement
   - Le système utilise les horaires contractuels pour calculer correctement
   - Les anomalies ne sont créées que pour les cas nécessitant une action manuelle
   - Le statut du pointage (`late`/`early`) permet de voir l'historique

2. ⚠️ **Planification de la commande de détection**
   - À configurer : Task Scheduler Windows ou cron (Linux)
   - Exécution quotidienne automatique recommandée
   - Actuellement : Exécution manuelle nécessaire

---

## 📊 9. DONNÉES ET MODÈLES

### Modèle AttendanceAnomaly

```python
class AttendanceAnomaly:
    - attendance: ForeignKey(Attendance)     # Pointage concerné
    - anomaly_type: CharField                # Type d'anomalie
    - description: TextField                 # Description
    - status: CharField                      # pending/justified/resolved/ignored
    - justification: TextField (nullable)   # Justification de la résolution
    - resolved_by: ForeignKey(User, nullable) # Qui a résolu
    - resolved_at: DateTime (nullable)      # Quand résolu
    - created_at: DateTime                  # Date de création
```

### Relations

```
AttendanceAnomaly
    ↓ (ForeignKey)
Attendance
    ↓ (ForeignKey)
User (Employé)
    ↓ (OneToOne)
EmployeeProfile
    ↓ (ForeignKey)
Department
    ↓ (ForeignKey manager)
User (Manager)
```

---

## 🎯 10. RÉSUMÉ

### Ce qui fonctionne actuellement

✅ **Oubli sortie** : Détection automatique via commande quotidienne  
✅ **Oubli entrée** : Détection lors du pointage de sortie  
✅ **Gestion** : Managers voient leur département, RH voit tout  
✅ **Résolution** : Workflow complet avec justification obligatoire  
✅ **Traçabilité** : Toutes les actions sont enregistrées  
✅ **Calcul heures** : Retards/départs pris en compte automatiquement dans le calcul  
✅ **Horaires contractuels** : Le système utilise WorkSchedule pour calculer correctement  

### Décision de conception

✅ **Retards/Départs** : Pas d'anomalie créée (par design)
   - **Pourquoi :** Le calcul des heures gère déjà ces cas automatiquement
   - Les anomalies ne sont créées que pour les cas nécessitant une action manuelle
   - Le statut du pointage indique `late`/`early` pour l'historique

### À améliorer (optionnel)

⚠️ **Planification** : Commande de détection doit être exécutée manuellement
   - Recommandation : Configurer Task Scheduler pour exécution quotidienne automatique  

---

**Date :** $(date)  
**Version :** 1.0  
**Projet :** PresencePro - Système de Gestion de Présence

