# Modules du Système de Gestion de Présence

Ce document détaille les trois principaux modules du système et leurs règles métier associées.

---

## 📍 1. Module de Gestion du Temps et de la Présence (Pointage)

### Logique de Calcul / Règle Métier

#### ✅ Validation Géospatiale

**Description :** Le système enregistre l'heure uniquement si le pointage est validé par **PostGIS** comme étant dans la **ZoneAutorisee**.

**Technologie clé :** PostGIS pour la validation géographique

**Impact :** Sécurisation des données de présence par géolocalisation

---

#### ⏰ Calcul du Temps Effectif (Plafonné)

**Description :** Le temps payable est calculé en **plafonnant** les heures enregistrées aux heures contractuelles et en déduisant la **pause fixe**.

**Exemples :**
- Ignorer le pointage avant 8h ou après 18h
- Déduire la pause fixe de la durée travaillée
- Respecter les heures contractuelles de l'employé

**Termes clés :**
- **Plafonnat** : Limite les heures payables aux heures contractuelles
- **Pause fixe** : Temps de pause déductible du temps de travail

---

#### 📊 Rapport d'Anomalies

**Description :** Identification des pointages **hors zone** (échec Geofencing) et des **retards significatifs** par rapport à l'heure de début contractuelle.

**Types d'anomalies détectées :**
- Pointages **hors zone** : Échec de validation géospatiale (Geofencing)
- **Retards significatifs** : Retard par rapport à l'heure contractuelle de début

**Utilité :** 
- Traçabilité des incidents
- Analyse des patterns d'absence
- Conformité et audit

---

## 📅 2. Module de Gestion des Congés (Workflow et Conformité)

### Logique de Déduction / Règle Métier

#### 📋 Décompte Conforme

**Description :** Le nombre de jours **déduit du solde annuel est calculé en excluant les jours fériés** qui tombent dans la période demandée (conformité légale).

**Caractéristiques :**
- Conformité légale respectée
- Exclusion automatique des jours fériés
- Calcul précis du solde restant

**Exemple :** 
Si un employé demande 5 jours de congés incluant 1 jour férié, seulement 4 jours seront déduits de son solde annuel.

---

#### 🏷️ Types de Congés

**Description :** Différenciation du Congé Annuel Payé (déduit du solde) des Congés Exceptionnels/Maladie (ne déduisent pas du solde).

**Types de congés :**

| Type | Déduction du Solde | Description |
|------|-------------------|-------------|
| **Congé Annuel Payé** | ✅ Oui | Déduit du solde annuel |
| **Congés Exceptionnels** | ❌ Non | Congés spéciaux non déductibles |
| **Congés Maladie** | ❌ Non | Congés maladie non déductibles |

---

#### 🔄 Workflow avec Motif de Rejet

**Description :** Le Manager ou le RH **doit fournir un** `motif_rejet` pour toute demande rejetée, assurant transparence et traçabilité.

**Caractéristiques :**
- **Obligatoire** : Le motif de rejet est requis
- **Transparence** : Communication claire du motif
- **Traçabilité** : Historique des rejets conservé
- **Champ technique :** `motif_rejet`

**Workflow :**
```
Demande → Pré-validation Manager → ✅ Approuvé → Validation RH
                              ↓
                           ❌ Rejeté (avec motif obligatoire)
```

---

#### 👤 Statut Utilisateur

**Description :** Le pointage est **bloqué** pour l'employé pendant la période de congé `APPROUVÉ`.

**Règles d'application :**
- Blocage automatique du pointage
- Statut : `APPROUVÉ`
- Protection contre les double-comptes
- Sécurité des données de présence

**Impact :** Empêche tout pointage pendant la période de congé approuvé

---

## 🔒 3. Module d'Administration et Sécurité

### Logique de Sécurité / Administration

#### 🔐 Création de Compte Sécurisée

**Description :** Le système envoie l'ID et le MDP temporaire par e-mail, forçant l'utilisateur à **changer de mot de passe à la première connexion**.

**Processus de création :**
1. Création du compte par RH ou Admin
2. Envoi automatique de l'ID et mot de passe temporaire par email
3. **Obligation de changement** du mot de passe à la première connexion
4. Accès complet uniquement après authentification sécurisée

**Avantages :**
- Sécurité renforcée
- Contrôle d'accès initial
- Traçabilité des authentifications

---

#### 👥 Gestion Hiérarchique

**Description :** Le RH crée les utilisateurs et les associe à leur **Service** ; le Manager est lié à ce service pour l'autorité de validation de l'équipe.

**Structure :**
```
RH
  ├── Crée les utilisateurs
  ├── Associe à leur Service
  └── Nomme les Managers

Manager
  ├── Lié à un Service spécifique
  └── Autorité de validation de l'équipe
```

**Responsabilités :**
- **RH** : Création et organisation des utilisateurs
- **Service** : Unité organisationnelle de rattachement
- **Manager** : Supervision et validation hiérarchique

---

#### 📈 Rapports RH

**Description :** Génération des rapports Paie, Anomalies, et Solde de Congés, essentiels pour la gestion et l'audit.

**Types de rapports disponibles :**

1. **Rapport Paie**
   - Calcul des heures travaillées
   - Temps payable vs temps réel
   - Primes et heures supplémentaires

2. **Rapport d'Anomalies**
   - Pointages hors zone
   - Retards significatifs
   - Incidents de présence

3. **Rapport de Solde de Congés**
   - Solde annuel par employé
   - Congés pris vs restants
   - Historique des demandes

**Utilité :**
- Gestion administrative
- Audit et conformité
- Prise de décision RH

---

---

## 🕐 4. Module Heures Supplémentaires (Détection Automatique)

### Vue d'Ensemble

Le système **calcule automatiquement** les heures supplémentaires à partir des pointages et gère un workflow de validation complet.

### Fonctionnalités Principales

#### Calcul Automatique par Type

1. **Heures Supplémentaires Quotidiennes**
   - Dépassement de la limite quotidienne (8h par défaut)
   - Calcul automatique après pointage de sortie
   - Création d'enregistrement `OvertimeRecord`

2. **Heures Supplémentaires Hebdomadaires**
   - Dépassement de 40h/semaine
   - Calcul par période de 7 jours

3. **Heures Supplémentaires Weekend**
   - Détection si pointage samedi/dimanche
   - Classification automatique

4. **Heures Supplémentaires Jours Fériés**
   - Détection si pointage jour férié
   - Bonus spécifique selon configuration

5. **Heures Supplémentaires de Nuit**
   - Pointage entre 22h-6h
   - Prime de nuit calculée

#### Workflow de Validation

```python
# Automatique : Signal post_save sur Attendance
@receiver(post_save, sender=Attendance)
def calculate_overtime_on_attendance_change(sender, instance, created, **kwargs):
    # Détection et création automatiques des heures supplémentaires
```

**Validation :**
- Détection automatique → Manager → RH
- Motif obligatoire pour rejet
- Traçabilité complète

---

## 🚨 5. Détection Automatique des Anomalies (Complet)

### Types d'Anomalies Détectées

1. **Pointages Hors Zone** (`outside_zone`)
   - Distance > rayon autorisé
   - Échec Geofencing

2. **Retards Significatifs** (`late_arrival`)
   - Heure d'entrée > heure attendue + tolérance
   - Détection selon horaires configurés

3. **Départs Anticipés** (`early_departure`)
   - Heure de sortie < heure normale
   - Détection automatique

4. **Oubli de Sortie** (`missing_punch_out`)
   - Entrée sans sortie
   - Détection via commande quotidienne
   - `worked_hours = NULL`

5. **Oubli d'Entrée** (`missing_punch_in`)
   - Sortie sans entrée correspondante

6. **Double Pointage** (`double_punch`)
   - Tentative de pointer deux fois même type même jour

7. **Précision GPS Faible** (`low_accuracy`)
   - Précision > seuil configuré

8. **Durée Excessive** (`long_duration`)
   - Session de travail > durée normale

### Workflow de Résolution

```
Anomalie Détectée → Statut 'pending'
    ↓
Notification Manager
    ↓
Justification/Résolution → 'resolved' ou 'justified'
    ↓
Traçabilité complète
```

---

## 📊 6. Rapports et Statistiques Avancées

### Rapports Générés

#### Rapport de Présence
- Statistiques par employé :
  - Total jours
  - Jours présents
  - Taux de présence
  - Heures travaillées

#### Rapport de Congés
- Par type de congé
- Par mois
- Export PDF/Excel

#### Rapport d'Anomalies
- Consolidation par type
- Statistiques par employé
- Tendance temporelle

### API Statistiques Critiques

**Métriques calculées :**
- Taux de présence global
- Évolution absentéisme (6 mois)
- Heures supplémentaires totales
- Moyenne heures sup par employé
- Congés utilisés
- Alertes automatiques

---

## Récapitulatif des Fonctionnalités Clés

| Module | Fonctionnalité | Règle Métier | Statut |
|--------|---------------|--------------|--------|
| **Pointage** | Validation Géospatiale | Haversine + ZoneAutorisee | ✅ |
| **Pointage** | Calcul Temps | Plafonnage 8h + pause 1h | ✅ |
| **Pointage** | Anomalies | 8 types détectés auto | ✅ |
| **Pointage** | Blocage congé | ❌ Impossible si congé | ✅ **CORRIGÉ** |
| **Congés** | Décompte | Exclusion jours fériés | ✅ **CORRIGÉ** |
| **Congés** | Types | Déduction selon type | ✅ |
| **Congés** | Workflow | Motif rejet obligatoire | ✅ **CORRIGÉ** |
| **Congés** | Statut | Blocage pointage si APPROUVÉ | ✅ **CORRIGÉ** |
| **Heures Sup** | Détection auto | 5 types calculés | ✅ |
| **Heures Sup** | Validation | Manager → RH | ✅ |
| **Anomalies** | Résolution | Workflow complet | ✅ |
| **Admin** | Création compte | Email + force MDP | ✅ |
| **Admin** | Hiérarchie | Département + Manager | ✅ |
| **Admin** | Rapports | PDF + Excel + API | ✅ |
| **Dashboard** | Personnel | Stats + historiques | ✅ |
| **Dashboard** | Manager | Supervision équipe | ✅ |
| **Dashboard** | RH | Vue globale entreprise | ✅ |

---

## Notes Techniques

- **Haversine** : Formule de calcul de distance GPS (implémentation Python)
- **ZoneAutorisee** : Rayon circulaire configuré par Admin (pas polygones PostGIS)
- **Geofencing** : Validation de zone par rayon en mètres
- **Motif de rejet** : Validation formulaire obligatoire ✅ **CORRIGÉ**
- **Statut APPROUVÉ** : Vérification congé avant pointage ✅ **CORRIGÉ**
- **Exclusion fériés** : Utilisation `HolidayService.get_working_days_in_period()` ✅ **CORRIGÉ**
- **Signaux Django** : Calcul automatique heures supplémentaires via signals
- **Commandes Management** : Détection quotidienne des oublis de sortie
- **API REST** : Statistiques critiques exposées en JSON
- **Exports** : Génération PDF/Excel pour rapports

