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
- Consulte son **Dashboard Personnel** (statistiques, derniers pointages)
- Consulte l'**historique de ses pointages** avec filtres par date et statut
- Consulte ses **anomalies personnelles** de pointage

---

## 2. Manager 💼

### Responsabilités Clés
Assure la supervision hiérarchique de premier niveau au sein de son service.

### Actions et Permissions Spécifiques
- **Pré-valide ou Rejette** les demandes de congés de son **Service uniquement**
  - Le rejet nécessite un **motif obligatoire**
- Consulte le **Calendrier d'Absences** de son équipe (qui est présent/en congé)
- Effectue son propre pointage et demande ses congés (qui passent directement au RH)
- Consulte le **Dashboard Manager** (effectif équipe, pointages aujourd'hui, demandes en attente)
- Consulte les **pointages de son équipe** avec filtres avancés
- Consulte les **anomalies de son équipe**
- Valide ou rejette les **heures supplémentaires** de son équipe

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
- Consulte le **Dashboard RH** (effectif, présences, absents, congés du jour)
- Gère les **anomalies globales** de l'entreprise
- Valide ou rejette les **heures supplémentaires** (toutes les demandes)
- Consulte et exporte les **rapports avancés** (PDF, Excel)
- Configure les **paramètres d'entreprise** (horaires, GPS, etc.)

---

## 4. Admin 💻

### Responsabilités Clés
Assure la sécurité et la configuration technique du système.

### Actions et Permissions Spécifiques
- Crée le compte **RH initial** et gère les super-utilisateurs
- Configure les polygones géographiques de la **Zone Autorisée (Geofencing)** (rayon circulaire actuellement)
- Effectue la maintenance technique et les mises à jour
- Accède à l'**administration Django** complète
- Gère la **configuration GPS avancée** (latitude, longitude, rayon, précision)
- Configure les **horaires de travail** (début, fin, tolérance retard)

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

---

## 5. MODULE HEURES SUPPLÉMENTAIRES ⏰

### Vue d'Ensemble

Le système calcule **automatiquement** les heures supplémentaires à partir des pointages et gère un workflow de validation.

### Fonctionnalités

#### Types de Heures Supplémentaires
- **Quotidiennes** : Dépassement de 8h/jour
- **Hebdomadaires** : Dépassement de 40h/semaine
- **Weekend** : Travail samedi/dimanche
- **Jours Fériés** : Travail jours fériés
- **Heures de Nuit** : Travail entre 22h-6h

#### Détection Automatique
- Calcul automatique après chaque pointage
- Classification par type d'heures supplémentaires
- Création automatique d'enregistrements `OvertimeRecord`

#### Workflow de Validation
- Manager → Validation préliminaire
- RH → Validation finale
- Motif obligatoire pour rejet

---

## 6. DASHBOARDS PAR RÔLE 📊

### Dashboard Employé
**Accès :** `/dashboard/employee/`

**Informations affichées :**
- Derniers pointages (5 derniers)
- Demandes de congés en attente
- Solde de congés restants
- Anomalies personnelles
- Prochaines absences planifiées
- Statistiques de présence

### Dashboard Manager
**Accès :** `/dashboard/manager/`

**Informations affichées :**
- Effectif de l'équipe
- Pointages de l'équipe aujourd'hui
- Demandes de validation en attente
- Anomalies de l'équipe
- Absences planifiées de l'équipe
- Statistiques de présence de l'équipe

### Dashboard RH/DG
**Accès :** `/dashboard/rh-dg/`

**Informations affichées :**
- Effectif total entreprise
- Présences aujourd'hui (tout le monde)
- Absents aujourd'hui
- En congé aujourd'hui
- Demandes en attente de validation finale
- Anomalies en attente
- Top départements
- Graphiques de tendances

---

## 7. RAPPORTS AVANCÉS 📈

### Rapports Disponibles

#### Rapport de Présence
- Filtres : date, département, employé
- Statistiques par employé :
  - Total jours période
  - Jours présents
  - Jours absents
  - Taux de présence
  - Heures travaillées

#### Rapport de Congés
- Filtres : année, type congé, statut
- Statistiques par type de congé
- Statistiques par mois
- Export PDF/Excel

#### Rapport d'Anomalies
- Filtres : date, type d'anomalie
- Statistiques par type d'anomalie
- Statistiques par employé
- Consolidation des anomalies

#### API Statistiques Critiques
- Taux de présence global
- Évolution absentéisme
- Heures supplémentaires totales
- Moyenne heures sup par employé
- Congés utilisés
- Système d'alertes automatiques

---

## Notes Importantes

- Les **Managers** ont leurs propres demandes de congés qui passent **directement au RH**, sans pré-validation
- Le **rejet d'une demande** par un Manager nécessite toujours un **motif obligatoire** ✅ **CORRIGÉ**
- Le **RH** a un accès complet à la gestion administrative du système
- L'**Admin** est responsable de la configuration technique et de la sécurité globale du système
- La **Zone Autorisée (Geofencing)** est configurée uniquement par l'Admin (rayon circulaire actuellement)
- **Pointage bloqué** pendant congé approuvé ✅ **CORRIGÉ**
- **Jours fériés exclus** du décompte des congés ✅ **CORRIGÉ**

