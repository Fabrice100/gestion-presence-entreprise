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

## Récapitulatif des Fonctionnalités Clés

| Module | Fonctionnalité | Règle Métier |
|--------|---------------|--------------|
| **Pointage** | Validation Géospatiale | PostGIS + ZoneAutorisee |
| **Pointage** | Calcul Temps | Plafonnage + pause fixe |
| **Pointage** | Anomalies | Détection hors zone + retards |
| **Congés** | Décompte | Exclusion jours fériés |
| **Congés** | Types | Déduction selon type |
| **Congés** | Workflow | Motif de rejet obligatoire |
| **Congés** | Statut | Blocage pointage si APPROUVÉ |
| **Admin** | Création compte | Email + changement MDP obligatoire |
| **Admin** | Hiérarchie | Service + Manager |
| **Admin** | Rapports | Paie + Anomalies + Solde |

---

## Notes Techniques

- **PostGIS** : Validation géographique des pointages
- **ZoneAutorisee** : Polygones géographiques configurés par Admin
- **Geofencing** : Système de restriction géographique
- **Motif de rejet** : Champ obligatoire dans le workflow de validation
- **Statut APPROUVÉ** : Blocage automatique du pointage pendant congés

