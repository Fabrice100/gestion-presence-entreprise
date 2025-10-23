## Présentation générale

Cette application gère la présence, les congés et des rapports pour une PME. Elle propose des interfaces adaptées aux rôles: Administrateur, RH/DG, Manager et Employé. Les modules principaux: authentification, pointage (présence), congés (workflow de validation), rapports/exports.

## Rôles et périmètres

- **Administrateur**
  - Gère la configuration globale (accès technique, comptes spéciaux).
  - Accède à l’administration Django pour la maintenance des données.

- **RH/DG**
  - Supervise l’ensemble de l’organisation: employés, départements, paramètres d’entreprise.
  - Valide les demandes de congés après le manager (validation finale).
  - Consulte les rapports (présence, congés, anomalies) et effectue des exports PDF/XLSX.

- **Manager (N+1)**
  - Suit son équipe: présences, retards, demandes de congés.
  - Valide ou rejette les demandes de congés de ses collaborateurs.
  - Consulte des rapports ciblés (équipe) et les actions à traiter.

- **Employé**
  - Poinçonne (arrivée/départ) via l’interface.
  - Consulte son historique de présence.
  - Crée des demandes de congés et suit leur statut.

## Authentification et navigation

- Connexion via identifiant (ID employé) et mot de passe.
- Redirection automatique vers le tableau de bord adapté au rôle.
- Barre latérale avec raccourcis: Tableau de bord, Présence (pointer/mes présences), Congés (mes demandes/approbations), Paramètres (profil, entreprise pour RH/DG).

## Module Présence (Pointage)

- **Pointage**
  - L’employé effectue un pointage: coordonnées GPS, horodatage serveur.
  - Le système calcule un **statut** sur l’événement: 
    - **normal** (heure dans la fenêtre), **late** (retard), **early** (départ anticipé), 
    - **outside_zone** (hors périmètre), **low_accuracy** (GPS imprécis), **double_punch** (doublon).
  - La tolérance de retard est paramétrée (ex: `late_tolerance_minutes`).

- **Historique et filtres**
  - Vue "Mes présences" avec filtrage par statut et période.

- **Absence**
  - L’absence n’est pas stockée comme statut d’un pointage: c’est l’absence d’événement sur un jour ouvré. Elle est dérivée côté rapports.

## Module Congés (Workflow)

- **Création** (Employé)
  - Remplit: type de congé, période, motif (+ justificatif si requis).
  - Contrôles automatiques: **solde disponible**, **chevauchement** avec congés existants.
  - Calcul d’une **durée simple** en jours (week-ends/jours fériés non exclus par défaut).

- **Statuts de la demande**
  - `pending` → en attente de manager.
  - `approved_manager` → validée par le manager, en attente RH/DG.
  - `approved_rh` → validée par RH/DG (finale).
  - `rejected_manager`, `rejected_rh` → refusée.
  - `cancelled` → annulée par l’employé avant validation finale.

- **Routage à la création**
  - Employé: statut initial `pending`, le manager assigné reçoit la demande.
  - Manager (qui crée sa propre demande): passe directement en `approved_manager` (RH doit finaliser).
  - RH/DG: auto‑approbation (`approved_rh`).

- **Validation**
  - Manager décide (approuve/rejette). S’il approuve, la demande est **notifiée** aux RH/DG.
  - RH/DG décide (approuve/rejette) en validation finale.
  - Les champs de traçabilité existent: commentaire/décision/date côté manager et RH.

- **Listes d’approbation**
  - Manager: voit les demandes `pending` de ses collaborateurs.
  - RH/DG: voit les demandes `approved_manager` (à valider).

## Rapports et exports

- **Rapports disponibles**
  - Présence: statistiques globales + détail par employé.
  - Congés: volumes par année, filtrage par type/statut.
  - Anomalies: événements atypiques (templates fournis).

- **Exports**
  - **PDF**: présence et congés (formaté, prêt à communiquer).
  - **Excel (XLSX)**: présence et congés (données tabulaires pour exploitation).
  - Données de présence brutes (événements) en XLSX.

## Notifications

- À la soumission: notification au manager (si `pending`).
- Après approbation manager: notification aux RH/DG (file d’attente de validation finale).
- Après décisions: notification à l’employé.

## Sécurité et intégrité

- Authentification standard Django.
- En pointage: distance au site, gestion d’exactitude GPS, prévention des doublons.
- Journalisation des décisions de congés (qui/quand/commentaire).

## Ce que fait chaque rôle (enchaînement type)

- **Employé**
  - Se connecte → voit son tableau de bord.
  - Pointe à l’arrivée et au départ (statuts calculés).
  - Crée une demande de congé → passe en `pending` → suit son statut.

- **Manager**
  - Voit les demandes `pending` de son équipe.
  - Approuve/Rejette (commentaire possible) → si approuvé, la demande passe en `approved_manager` et est transmise aux RH.
  - Suit la présence et les demandes depuis son dashboard.

- **RH/DG**
  - Voit les demandes `approved_manager`.
  - Approuve/Rejette en décision finale (`approved_rh`/`rejected_rh`).
  - Consulte et exporte les rapports; gère les paramètres d’entreprise.

- **Administrateur**
  - Maintenance via l’admin Django.
  - Gestion avancée des modèles et données si besoin.

## Limites actuelles (connues)

- La durée des congés n’exclut pas encore automatiquement week‑ends et fériés.
- L’absence n’est pas matérialisée comme enregistrement journalier (déduite dans les rapports).
- Pas de catégories HS (heures supplémentaires) complexes ni de clôture mensuelle.

## Pistes d’amélioration (légères et utiles)

- Exclure week‑ends/fériés du calcul de `duration_days` (fixtures Togo déjà présentes).
- Règle PME: si durée ≤ 3 jours et type ordinaire, validation manager seule (paramétrable).
- Export paie mensuel simple (XLSX/CSV): heures normales estimées, HS simples, jours congé par type.
- Rappels automatiques si `pending` > 2 jours (manager) ou `approved_manager` > 2 jours (RH).

## Références techniques clés

- Présence: `attendance/models.py`, `attendance/views.py` (statut `normal/late/early/...`).
- Congés: `leave/models.py` (statuts), `leave/workflow_views.py` (routage et décisions), `leave/forms.py`.
- Rapports/Exports: `reports/export_services.py` (PDF/XLSX), `templates/reports/*.html`.
- Tableaux de bord: `templates/dashboard/*` (moderne et classique), layout `base_modern.html`.




