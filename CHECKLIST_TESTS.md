# ✅ CHECKLIST DE TESTS - PresencePro

## 🎯 Tests à effectuer avant la soutenance

---

## 1️⃣ LANDING PAGE & NAVIGATION

### Landing Page
- [ ] Accéder à http://127.0.0.1:8000/
- [ ] Vérifier que le logo PresencePro s'affiche
- [ ] Vérifier les 6 cartes de fonctionnalités
- [ ] Cliquer sur "Se connecter" → Redirige vers /accounts/login/
- [ ] Responsive : Tester sur mobile (F12 → Mode mobile)

### Navigation
- [ ] Menu latéral s'affiche correctement
- [ ] Logo "PresencePro" visible
- [ ] Tous les liens fonctionnent
- [ ] Menu responsive sur mobile

---

## 2️⃣ AUTHENTIFICATION

### Connexion
- [ ] Se connecter avec EMP007 / admin123 (Admin)
- [ ] Se connecter avec EMP009 / password123 (RH)
- [ ] Se connecter avec EMP008 / password123 (Manager)
- [ ] Se connecter avec EMP001 / password123 (Employé)
- [ ] Tester avec mauvais identifiants → Message d'erreur
- [ ] Cliquer sur comptes démo → Remplit automatiquement

### Déconnexion
- [ ] Cliquer sur profil → Déconnexion
- [ ] Redirige vers landing page

---

## 3️⃣ GESTION DES EMPLOYÉS (RH)

### Créer un employé
- [ ] Se connecter en RH (EMP009)
- [ ] Aller dans "Employés" → "Nouvel employé"
- [ ] Remplir : Prénom, Nom, Email, Département
- [ ] Essayer avec des chiffres dans prénom → Erreur
- [ ] Créer avec des vraies données
- [ ] **Vérifier le terminal** → Email de bienvenue affiché
- [ ] Vérifier que l'employé apparaît dans la liste

### Créer un manager
- [ ] Aller dans "Employés" → "Nouveau manager"
- [ ] Remplir les informations
- [ ] Vérifier l'email dans le terminal
- [ ] Vérifier dans la liste

### Modifier un employé
- [ ] Cliquer sur l'icône crayon
- [ ] Modifier le téléphone
- [ ] Enregistrer → Message de succès

### Liste des employés
- [ ] Voir tous les employés
- [ ] Badges de rôle colorés
- [ ] Badges de statut (Actif/Inactif)

---

## 4️⃣ GESTION DES DÉPARTEMENTS (RH)

### Créer un département
- [ ] Aller dans "Départements" → "Nouveau département"
- [ ] Remplir : Nom, Description, Manager
- [ ] Enregistrer → Message de succès

### Liste des départements
- [ ] Voir tous les départements
- [ ] Nombre d'employés affiché
- [ ] Modifier un département
- [ ] Tout fonctionne

---

## 5️⃣ DEMANDES DE CONGÉS (EMPLOYÉ)

### Créer une demande
- [ ] Se connecter en Employé (EMP001)
- [ ] Aller dans "Mes congés" → "Nouvelle demande"
- [ ] Sélectionner type : Congés payés
- [ ] Choisir dates (ex: dans 1 semaine)
- [ ] Remplir le motif
- [ ] Soumettre
- [ ] **Vérifier le terminal** → Email au manager
- [ ] Message de succès affiché

### Voir mes demandes
- [ ] Liste des demandes affichée
- [ ] Statut "En attente" visible
- [ ] Badges colorés corrects

---

## 6️⃣ VALIDATION CONGÉS (MANAGER)

### Valider une demande
- [ ] Se connecter en Manager (EMP008)
- [ ] Aller dans "Validation congés"
- [ ] Voir la demande de l'employé
- [ ] Cliquer sur "Valider"
- [ ] Voir les détails complets
- [ ] Ajouter un commentaire
- [ ] Cliquer sur "Approuver"
- [ ] **Vérifier le terminal** → 2 emails (employé + RH)
- [ ] Message de succès

### Rejeter une demande
- [ ] Créer une autre demande (en employé)
- [ ] Se reconnecter en Manager
- [ ] Cliquer sur "Valider"
- [ ] Essayer de rejeter sans commentaire → Erreur
- [ ] Ajouter un commentaire
- [ ] Cliquer sur "Rejeter"
- [ ] **Vérifier le terminal** → Email à l'employé
- [ ] Message de succès

---

## 7️⃣ VALIDATION FINALE (RH)

### Valider niveau 2
- [ ] Se connecter en RH (EMP009)
- [ ] Aller dans "Validation congés"
- [ ] Voir les demandes approuvées par manager
- [ ] Cliquer sur "Valider"
- [ ] Approuver la demande
- [ ] **Vérifier le terminal** → Email à l'employé
- [ ] Vérifier que le statut change à "Approuvé RH"

---

## 8️⃣ POINTAGE (EMPLOYÉ)

### Pointer l'entrée
- [ ] Se connecter en Employé
- [ ] Aller dans "Pointage"
- [ ] Horloge en temps réel fonctionne
- [ ] Cliquer sur "Pointer l'entrée"
- [ ] Autoriser la géolocalisation
- [ ] Message de succès
- [ ] Dernier pointage affiché

### Pointer la sortie
- [ ] Cliquer sur "Pointer la sortie"
- [ ] Autoriser la géolocalisation
- [ ] Message de succès

### Voir mes présences
- [ ] Aller dans "Mes présences"
- [ ] Statistiques affichées (jours, heures)
- [ ] Tableau des pointages
- [ ] Entrée et sortie visibles

---

## 9️⃣ DASHBOARDS

### Dashboard Employé
- [ ] Statistiques affichées (présences, congés)
- [ ] Dernières présences visibles
- [ ] Pas d'actions rapides

### Dashboard Manager
- [ ] Statistiques équipe
- [ ] Demandes en attente visibles
- [ ] Liste des membres de l'équipe

### Dashboard RH
- [ ] Statistiques globales
- [ ] Demandes en attente
- [ ] Employés récents

### Dashboard Admin
- [ ] Statistiques système
- [ ] Pas d'actions rapides

---

## 🔟 RESPONSIVE

### Mobile
- [ ] Ouvrir F12 → Mode mobile (375px)
- [ ] Navigation fonctionne
- [ ] Formulaires lisibles
- [ ] Tableaux scrollables
- [ ] Boutons pleine largeur

### Tablette
- [ ] Mode tablette (768px)
- [ ] Grille 2 colonnes
- [ ] Tout lisible

---

## 📧 EMAILS (DÉMONSTRATION)

### Console
- [ ] Terminal visible pendant les tests
- [ ] Emails affichent avec format amélioré
- [ ] Séparateurs visibles (====)
- [ ] Contenu complet lisible

### Mailtrap (si configuré)
- [ ] Aller sur mailtrap.io
- [ ] Créer un employé
- [ ] Email apparaît dans Mailtrap
- [ ] Design HTML visible

---

## ✅ VALIDATION FINALE

### Fonctionnalités critiques
- [ ] Toutes les pages chargent sans erreur
- [ ] Aucune erreur 404 ou 500
- [ ] Tous les formulaires fonctionnent
- [ ] Toutes les validations marchent
- [ ] Tous les emails s'envoient

### Design
- [ ] Cohérent sur toutes les pages
- [ ] Pas de gradients excessifs
- [ ] Pas d'animations gênantes
- [ ] Professionnel et sobre

### Performance
- [ ] Pages chargent rapidement
- [ ] Pas de lenteur
- [ ] Responsive fluide

---

## 🎓 SCÉNARIO COMPLET POUR SOUTENANCE

### Durée : 10 minutes

**Minute 1-2 : Introduction**
- Montrer landing page
- Expliquer PresencePro

**Minute 3-4 : Création employé**
- Se connecter en RH
- Créer un employé
- Montrer l'email dans le terminal

**Minute 5-7 : Workflow congés**
- Se connecter en Employé
- Demander un congé
- Se connecter en Manager → Approuver
- Se connecter en RH → Approuver
- Montrer les 3 emails dans le terminal

**Minute 8-9 : Pointage**
- Se connecter en Employé
- Pointer entrée
- Voir l'historique

**Minute 10 : Rapports**
- Se connecter en Admin
- Montrer les statistiques

---

**✅ Si tous ces tests passent, votre projet est PRÊT pour la soutenance !**

