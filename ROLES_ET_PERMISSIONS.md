# Rôles et Permissions du Système de Gestion de Présence

## Vue d'Ensemble des Acteurs

Ce document définit les rôles, responsabilités et permissions de chaque acteur au sein du système de gestion de présence et de congés.

---

## 1. Employé 👤

### Responsabilités Clés
Fournit la donnée brute de présence et initie le workflow de congés.

### Actions et Permissions Spécifiques
- Effectue le **Pointage** (Entrée/Sortie)
- Soumet des **Demandes de Congés** (avec sélection du type)
- **Annule** sa demande si non approuvée
- Consulte son propre **solde de congés** et historique de pointage

---

## 2. Manager 💼

### Responsabilités Clés
Assure la supervision hiérarchique de premier niveau au sein de son service.

### Actions et Permissions Spécifiques
- **Pré-valide ou Rejette** les demandes de congés de son **Service uniquement**
  - Le rejet nécessite un **motif obligatoire**
- Consulte le **Calendrier d'Absences** de son équipe (qui est présent/en congé)
- Effectue son propre pointage et demande ses congés (qui passent directement au RH)

---

## 3. RH (Ressources Humaines) 🏢

### Responsabilités Clés
Garantit la conformité, la gestion administrative, et la prise de décision finale.

### Actions et Permissions Spécifiques
- **Validation Finale** de **TOUS** les congés (y compris ceux des Managers)
- Met à jour le solde de congés après décompte ajusté (hors jours fériés)
- **Création des comptes** Managers et Employés
- Génère les **Rapports RH Essentiels** (Paie, Anomalies, Solde)
- Maintient la liste des **Jours Fériés**

---

## 4. Admin 💻

### Responsabilités Clés
Assure la sécurité et la configuration technique du système.

### Actions et Permissions Spécifiques
- Crée le compte **RH initial** et gère les super-utilisateurs
- Configure les polygones géographiques de la **Zone Autorisée (Geofencing)**
- Effectue la maintenance technique et les mises à jour

---

## Workflow de Validation des Congés

```
Employé → Demande de Congé
           ↓
    ┌──────┴──────┐
    ↓             ↓
 Manager      Manager
Pré-validation (si applicable)
    ↓
    ├── Approuvé → RH
    │              ↓
    │         Validation
    │         Finale
    ↓              ↓
 Rejeté     ┌──────┴──────┐
(Motif      ↓              ↓
obligatoire)  Approuvé    Rejeté
```

---

## Matrice des Permissions

| Action | Employé | Manager | RH | Admin |
|--------|---------|---------|----|-----|----|
| Pointage (Entrée/Sortie) | ✅ | ✅ | ✅ | ✅ |
| Soumettre demande de congé | ✅ | ✅ | ❌ | ❌ |
| Annuler sa propre demande | ✅ | ✅ | ❌ | ❌ |
| Pré-valider congés (Service) | ❌ | ✅ | ❌ | ❌ |
| Validation finale congés | ❌ | ❌ | ✅ | ❌ |
| Consulter solde de congés | ✅ (soi) | ✅ (équipe) | ✅ (tous) | ✅ (tous) |
| Créer comptes utilisateurs | ❌ | ❌ | ✅ | ❌ |
| Créer compte RH initial | ❌ | ❌ | ❌ | ✅ |
| Configurer Geofencing | ❌ | ❌ | ❌ | ✅ |
| Gérer jours fériés | ❌ | ❌ | ✅ | ❌ |
| Générer rapports RH | ❌ | ❌ | ✅ | ❌ |

---

## Notes Importantes

- Les **Managers** ont leurs propres demandes de congés qui passent **directement au RH**, sans pré-validation
- Le **rejet d'une demande** par un Manager nécessite toujours un **motif obligatoire**
- Le **RH** a un accès complet à la gestion administrative du système
- L'**Admin** est responsable de la configuration technique et de la sécurité globale du système
- La **Zone Autorisée (Geofencing)** est configurée uniquement par l'Admin pour s'assurer de la précision des pointages

