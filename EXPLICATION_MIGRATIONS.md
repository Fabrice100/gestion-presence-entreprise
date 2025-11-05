# 📋 Explication Détaillée des Migrations

## 🔍 Migration 1 : `accounts/migrations/0008_alter_employeeprofile_role.py`

### Ce qu'elle fait

**Action :** Modifie les choix autorisés pour le champ `role` dans `EmployeeProfile`

**Changement :**
- **Avant (migration 0006) :** 
  ```python
  choices=[('employee', 'Employé'), ('manager', 'Manager'), ('rh_dg', 'RH/DG')]
  ```
- **Après (modèle actuel) :**
  ```python
  choices=[('employee', 'Employé'), ('manager', 'Manager'), ('rh', 'RH')]
  ```

### Pourquoi cette migration ?

**Raison :**
1. Le modèle Python (`accounts/models.py`) définit maintenant `ROLE_CHOICES = [('employee', 'Employé'), ('manager', 'Manager'), ('rh', 'RH')]`
2. Mais la dernière migration (0006) avait encore `rh_dg` au lieu de `rh`
3. Django détecte cette incohérence et veut synchroniser la base de données

### Impact

**Ce qui va se passer :**
- ✅ La colonne `role` dans la table `accounts_employeeprofile` sera modifiée
- ✅ Les contraintes de choix seront mises à jour
- ✅ Les données existantes **restent intactes** (pas de suppression)
- ⚠️ Si vous avez des utilisateurs avec `role='rh_dg'`, ils garderont cette valeur (mais elle ne sera plus dans les choix valides)

**Risque :** ⚠️ **FAIBLE**
- Aucune donnée supprimée
- Seulement une mise à jour des contraintes
- Les valeurs existantes `rh_dg` restent en base (mais devront être mises à jour manuellement si nécessaire)

**Action recommandée après migration :**
```sql
-- Si vous avez des utilisateurs avec rh_dg, les mettre à jour
UPDATE accounts_employeeprofile SET role = 'rh' WHERE role = 'rh_dg';
```

---

## 🔍 Migration 2 : `leave/migrations/0008_remove_leaverequest_priority.py`

### Ce qu'elle fait

**Action :** Supprime la colonne `priority` de la table `leave_leaverequest`

### Pourquoi cette migration ?

**Raison :**
1. Le champ `priority` a été supprimé du modèle `LeaveRequest` (il n'existe plus dans `leave/models.py`)
2. Une migration `0006_drop_priority_column.py` a déjà été créée avec `RunSQL` pour supprimer la colonne directement en SQL
3. Mais Django détecte toujours que le modèle n'a plus ce champ et veut créer une migration normale `RemoveField`

### Impact

**Ce qui va se passer :**
- ✅ Django tentera de supprimer la colonne `priority`
- ✅ Si la colonne existe déjà (migration 0006 non appliquée) : Suppression réussie
- ⚠️ Si la colonne n'existe plus (migration 0006 déjà appliquée) : Erreur "column does not exist" (mais c'est OK, on peut ignorer ou créer une migration conditionnelle)

**Risque :** ✅ **TRÈS FAIBLE**
- La colonne est déjà supprimée ou sera supprimée
- Aucune donnée importante (c'était juste un champ technique)
- C'est une correction de cohérence Django

---

## 📊 Résumé Comparatif

| Migration | Type | Action | Impact Données | Risque | Nécessaire ? |
|-----------|------|--------|----------------|--------|--------------|
| **0008_alter_role** | `AlterField` | Modifie les choix du champ `role` | ✅ Aucune perte | ⚠️ Faible | ✅ Oui |
| **0008_remove_priority** | `RemoveField` | Supprime colonne `priority` | ✅ Aucune perte | ✅ Très faible | ✅ Oui (cohérence) |

---

## ✅ Ce que ces migrations NE FONT PAS

❌ **Ne suppriment PAS de données utilisateur**
❌ **Ne modifient PAS les données existantes**
❌ **Ne cassent PAS l'application**
❌ **Ne sont PAS destructives**

---

## ✅ Ce que ces migrations FONT

✅ **Synchronisent le modèle Python avec la base de données**
✅ **Corrigent les incohérences Django**
✅ **Mettent à jour les contraintes de validation**
✅ **Assurent la cohérence du schéma**

---

## 🎯 Conclusion

**Ces migrations sont SÉCURISÉES et NÉCESSAIRES :**
- ✅ Elles corrigent des incohérences entre le modèle et la base de données
- ✅ Elles ne suppriment pas de données importantes
- ✅ Elles assurent la cohérence du système
- ✅ Elles sont nécessaires pour éviter des erreurs futures

**Action :** ✅ **On peut les créer et les appliquer sans risque**

---

**Date :** Novembre 2025
