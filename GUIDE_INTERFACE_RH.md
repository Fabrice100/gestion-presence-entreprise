# 🏢 Guide d'Utilisation de l'Interface RH

## 📋 Vue d'ensemble

L'interface RH du système de gestion de présence permet la validation finale des demandes de congés qui ont été approuvées par les managers.

## 🔗 Accès à l'Interface

**URL:** `/leave/approvals/`  
**Rôle requis:** `rh_dg` (Ressources Humaines/Direction Générale)

## 🔐 Utilisateur de Test

- **Username:** `rh.dg`
- **Mot de passe:** Défini lors de la création
- **Rôle:** `rh_dg`

## 📊 Fonctionnalités Disponibles

### 1. 📈 Tableau de Bord Principal
- **Statistiques globales** des demandes de congés
- **Vue d'ensemble** des demandes en attente
- **Indicateurs** de performance du système

### 2. 📋 Liste des Demandes à Valider

L'interface affiche uniquement les demandes ayant le statut `approved_manager` :

| Colonne | Description |
|---------|-------------|
| **Employé** | Nom complet + département |
| **Type de congé** | Congés payés, maladie, etc. |
| **Période** | Dates de début et fin |
| **Durée** | Nombre de jours |
| **Demandé le** | Date de création |
| **Actions** | Bouton "Valider" |

### 3. ✅ Validation Détaillée

Cliquer sur "Valider" ouvre une page détaillée avec :
- **Informations employé** (photo, département, historique)
- **Détails de la demande** (motif, pièces jointes)
- **Historique** des validations (manager)
- **Actions disponibles** : Approuver ou Rejeter

## 🔄 Workflow de Validation

```
Employee → Manager → RH/DG → Approuvé Final
                     ↑
                 Vous êtes ici
```

### Statuts des Demandes

1. **`submitted`** - Soumise par l'employé
2. **`approved_manager`** - ✅ Approuvée manager → **Visible RH**
3. **`approved_rh`** - ✅ Approuvée RH → Congé accordé
4. **`rejected`** - ❌ Rejetée à n'importe quelle étape

## 📊 Demandes Actuellement en Attente

```
🔍 4 demandes en attente de validation RH :
   • dev1 - Congés payés (31/10/2025)
   • dev2 - Congés payés (13/10/2025)
   • manager.it - Événements familiaux (22/10/2025)
   • dev1 - Congé maladie (13/10/2025)
```

## 🎨 Design System Intégré

L'interface utilise le design system uniforme avec :
- **Couleurs cohérentes** avec le reste de l'application
- **Icons Bootstrap** pour une navigation intuitive
- **Responsive design** pour tous les écrans
- **Animations fluides** pour une meilleure UX

## 🔧 Architecture Technique

### Vues Principales
- `LeaveApprovalListView` - Liste des demandes
- `LeaveApprovalDetailView` - Détails d'une demande
- `LeaveApprovalUpdateView` - Traitement de la validation

### Templates
- `leave_approval_list.html` - Interface principale
- `leave_approval_detail.html` - Page de validation détaillée

### Permissions
- Utilise `RHPermissionMixin` pour la sécurité
- Logs automatiques des actions
- Validation des rôles intégrée

## 🚀 Utilisation Pratique

### Étape 1 : Connexion
1. Aller sur `http://127.0.0.1:8000/accounts/login/`
2. Se connecter avec le compte `rh.dg`
3. Redirection automatique vers le dashboard

### Étape 2 : Accès aux Validations
1. Cliquer sur "Congés" dans le menu
2. Sélectionner "Validations en attente"
3. Voir la liste des 4 demandes actuelles

### Étape 3 : Validation d'une Demande
1. Cliquer sur "Valider" pour une demande
2. Examiner les détails
3. Choisir "Approuver" ou "Rejeter"
4. Ajouter un commentaire si nécessaire
5. Confirmer l'action

## 📱 Interface Mobile

L'interface est entièrement responsive :
- **Navigation adaptée** aux petits écrans
- **Tableaux scrollables** horizontalement
- **Boutons optimisés** pour le tactile

## 🔔 Notifications

Après validation :
- **Email automatique** envoyé à l'employé
- **Notification** dans le système
- **Mise à jour** des soldes de congés
- **Log** de l'action dans l'historique

## 🎯 Bonnes Pratiques

### ✅ À Faire
- Valider les demandes rapidement (< 48h)
- Vérifier les soldes de congés avant validation
- Ajouter des commentaires pour les rejets
- Consulter l'historique de l'employé

### ❌ À Éviter
- Valider sans examiner les détails
- Oublier de traiter les demandes urgentes
- Rejeter sans justification
- Valider des congés dépassant les soldes

## 🔍 Maintenance

### Vérifications Régulières
- Surveiller les demandes en attente
- Vérifier les soldes de congés
- Consulter les statistiques mensuelles
- Mettre à jour les types de congés si nécessaire

### Sauvegardes
- Base de données sauvegardée automatiquement
- Logs des actions conservés
- Historique complet des validations

## 📞 Support

En cas de problème :
1. Vérifier les logs dans `/logs/`
2. Consulter l'administrateur système
3. Contacter l'équipe de développement

---

**Développé avec ❤️ suivant les principes SOLID**  
**Version:** 1.0 | **Dernière mise à jour:** Octobre 2025