# 🕐 Système de Profils Horaires Contractuels

## Vue d'ensemble

Le système de profils horaires permet de gérer les heures contractuelles des employés avec :
- **HDC (Heure Début Contractuelle)** : Si l'employé pointe avant, l'heure est plafonnée à HDC
- **HFC (Heure Fin Contractuelle)** : Si l'employé pointe après, l'heure est plafonnée à HFC
- **Pause variable** : Chaque profil définit sa propre durée de pause
- **Historisation** : Tous les changements sont tracés (immuabilité des paies)
- **Réutilisabilité** : Un profil peut être assigné à plusieurs employés

## Architecture

### Modèles de données

#### 1. WorkSchedule (Profil horaire)
```python
class WorkSchedule(models.Model):
    name = "Bureau Standard"                  # Nom du profil
    description = "Horaire de bureau"         # Description
    start_time = time(8, 0)                   # HDC : 08:00
    end_time = time(18, 0)                    # HFC : 18:00
    pause_start = time(12, 0)                 # Début pause : 12:00
    pause_end = time(14, 0)                   # Fin pause : 14:00
    is_default = True                         # Profil par défaut ?
    created_by = User                         # Créé par (RH)
```

**Méthodes utiles :**
- `get_pause_duration_hours()` → 2.0 (heures de pause)
- `get_contractual_duration_hours()` → 8.0 (heures travail par jour)

#### 2. EmployeeScheduleHistory (Historisation)
```python
class EmployeeScheduleHistory(models.Model):
    employee = EmployeeProfile                # L'employé
    work_schedule = WorkSchedule              # Le profil horaire
    assigned_date = date(2025, 1, 15)         # Date d'assignation
    end_date = date(2025, 3, 1)               # Date de fin (nullable)
    assigned_by = User                        # Assigné par (RH)
```

**Principe d'immuabilité :**
- Quand un employé change de profil, l'ancien historique est fermé (`end_date` = aujourd'hui)
- Un nouvel historique est créé (`assigned_date` = aujourd'hui)
- Les pointages passés gardent leurs heures calculées (pas de recalcul)

#### 3. EmployeeProfile.current_work_schedule
```python
current_work_schedule = ForeignKey(WorkSchedule, null=True, blank=True)
```
- Dénormalisation pour performance
- Toujours synchronisé avec l'historique actif

### Services

#### WorkScheduleService
Service principal pour gérer les profils horaires.

**Méthodes clés :**

```python
# 1. Récupérer le profil d'un employé pour une date donnée
schedule = WorkScheduleService.get_schedule_for_date(
    employee=jean,
    target_date=date(2025, 1, 20)
)
# → Retourne le profil valide à cette date (grâce à l'historique)

# 2. Changer le profil d'un employé
history = WorkScheduleService.change_employee_schedule(
    employee=jean,
    new_schedule=profil_matin,
    assigned_by_user=rh_marie
)
# → Ferme l'ancien historique, crée le nouveau, met à jour current_work_schedule

# 3. Lister les employés sur un profil
employees = WorkScheduleService.get_employees_by_schedule(profil_bureau)
# → Liste tous les employés actuellement sur ce profil

# 4. Vérifier si un profil peut être supprimé
can_delete = WorkScheduleService.can_delete_schedule(profil_test)
# → False si des employés l'utilisent actuellement
```

#### HoursCalculationService
Service de calcul des heures avec correction HDC/HFC.

```python
# Calcul avec profil horaire
worked_hours = HoursCalculationService.calculate_worked_hours_with_schedule(
    employee_profile=jean,
    punch_in=punch_in,  # 07:45
    punch_out=punch_out  # 18:30
)
# Logique :
# 1. in_time (07:45) < HDC (08:00) → correction à 08:00
# 2. out_time (18:30) > HFC (18:00) → correction à 18:00
# 3. Calcul : (18:00 - 08:00) - pause (2h) = 8h
```

## Interface RH

### URLs disponibles
- `/hr/schedules/` : Liste des profils horaires
- `/hr/schedules/create/` : Créer un nouveau profil
- `/hr/schedules/<pk>/` : Détail d'un profil
- `/hr/schedules/<pk>/edit/` : Modifier un profil
- `/hr/schedules/<pk>/delete/` : Supprimer un profil
- `/hr/employees/<id>/change-schedule/` : Changer le profil d'un employé

### Templates créés
1. `schedule_list.html` : Liste tous les profils avec nombre d'employés
2. `schedule_form.html` : Formulaire création/modification (validation temps)
3. `schedule_detail.html` : Affiche détails + liste employés assignés
4. `change_employee_schedule.html` : Interface changement profil employé
5. `schedule_confirm_delete.html` : Confirmation suppression (+ vérifications)

### Formulaires

#### WorkScheduleForm
```python
# Champs :
- name : Nom du profil (unique)
- description : Description optionnelle
- start_time : HDC (format HH:MM)
- end_time : HFC (format HH:MM)
- pause_start : Début pause
- pause_end : Fin pause
- is_default : Profil par défaut ?

# Validations :
✓ pause_start < pause_end
✓ start_time < end_time
✓ Un seul profil par défaut maximum
```

#### ChangeEmployeeScheduleForm
```python
# Champs :
- new_schedule : Sélection du nouveau profil

# Affichage :
- Profil actuel de l'employé
- Liste déroulante des profils disponibles
- Message d'avertissement (immuabilité)
```

### Intégration dans création d'employés

Le champ `current_work_schedule` a été ajouté aux formulaires :
- `EmployeeCreateFormSimple` : Création employé
- `EmployeeProfileForm` : Modification profil
- Dropdown avec tous les profils disponibles
- Si aucun n'est sélectionné, le profil par défaut est utilisé

## Workflow complet

### 1. RH crée un profil horaire
```
RH → /hr/schedules/create/
→ Remplit le formulaire :
   - Nom : "Équipe du Matin"
   - HDC : 06:00
   - HFC : 14:00
   - Pause : 10:00 - 10:30
→ Enregistre
→ Profil créé, disponible pour assignation
```

### 2. RH assigne le profil à un employé
```
Option A : Lors de la création
  → /hr/employees/create/
  → Sélectionne le profil dans le dropdown

Option B : Changement de profil
  → /hr/schedules/<pk>/ (détail profil)
  → Clique sur "Changer profil" pour un employé
  → Sélectionne le nouveau profil
  → Validation
  → Historique créé automatiquement
```

### 3. Employé effectue ses pointages
```
Employé arrive à 05:45 (avant HDC 06:00)
Employé part à 14:30 (après HFC 14:00)

Calcul automatique :
  1. Correction HDC : 05:45 → 06:00
  2. Correction HFC : 14:30 → 14:00
  3. Durée : 14:00 - 06:00 = 8h
  4. Pause : 0.5h
  5. Heures travaillées : 8h - 0.5h = 7.5h
```

### 4. RH consulte l'historique
```
→ /hr/schedules/<pk>/
→ Section "Employés assignés"
→ Voit la liste avec dates d'assignation
→ Peut voir l'historique complet de chaque employé
```

## Tests

### test_schedule_calculation.py
Test unitaire du calcul des heures avec 8 scénarios :
- ✅ Heures normales (8h-18h) → 8h
- ✅ Arrivée avant HDC (7h-18h) → 8h (plafonnée)
- ✅ Départ après HFC (8h-19h) → 8h (plafonnée)
- ✅ Double correction (7h-19h) → 8h
- ✅ Demi-journée matin (8h-12h) → 2h
- ✅ Demi-journée après-midi (14h-18h) → 2h
- ✅ Arrivée en retard (10h-18h) → 6h
- ✅ Départ anticipé (8h-16h) → 6h

### test_workflow_schedules.py
Test end-to-end du workflow complet :
1. ✅ Création de profil horaire
2. ✅ Assignation de profil à un employé
3. ✅ Création d'historique automatique
4. ✅ Calcul avec correction HDC/HFC
5. ✅ Validation des heures contractuelles
6. ✅ Changement de profil
7. ✅ Historisation avec date de fin
8. ✅ Principe d'immuabilité (récupération historique)
9. ✅ Service de récupération pour date passée

**Résultat : 🎉 Tous les tests passent avec succès**

## Migration

### 0007_workschedule_employeeprofile_current_work_schedule_and_more.py

```python
# 1. Crée la table WorkSchedule
# 2. Ajoute current_work_schedule à EmployeeProfile
# 3. Crée la table EmployeeScheduleHistory
# 4. Applique les contraintes et index
```

### Script de données initiales
`create_default_schedule.py` :
- Crée le profil "Bureau Standard" (8h-18h, pause 12h-14h)
- Assigne ce profil aux 14 employés existants
- Crée l'historique initial

## Avantages du système

### 1. Flexibilité
- Profils réutilisables (un profil → plusieurs employés)
- Création illimitée de profils
- Adaptation à tous les types d'horaires

### 2. Immuabilité
- Les paies passées ne changent jamais
- Historique complet pour audit
- Traçabilité de tous les changements

### 3. Performance
- Dénormalisation (current_work_schedule)
- Requêtes optimisées (index sur dates)
- Calculs rapides

### 4. Conformité légale
- Heures contractuelles respectées
- Plafonnement automatique (HDC/HFC)
- Audit trail complet

## Cas d'usage

### Équipes alternées
```python
# Équipe du matin
WorkSchedule(name="Matin", start_time="06:00", end_time="14:00")

# Équipe du soir
WorkSchedule(name="Soir", start_time="14:00", end_time="22:00")

# Rotation hebdomadaire
→ change_employee_schedule() chaque lundi
```

### Temps partiel
```python
# Mi-temps matin
WorkSchedule(name="Mi-temps matin", start_time="08:00", end_time="12:00")

# Mi-temps après-midi
WorkSchedule(name="Mi-temps AM", start_time="14:00", end_time="18:00")
```

### Horaires variables
```python
# Cadres
WorkSchedule(name="Cadre", start_time="08:00", end_time="18:00", 
             pause_start="12:00", pause_end="13:00")  # 1h pause

# Ouvriers
WorkSchedule(name="Ouvrier", start_time="07:00", end_time="16:00",
             pause_start="12:00", pause_end="12:30")  # 30min pause
```

## Sécurité

### Permissions
- **Création/modification de profils** : RH/DG uniquement
- **Assignation de profils** : RH/DG uniquement
- **Consultation historique** : RH/DG uniquement
- **Pointages** : Tous les employés (utilise automatiquement leur profil)

### Validations
- Cohérence des horaires (start < end, pause_start < pause_end)
- Unicité du nom de profil
- Un seul profil par défaut maximum
- Impossible de supprimer un profil utilisé

### Audit
- Tous les changements sont tracés
- Utilisateur responsable enregistré
- Dates d'effectivité précises

## Maintenance

### Ajouter un nouveau profil
```bash
# Via interface RH (recommandé)
/hr/schedules/create/

# Ou via shell Django
python manage.py shell
from accounts.models import WorkSchedule
WorkSchedule.objects.create(
    name="Nouveau profil",
    start_time=time(9, 0),
    end_time=time(17, 0),
    pause_start=time(12, 30),
    pause_end=time(13, 30),
    is_default=False,
    created_by=user
)
```

### Modifier le profil par défaut
```python
# 1. Désactiver l'ancien défaut
old_default = WorkSchedule.objects.get(is_default=True)
old_default.is_default = False
old_default.save()

# 2. Activer le nouveau défaut
new_default = WorkSchedule.objects.get(name="Nouveau Standard")
new_default.is_default = True
new_default.save()
```

### Consulter l'historique d'un employé
```python
from accounts.models import EmployeeScheduleHistory

history = EmployeeScheduleHistory.objects.filter(
    employee__employee_id="EMP001"
).order_by('-assigned_date')

for entry in history:
    print(f"{entry.work_schedule.name}: {entry.assigned_date} → {entry.end_date or 'actif'}")
```

## Évolutions futures possibles

1. **Profils hebdomadaires** : Différents horaires par jour de la semaine
2. **Rotation automatique** : Changement de profil selon un planning
3. **Congés intégrés** : Ajustement automatique selon les absences
4. **Export Excel** : Rapport des affectations et historiques
5. **Notifications** : Alert RH lors des changements de profil
6. **Statistiques** : Analyse des heures par profil

## Conclusion

Le système de profils horaires est **opérationnel à 100%** :
- ✅ Modèles créés et migrés
- ✅ Services fonctionnels et testés
- ✅ Interface RH complète
- ✅ Intégration dans création d'employés
- ✅ Tests unitaires et end-to-end validés
- ✅ Documentation complète

**Status : Production Ready 🚀**

---

*Implémentation réalisée conformément aux captures d'écran et spécifications fournies.*
*Tous les tests passent avec succès.*
*Date : Octobre 2025*
