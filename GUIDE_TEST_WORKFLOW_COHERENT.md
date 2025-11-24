# Guide de Test : Workflow Manager Cohérent

## ✅ Vérifications Préliminaires

**Check Django** : ✅ Aucune erreur détectée

---

## 🧪 Scénarios de Test

### Test 1 : Manager crée sa propre demande

**Objectif** : Vérifier que la demande de manager passe directement au RH avec `status='pending'`

**Étapes** :
1. Se connecter en tant que **Manager**
2. Aller dans "Mes demandes de congés" → "Nouvelle demande"
3. Remplir le formulaire et soumettre
4. **Vérifier** :
   - ✅ La demande a le statut `'pending'` (pas `'approved_manager'`)
   - ✅ La demande apparaît dans la liste RH
   - ✅ Le badge affiche "À valider"
   - ✅ Notification envoyée au RH

**Résultat attendu** : ✅ Demande avec `status='pending'` visible par le RH

---

### Test 2 : Employé crée une demande

**Objectif** : Vérifier que le workflow employé reste identique

**Étapes** :
1. Se connecter en tant qu'**Employé**
2. Aller dans "Mes demandes de congés" → "Nouvelle demande"
3. Remplir le formulaire et soumettre
4. **Vérifier** :
   - ✅ La demande a le statut `'pending'`
   - ✅ La demande apparaît dans la liste du Manager (pas du RH)
   - ✅ Notification envoyée au Manager

**Résultat attendu** : ✅ Workflow employé identique (pas de changement)

---

### Test 3 : Manager approuve une demande d'employé

**Objectif** : Vérifier que le workflow de validation manager reste identique

**Étapes** :
1. Se connecter en tant que **Manager**
2. Aller dans "Validation des congés"
3. Voir la demande de l'employé avec `status='pending'`
4. Cliquer sur "Approuver"
5. **Vérifier** :
   - ✅ La demande passe à `status='approved_manager'`
   - ✅ La demande apparaît maintenant dans la liste RH
   - ✅ Notification envoyée au RH

**Résultat attendu** : ✅ Workflow de validation manager identique (pas de changement)

---

### Test 4 : RH approuve une demande de manager

**Objectif** : Vérifier que le RH peut approuver les demandes de managers avec `status='pending'`

**Étapes** :
1. Se connecter en tant que **RH**
2. Aller dans "Gestion des congés"
3. Voir la demande du manager avec `status='pending'`
4. Cliquer sur "Approuver"
5. **Vérifier** :
   - ✅ La demande passe à `status='approved_rh'`
   - ✅ Le solde de congés est déduit
   - ✅ Notification envoyée au manager

**Résultat attendu** : ✅ RH peut approuver les demandes de managers

---

### Test 5 : RH approuve une demande d'employé (après manager)

**Objectif** : Vérifier que le RH peut approuver les demandes d'employés validées par manager

**Étapes** :
1. Se connecter en tant que **RH**
2. Aller dans "Gestion des congés"
3. Voir la demande d'employé avec `status='approved_manager'`
4. Cliquer sur "Approuver"
5. **Vérifier** :
   - ✅ La demande passe à `status='approved_rh'`
   - ✅ Le solde de congés est déduit
   - ✅ Notification envoyée à l'employé

**Résultat attendu** : ✅ RH peut approuver les demandes d'employés (workflow identique)

---

### Test 6 : Statistiques et compteurs

**Objectif** : Vérifier que les statistiques sont correctes

**Étapes** :
1. Se connecter en tant que **RH**
2. Aller dans le dashboard ou la page de gestion des congés
3. **Vérifier** :
   - ✅ `pending_count` inclut les managers avec `status='pending'` ET les employés avec `status='approved_manager'`
   - ✅ Les compteurs sont corrects

**Résultat attendu** : ✅ Statistiques correctes

---

### Test 7 : Filtres et affichage

**Objectif** : Vérifier que les filtres fonctionnent correctement

**Étapes** :
1. Se connecter en tant que **RH**
2. Aller dans "Gestion des congés"
3. Tester les filtres :
   - ✅ Filtre "Tous" : Affiche managers `pending` + employés `approved_manager`
   - ✅ Filtre "Managers (en attente RH)" : Affiche seulement les managers
   - ✅ Filtre "Validé Manager (en attente RH)" : Affiche seulement les employés validés

**Résultat attendu** : ✅ Filtres fonctionnent correctement

---

### Test 8 : Badges et affichage visuel

**Objectif** : Vérifier que les badges s'affichent correctement

**Étapes** :
1. Se connecter en tant que **RH**
2. Aller dans "Gestion des congés"
3. **Vérifier** :
   - ✅ Les demandes de managers avec `status='pending'` affichent "À valider" (badge jaune)
   - ✅ Les demandes d'employés avec `status='approved_manager'` affichent "À valider" (badge jaune)
   - ✅ Les couleurs sont cohérentes

**Résultat attendu** : ✅ Badges affichés correctement

---

## 🐛 Points d'Attention

### Erreurs possibles

1. **`AttributeError: 'LeaveRequest' object has no attribute 'employee_profile'`**
   - **Cause** : Accès à `request.employee.employee_profile.role` dans un template
   - **Solution** : Vérifier que `request.employee` a bien un `employee_profile`

2. **Demandes de managers non visibles par le RH**
   - **Cause** : Filtre incorrect dans `get_queryset()`
   - **Solution** : Vérifier que le filtre inclut `Q(status='pending', employee__employee_profile__role='manager')`

3. **Notifications non envoyées**
   - **Cause** : Logique de notification incorrecte
   - **Solution** : Vérifier que la condition `employee_profile.role == 'manager'` est correcte

---

## ✅ Checklist de Validation

- [ ] Test 1 : Manager crée demande → `status='pending'` → Visible par RH
- [ ] Test 2 : Employé crée demande → `status='pending'` → Visible par Manager
- [ ] Test 3 : Manager approuve employé → `status='approved_manager'` → Visible par RH
- [ ] Test 4 : RH approuve manager → `status='approved_rh'`
- [ ] Test 5 : RH approuve employé → `status='approved_rh'`
- [ ] Test 6 : Statistiques correctes
- [ ] Test 7 : Filtres fonctionnent
- [ ] Test 8 : Badges affichés correctement

---

## 📝 Notes

- **Branche** : `workflow-manager-coherent`
- **Date** : Novembre 2025
- **Statut** : En test

---

**Bon test ! 🚀**

