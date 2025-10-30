# 🧪 GUIDE DE TEST COMPLET - Système de Gestion de Présence

Ce guide vous permet de tester toutes les fonctionnalités principales du système de manière séquentielle.

---

## 📋 PRÉREQUIS

- Serveur Django démarré : `python manage.py runserver`
- Accès à `http://localhost:8000`
- Compte **superadmin** créé (ou créer avec `python manage.py createsuperuser`)

---

## 🎯 ÉTAPE 1 : CONFIGURER LA GÉOLOCALISATION (Admin)

### 1.1 Connexion en tant qu'Admin

1. Aller sur : `http://localhost:8000/admin/`
2. Se connecter avec les identifiants du superadmin
3. Vérifier l'accès au panneau d'administration Django

### 1.2 Configuration GPS

1. Dans le menu de gauche, cliquer sur **"Attendance"** → **"Company settings"**
2. Cliquer sur **"Add Company settings"** ou modifier les paramètres existants
3. Renseigner les informations GPS :

   ```
   Site Center Latitude: 6.3654
   Site Center Longitude: 2.4183
   Radius Meters: 200
   Accuracy Max Meters: 100
   ```

   **Note :** Ces coordonnées correspondent à Cotonou (Togo). Ajustez selon votre localisation réelle.

4. Cliquer sur **"Save"**

### 1.3 Vérification

- Les paramètres GPS sont maintenant configurés
- Tous les pointages seront validés selon cette zone

---

## 🎯 ÉTAPE 2 : CRÉER UN COMPTE RH

### 2.1 Méthode via Admin Django

1. Dans `/admin/`, aller dans **"Authentication and Authorization"** → **"Users"**
2. Cliquer sur **"Add user"**
3. Renseigner :
   - **Username** : `rh1` (ou autre nom)
   - **Email** : `rh1@entreprise.com`
   - **Password** : Choisir un mot de passe fort
   - Cliquer sur **"Save"**

4. Dans la section **"Employee Profile"** (en bas de la page) :
   - **Employee ID** : `RH001` (ou laisser vide, sera généré)
   - **Role** : `RH`
   - **Department** : Créer un département "RH" si nécessaire
   - **Can Punch** : `False` (RH ne pointe pas)
   - **Is Active** : `True`
   - Cliquer sur **"Save"**

### 2.2 Vérification

- Le compte RH est créé
- Se déconnecter de l'admin
- Se connecter avec le compte RH sur `http://localhost:8000/accounts/login/`
- Vérifier l'accès au dashboard RH

**Note importante :** ⚠️ Le système limite à **UN SEUL compte RH actif** à la fois. Si vous essayez de créer un deuxième compte RH, l'opération sera bloquée avec un message d'erreur. Pour créer un nouveau compte RH, vous devez d'abord désactiver le compte RH existant.

---

## 🎯 ÉTAPE 3 : CRÉER UN DÉPARTEMENT ET UN MANAGER (via RH)

### 3.1 Créer un Département

1. Connecté en tant que RH, aller dans **"Gestion RH"** → **"Départements"**
2. Cliquer sur **"Ajouter un département"**
3. Renseigner :
   - **Nom** : `Informatique` (ou autre)
   - **Description** : `Département informatique`
4. Cliquer sur **"Enregistrer"**

### 3.2 Créer un Manager

1. Toujours dans l'interface RH, aller dans **"Gestion RH"** → **"Employés"**
2. Cliquer sur **"Créer un Manager"**
3. Renseigner le formulaire :

   ```
   Informations personnelles:
   - Prénom: Jean
   - Nom: Dossou
   - Email: jean.dossou@entreprise.com
   
   Informations professionnelles:
   - Rôle: Manager
   - Département: Informatique
   ```

4. Cliquer sur **"Enregistrer"**
5. **IMPORTANT :** Noter les identifiants affichés :
   - **ID Employé** : (ex: `EMP001`)
   - **Mot de passe temporaire** : (affiché à l'écran)

### 3.3 Vérification

- Le manager est créé avec succès
- Un email devrait être envoyé au manager avec ses identifiants
- Le département "Informatique" a maintenant ce manager assigné

---

## 🎯 ÉTAPE 4 : CRÉER DES EMPLOYÉS (via RH)

### 4.1 Créer un Employé

1. Toujours connecté en tant que RH, aller dans **"Gestion RH"** → **"Employés"**
2. Cliquer sur **"Créer un Employé"**
3. Renseigner :

   ```
   Informations personnelles:
   - Prénom: Marie
   - Nom: Koffi
   - Email: marie.koffi@entreprise.com
   
   Informations professionnelles:
   - Rôle: Employé
   - Département: Informatique
   - Manager: Jean Dossou (le manager créé précédemment)
   ```

4. Cliquer sur **"Enregistrer"**
5. **Noter les identifiants** :
   - **ID Employé** : (ex: `EMP002`)
   - **Mot de passe temporaire**

### 4.2 Créer un deuxième Employé (optionnel)

Répéter les étapes 4.1 pour créer un autre employé si vous voulez tester avec plusieurs personnes.

---

## 🎯 ÉTAPE 5 : TESTER LE POINTAGE

### 5.1 Connexion en tant qu'Employé

1. Se déconnecter du compte RH
2. Aller sur `http://localhost:8000/accounts/login/`
3. Se connecter avec l'ID employé (ex: `EMP002`) et le mot de passe temporaire
4. **Première connexion :** Le système vous demandera de changer le mot de passe
   - Choisir un nouveau mot de passe
   - Confirmer

### 5.2 Pointer l'Arrivée (Punch In)

1. Dans le menu, aller sur **"Pointage"**
2. Vous verrez le bouton **"Pointer l'arrivée"**
3. Cliquer sur **"Pointer"**
4. Le navigateur demandera l'autorisation d'accès à la géolocalisation
   - Cliquer sur **"Autoriser"**
5. Le système vérifie :
   - ✅ Vous êtes dans la zone autorisée (200m du centre)
   - ✅ La précision GPS est acceptable (< 100m)
   - ✅ Il n'y a pas déjà de pointage d'entrée aujourd'hui

6. **Résultat attendu :**
   - Message de succès : "✅ Pointage entrée enregistré avec succès"
   - L'heure de pointage s'affiche
   - Le bouton devient **"Pointer la sortie"**

### 5.3 Pointer la Sortie (Punch Out)

1. Quelques minutes plus tard (ou immédiatement pour le test)
2. Cliquer sur **"Pointer la sortie"**
3. Autoriser à nouveau la géolocalisation
4. **Résultat attendu :**
   - Message de succès : "✅ Pointage sortie enregistré avec succès"
   - Les heures travaillées sont calculées automatiquement
   - Affichage de l'historique des pointages du jour

### 5.4 Vérifier l'Historique

1. Aller dans **"Présence"** → **"Mon historique"**
2. Vérifier que les pointages apparaissent
3. Vérifier le calcul des heures travaillées

---

## 🎯 ÉTAPE 6 : TESTER LA DEMANDE DE CONGÉ (Employé)

### 6.1 Créer une Demande de Congé

1. Toujours connecté en tant qu'employé, aller dans **"Congés"** → **"Mes demandes"**
2. Cliquer sur **"Nouvelle demande"**
3. Renseigner le formulaire :

   ```
   Type de congé: Congés payés
   Date de début: (choisir une date future, ex: dans 2 semaines)
   Date de fin: (choisir une date, ex: 3 jours après)
   Motif: Vacances familiales
   ```

4. **Vérification automatique :**
   - ✅ Solde de congés suffisant (30 jours annuels)
   - ✅ Pas de chevauchement avec d'autres demandes
   - ✅ Dates cohérentes (début < fin)

5. Cliquer sur **"Soumettre la demande"**

### 6.2 Vérification

- **Message de succès :** "Demande de congé créée avec succès !"
- La demande apparaît dans la liste avec le statut **"En attente"**
- Un email de notification est envoyé au manager pour validation

---

## 🎯 ÉTAPE 7 : TESTER LA VALIDATION MANAGER

### 7.1 Connexion en tant que Manager

1. Se déconnecter du compte employé
2. Se connecter avec le compte manager créé (ex: `EMP001` + mot de passe)
3. Si c'est la première connexion, changer le mot de passe

### 7.2 Valider la Demande

1. Aller dans **"Congés"** → **"Validation des demandes"**
2. Vous devriez voir la demande de congé de l'employé de votre département
3. Cliquer sur **"Traiter la demande"** (ou **"Examiner"**)
4. Choisir une action :

   **A. Approuver :**
   - Sélectionner **"Approuver"**
   - Optionnel : Ajouter un commentaire
   - Cliquer sur **"Valider"**
   - **Résultat :** La demande passe au statut "Approuvé par Manager"
   - Un email est envoyé à l'employé et aux RH

   **B. Rejeter :**
   - Sélectionner **"Rejeter"**
   - **Obligatoire :** Ajouter un motif de rejet
   - Cliquer sur **"Valider"**
   - **Résultat :** La demande passe au statut "Rejeté par Manager"
   - Un email est envoyé à l'employé avec le motif

### 7.3 Vérification Manager

- Dans la liste, voir les demandes avec leurs nouveaux statuts
- Les compteurs (Total, Approuvé, Rejeté) se mettent à jour

---

## 🎯 ÉTAPE 8 : TESTER LA VALIDATION RH (si Manager a approuvé)

### 8.1 Connexion en tant que RH

1. Se déconnecter du compte manager
2. Se connecter avec le compte RH créé à l'étape 2

### 8.2 Validation Finale RH

1. Aller dans **"Congés"** → **"Validation des demandes"**
2. Vous verrez :
   - Les demandes en attente de validation finale (statut "Approuvé par Manager")
   - Toutes les demandes de tous les départements
3. Cliquer sur **"Traiter la demande"** pour une demande approuvée par le manager
4. Choisir :

   **A. Approuver définitivement :**
   - Sélectionner **"Approuver"**
   - Optionnel : Commentaire
   - Cliquer sur **"Valider"**
   - **Résultat :**
     - ✅ Statut : "Approuvé par RH"
     - ✅ Les jours sont déduits du solde (excluant les jours fériés)
     - ✅ Email envoyé à l'employé

   **B. Rejeter :**
   - Sélectionner **"Rejeter"**
   - Motif obligatoire
   - Cliquer sur **"Valider"**
   - **Résultat :**
     - ❌ Statut : "Rejeté par RH"
     - ❌ Email envoyé à l'employé avec motif

### 8.3 Vérification RH

- Voir toutes les demandes avec leurs statuts finaux
- Les statistiques se mettent à jour
- Les soldes de congés sont correctement déduits

---

## 🎯 ÉTAPE 9 : TESTER D'AUTRES SCÉNARIOS

### 9.1 Test Manager qui Demande un Congé

1. Se connecter avec le compte manager
2. Faire une demande de congé
3. **Comportement attendu :**
   - La demande passe directement au statut "Approuvé par Manager"
   - Elle apparaît directement dans la liste RH (sans passer par validation manager)
   - Le RH doit faire la validation finale

### 9.2 Test Pointage Hors Zone

1. Se connecter avec un compte employé
2. Aller sur la page de pointage
3. Si vous êtes loin du bureau (> 200m), le système devrait :
   - Soit bloquer le pointage (si validation stricte)
   - Soit afficher un avertissement selon la configuration

### 9.3 Test Anomalies

1. Oublier de pointer la sortie un jour
2. Le lendemain, exécuter : `python manage.py detect_missing_punches`
3. Une anomalie devrait être créée automatiquement
4. Le manager et le RH peuvent la voir dans **"Anomalies"**

---

## ✅ CHECKLIST DE VÉRIFICATION

Avant de finaliser, vérifier que :

- [ ] Configuration GPS fonctionnelle
- [ ] Compte RH créé et accessible
- [ ] Département créé avec manager assigné
- [ ] Employé(s) créé(s) et assigné(s) au manager
- [ ] Pointage entrée fonctionnel (géolocalisation)
- [ ] Pointage sortie fonctionnel (calcul heures)
- [ ] Demande de congé créée avec succès
- [ ] Validation manager fonctionnelle (approuver/rejeter)
- [ ] Validation RH fonctionnelle (validation finale)
- [ ] Emails envoyés à chaque étape (vérifier console)
- [ ] Soldes de congés correctement déduits
- [ ] Historique et dashboards s'affichent correctement

---

## 📝 NOTES IMPORTANTES

### Emails en Développement

Par défaut, les emails s'affichent dans la **console** (backend console). Pour recevoir de vrais emails :

1. Configurer Mailtrap ou un service SMTP dans `.env`
2. Voir `env.example` pour la configuration

### Géolocalisation

Si la géolocalisation ne fonctionne pas dans le navigateur :
- Vérifier que le site est en HTTPS ou localhost
- Autoriser l'accès à la géolocalisation dans les paramètres du navigateur
- En développement, certains navigateurs peuvent bloquer la géolocalisation sur HTTP

### Création de Comptes RH

**⚠️ LIMITATION : UN SEUL COMPTE RH**  
Le système limite à **un seul compte RH actif** à la fois pour éviter la confusion et les conflits de permissions. Si vous essayez de créer un deuxième compte RH :
- Via Admin Django : Message d'erreur "Impossible de créer un nouveau compte RH"
- Solution : Désactiver le compte RH existant avant d'en créer un nouveau

---

## 🎓 RÉSUMÉ DU WORKFLOW

```
┌─────────────┐
│   Employé   │ → Crée demande congé
└──────┬──────┘
       │ (statut: pending)
       ▼
┌─────────────┐
│   Manager   │ → Approuve ou Rejette
└──────┬──────┘
       │ (statut: approved_manager / rejected_manager)
       ▼
┌─────────────┐
│     RH      │ → Validation finale
└──────┬──────┘
       │ (statut: approved_rh / rejected_rh)
       ▼
  Déduction solde (si approuvé)
```

---

**Date de création :** $(date)  
**Version :** 1.0  
**Projet :** PresencePro - Système de Gestion de Présence
