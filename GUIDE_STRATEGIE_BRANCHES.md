# Guide : Stratégie de Branches pour Tester l'Approche Proposée

## 🎯 Objectif

Garder la branche `full-project-snapshot` **intacte** pour la présentation, tout en implémentant l'approche proposée (workflow cohérent) sur une **nouvelle branche**.

---

## 📋 Situation Actuelle

- **Branche actuelle** : `full-project-snapshot` (pour présentation)
- **État** : Fonctionnel, prêt pour présentation
- **Modifications à tester** : Workflow Manager → RH (approche proposée)

---

## 🎯 Stratégies Disponibles

### ✅ **Stratégie 1 : Nouvelle Branche de Développement (RECOMMANDÉE)**

**Principe** : Créer une nouvelle branche à partir de `full-project-snapshot` pour tester les modifications.

#### Avantages
- ✅ Branche de présentation intacte
- ✅ Possibilité de revenir facilement
- ✅ Comparaison facile entre les deux approches
- ✅ Pas de risque pour la présentation

#### Inconvénients
- ⚠️ Nécessite de gérer deux branches
- ⚠️ Synchronisation si modifications communes

#### Étapes

```bash
# 1. S'assurer d'être sur full-project-snapshot et à jour
git checkout full-project-snapshot
git pull origin full-project-snapshot

# 2. Créer une nouvelle branche à partir de full-project-snapshot
git checkout -b workflow-manager-coherent

# 3. Vérifier qu'on est sur la nouvelle branche
git branch
# * workflow-manager-coherent
#   full-project-snapshot

# 4. Implémenter les modifications (suivre GUIDE_MODIFICATION_WORKFLOW_MANAGER.md)

# 5. Commiter les modifications
git add .
git commit -m "feat(workflow): implémenter workflow cohérent Manager → RH"

# 6. Pousser la nouvelle branche (optionnel)
git push origin workflow-manager-coherent
```

#### Structure Résultante

```
full-project-snapshot (intact, pour présentation)
    ↓
workflow-manager-coherent (nouvelle branche avec modifications)
```

---

### ✅ **Stratégie 2 : Branche de Feature avec Backup**

**Principe** : Créer une branche de feature et sauvegarder l'état actuel.

#### Avantages
- ✅ Backup explicite de l'état actuel
- ✅ Possibilité de restaurer facilement
- ✅ Nom de branche explicite

#### Inconvénients
- ⚠️ Branche de backup supplémentaire à gérer

#### Étapes

```bash
# 1. Créer une branche de backup (optionnel mais recommandé)
git checkout full-project-snapshot
git checkout -b full-project-snapshot-backup
git push origin full-project-snapshot-backup

# 2. Revenir sur full-project-snapshot
git checkout full-project-snapshot

# 3. Créer la branche de feature
git checkout -b feature/workflow-manager-coherent

# 4. Implémenter les modifications

# 5. Commiter et pousser
git add .
git commit -m "feat(workflow): implémenter workflow cohérent Manager → RH"
git push origin feature/workflow-manager-coherent
```

#### Structure Résultante

```
full-project-snapshot (intact, pour présentation)
full-project-snapshot-backup (backup explicite)
    ↓
feature/workflow-manager-coherent (nouvelle branche avec modifications)
```

---

### ✅ **Stratégie 3 : Tag de Sauvegarde**

**Principe** : Créer un tag Git pour marquer l'état actuel avant modifications.

#### Avantages
- ✅ Tag léger, pas de branche supplémentaire
- ✅ Référence permanente à l'état actuel
- ✅ Facile à restaurer

#### Inconvénients
- ⚠️ Les tags sont généralement pour les versions, pas pour le développement

#### Étapes

```bash
# 1. Créer un tag de sauvegarde
git checkout full-project-snapshot
git tag v1.0-presentation
git push origin v1.0-presentation

# 2. Créer une nouvelle branche
git checkout -b workflow-manager-coherent

# 3. Implémenter les modifications

# 4. Pour restaurer l'état tagué (si nécessaire)
git checkout v1.0-presentation
```

#### Structure Résultante

```
full-project-snapshot (intact, pour présentation)
    ↓ (tag: v1.0-presentation)
workflow-manager-coherent (nouvelle branche avec modifications)
```

---

## 🔄 Workflow Recommandé (Stratégie 1)

### Phase 1 : Préparation

```bash
# 1. Vérifier l'état actuel
git status
git branch

# 2. S'assurer que full-project-snapshot est à jour
git checkout full-project-snapshot
git pull origin full-project-snapshot

# 3. Vérifier qu'il n'y a pas de modifications non commitées
git status
# Si oui, soit commiter, soit stash
```

### Phase 2 : Création de la Nouvelle Branche

```bash
# 1. Créer la nouvelle branche
git checkout -b workflow-manager-coherent

# 2. Vérifier qu'on est sur la bonne branche
git branch
# * workflow-manager-coherent
#   full-project-snapshot

# 3. Vérifier que le code est identique
git diff full-project-snapshot
# (devrait être vide)
```

### Phase 3 : Implémentation

```bash
# 1. Suivre le guide GUIDE_MODIFICATION_WORKFLOW_MANAGER.md
# 2. Faire les modifications étape par étape
# 3. Tester après chaque modification importante
```

### Phase 4 : Commit et Push

```bash
# 1. Vérifier les modifications
git status
git diff

# 2. Commiter
git add .
git commit -m "feat(workflow): implémenter workflow cohérent Manager → RH

- Modifier création demande manager: status='pending' au lieu de 'approved_manager'
- Adapter filtres RH pour inclure managers avec status='pending'
- Mettre à jour templates pour affichage cohérent
- Adapter statistiques et compteurs
- Suivre GUIDE_MODIFICATION_WORKFLOW_MANAGER.md"

# 3. Pousser la nouvelle branche (optionnel)
git push origin workflow-manager-coherent
```

---

## 🔀 Navigation Entre les Branches

### Basculer entre les branches

```bash
# Aller sur la branche de présentation
git checkout full-project-snapshot

# Aller sur la branche de test
git checkout workflow-manager-coherent

# Voir les différences entre les deux branches
git diff full-project-snapshot..workflow-manager-coherent
```

### Comparer les deux approches

```bash
# Voir les fichiers modifiés
git diff --name-only full-project-snapshot..workflow-manager-coherent

# Voir les différences détaillées
git diff full-project-snapshot..workflow-manager-coherent

# Voir les statistiques de modifications
git diff --stat full-project-snapshot..workflow-manager-coherent
```

---

## 🧪 Tests et Validation

### Tester la Nouvelle Branche

```bash
# 1. Basculer sur la nouvelle branche
git checkout workflow-manager-coherent

# 2. Lancer le serveur
python manage.py runserver

# 3. Tester les scénarios (voir GUIDE_MODIFICATION_WORKFLOW_MANAGER.md - Étape 9)
# - Manager crée demande → doit être 'pending'
# - RH voit la demande
# - RH approuve/rejette
# - Statistiques correctes
```

### Revenir à la Branche de Présentation

```bash
# 1. Basculer sur full-project-snapshot
git checkout full-project-snapshot

# 2. Vérifier que tout est intact
python manage.py runserver
# Tester que le workflow actuel fonctionne toujours
```

---

## 📊 Comparaison des Stratégies

| Critère | Stratégie 1 | Stratégie 2 | Stratégie 3 |
|---------|-------------|-------------|-------------|
| **Simplicité** | ✅ Très simple | ⚠️ Moyenne | ✅ Simple |
| **Sécurité** | ✅ Élevée | ✅ Très élevée | ✅ Élevée |
| **Flexibilité** | ✅ Élevée | ✅ Élevée | ⚠️ Moyenne |
| **Recommandation** | ✅ **OUI** | ⚠️ Si besoin de backup explicite | ⚠️ Si utilisation de tags |

---

## 🎯 Recommandation Finale

### ✅ **Stratégie 1 : Nouvelle Branche de Développement**

**Pourquoi ?**
- ✅ Simple et efficace
- ✅ Pas de risque pour la branche de présentation
- ✅ Facile à comparer les deux approches
- ✅ Standard dans le développement Git

**Nom suggéré pour la nouvelle branche :**
- `workflow-manager-coherent`
- `feature/workflow-manager-coherent`
- `improve/workflow-manager-coherent`

---

## 📝 Checklist de Démarrage

- [ ] Vérifier qu'on est sur `full-project-snapshot`
- [ ] Vérifier qu'il n'y a pas de modifications non commitées
- [ ] Créer la nouvelle branche : `git checkout -b workflow-manager-coherent`
- [ ] Vérifier qu'on est sur la nouvelle branche : `git branch`
- [ ] Suivre `GUIDE_MODIFICATION_WORKFLOW_MANAGER.md` pour les modifications
- [ ] Tester après chaque modification importante
- [ ] Commiter les modifications : `git commit -m "..."`
- [ ] (Optionnel) Pousser la branche : `git push origin workflow-manager-coherent`

---

## 🔄 Retour en Arrière (si nécessaire)

### Annuler les modifications sur la nouvelle branche

```bash
# Si on veut recommencer depuis le début
git checkout workflow-manager-coherent
git reset --hard full-project-snapshot
```

### Supprimer la nouvelle branche (si on ne veut plus la garder)

```bash
# Supprimer la branche locale
git checkout full-project-snapshot
git branch -D workflow-manager-coherent

# Supprimer la branche distante (si poussée)
git push origin --delete workflow-manager-coherent
```

### Restaurer l'état exact de full-project-snapshot

```bash
# Si on a modifié full-project-snapshot par erreur
git checkout full-project-snapshot
git reset --hard origin/full-project-snapshot
```

---

## 🎓 Commandes Utiles

### Voir toutes les branches

```bash
# Branches locales
git branch

# Branches distantes
git branch -r

# Toutes les branches
git branch -a
```

### Voir l'historique des branches

```bash
# Historique de la branche actuelle
git log --oneline

# Comparer les commits entre deux branches
git log full-project-snapshot..workflow-manager-coherent

# Voir le graphique des branches
git log --oneline --graph --all
```

### Voir les différences

```bash
# Différences entre deux branches
git diff full-project-snapshot..workflow-manager-coherent

# Fichiers modifiés
git diff --name-only full-project-snapshot..workflow-manager-coherent

# Statistiques
git diff --stat full-project-snapshot..workflow-manager-coherent
```

---

## ⚠️ Points d'Attention

1. **Ne jamais modifier `full-project-snapshot` directement**
   - Toujours créer une nouvelle branche pour les modifications

2. **Vérifier la branche avant de commiter**
   ```bash
   git branch
   # S'assurer qu'on est sur workflow-manager-coherent, pas full-project-snapshot
   ```

3. **Tester avant de pousser**
   - Tester localement avant de pousser la nouvelle branche

4. **Documenter les modifications**
   - Utiliser des messages de commit clairs
   - Référencer le guide de modification

---

## 📚 Ressources

- `GUIDE_MODIFICATION_WORKFLOW_MANAGER.md` : Guide détaillé des modifications
- `ANALYSE_COMPARATIVE_WORKFLOW_MANAGER.md` : Comparaison des deux approches

---

**Date de création** : Novembre 2025  
**Branche** : `full-project-snapshot`

