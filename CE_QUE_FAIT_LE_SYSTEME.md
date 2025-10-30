# 🎯 CE QUE FAIT LE SYSTÈME - Explication Concrète

## 1️⃣ QUE FAIT LE SYSTÈME CONCRÈTEMENT ?

### 📱 Système de Gestion de Présence et Congés pour Entreprise

Le système permet de :
- **Pointer l'arrivée et le départ** des employés avec GPS
- **Demander et valider les congés** avec workflow hiérarchique
- **Générer des rapports** de présence et congés
- **Détecter automatiquement les anomalies** (retards, sorties oubliées, etc.)
- **Calculer les heures travaillées et heures supplémentaires**

---

## 🏢 STRUCTURE DU SYSTÈME

```
SYSTÈME DE GESTION DE PRÉSENCE
│
├── 📍 POINTAGE GPS
│   └── Les employés pointent leur arrivée/départ via le navigateur
│
├── 🏖️ GESTION DES CONGÉS
│   └── Workflow : Employé → Manager → RH/DG
│
├── 📊 RAPPORTS
│   └── Présence, congés, anomalies (exports PDF/Excel)
│
└── 🚨 ANOMALIES
    └── Détection automatique et gestion
```

---

## 👥 ACTEURS DU SYSTÈME

Il y a **4 types d'acteurs** :

| Acteur | Nom | Peut Pointer | Rôle Principal |
|--------|-----|--------------|----------------|
| 🔵 **Employé** | `employee` | ✅ Oui | Pointer, demander congés |
| 🟢 **Manager** | `manager` | ✅ Oui | Valider congés équipe, suivre présences |
| 🟡 **RH/DG** | `rh_dg` | ❌ Non | Validation finale, gestion globale |
| 🔴 **Admin** | `admin` | ❌ Non | Configuration technique |

---

## 2️⃣ QUE FAIT CHAQUE ACTEUR CONCRÈTEMENT ?

---

## 🔵 1. L'EMPLOYÉ (employee)

### Ce qu'il peut faire concrètement :

#### A. POINTER SA PRÉSENCE 📍
```
Chaque jour, l'employé :
1. Ouvre son navigateur → Va sur le site
2. Clique sur "Pointer"
3. Le GPS se déclenche (géolocalisation)
4. Le système vérifie :
   ✅ Il est bien au bureau (distance < 200m)
   ✅ La précision GPS est bonne (< 200m)
5. Le système enregistre l'heure d'arrivée

Le soir, il fait pareil pour pointer la sortie.
```

**Résultat concret :**
- Heure d'arrivée enregistrée (ex: 08h15)
- Heure de sortie enregistrée (ex: 17h30)
- Heures travaillées calculées automatiquement (9h15)
- Si retard > 15min → Anomalie "retard" détectée

#### B. DEMANDER DES CONGÉS 🏖️
```
Quand l'employé veut prendre des vacances :
1. Va dans "Mes Congés"
2. Remplit le formulaire :
   - Type de congé (Congés payés, Maladie, etc.)
   - Date début et fin
   - Motif
3. Clique sur "Soumettre"

Le système vérifie :
   ✅ Il a assez de jours disponibles
   ✅ Pas de chevauchement avec autres demandes
   ✅ Les jours fériés sont exclus automatiquement

Ensuite :
   → La demande part au Manager
   → Après validation Manager → Part au RH
   → Le RH valide définitivement → Les jours sont déduits du solde
```

**Résultat concret :**
- Demande créée avec statut "En attente"
- Notification envoyée au Manager
- Si approuvée par RH → Les jours sont déduits automatiquement
- L'employé voit son solde mis à jour (ex: 25j → 23j)

#### C. CONSULTER SES DONNÉES 👀
```
L'employé peut consulter :
- Son historique de pointages (liste avec dates/heures)
- Son solde de congés par type (25j congés payés, 5j maladie, etc.)
- L'état de ses demandes de congés
- Ses anomalies (retards, oubli de pointage, etc.)
- Son dashboard avec statistiques personnelles
```

**Exemple Dashboard Employé :**
```
📊 Mes Statistiques
- Présence ce mois : 22/22 jours ✅
- Total heures : 176h
- Congés restants : 12 jours
- Demandes en cours : 1
- Anomalies non résolues : 0
```

---

## 🟢 2. LE MANAGER (manager)

### Ce qu'il peut faire concrètement :

#### A. POINTER SA PRÉSENCE 📍
```
Comme un employé normal
(Arrivée, sortie, horaires suivis)
```

#### B. VALIDER LES CONGÉS DE SON ÉQUIPE ✅
```
Quand un employé de son équipe demande congé :
1. Le Manager reçoit une notification
2. Va dans "Validations Congés"
3. Voit la liste des demandes en attente de son équipe
4. Pour chaque demande, il peut :
   ✅ Approuver → La demande passe au RH
   ❌ Rejeter → DOIT donner un motif obligatoire
```

**Exemple concret :**
```
Demande de Jean (son équipe) :
- 5 jours de congés du 15 au 20 Mars
- Type : Congés payés
- Solde disponible : 10 jours ✅

Manager décide :
✅ Approuver → Motif : "Ok, période calme"
   → Statut devient "Approuvé Manager" → Envoi au RH

❌ Rejeter → Motif obligatoire : "Rush projet, période non adaptée"
   → Statut devient "Rejeté Manager" → Notification à Jean
```

#### C. SUIVRE L'ÉQUIPE 👥
```
Le Manager peut voir :
- Les pointages de son équipe (qui a pointé aujourd'hui)
- Les présences/absences
- Les retards et anomalies de son équipe
- Le calendrier d'absences (qui est en congé)
```

**Exemple Dashboard Manager :**
```
📊 Mon Équipe (8 personnes)
- Pointages aujourd'hui : 7/8 ✅
- Absent : Marie (congé approuvé)
- Retards aujourd'hui : 0
- Demandes en attente : 3
- Anomalies non résolues : 2
```

#### D. GÉRER LES ANOMALIES DE L'ÉQUIPE 🔧
```
Si une anomalie est détectée pour un membre de son équipe :
1. Manager reçoit notification
2. Peut :
   ✅ Justifier l'anomalie (ex: "Exceptionnel, ok avec moi")
   ❌ L'ignorer (anomalie mineure)
   → Résoudre avec commentaire
```

---

## 🟡 3. RH/DIRECTION GÉNÉRALE (rh_dg)

### Ce qu'il peut faire concrètement :

#### A. VALIDATION FINALE DES CONGÉS 🎯
```
Après validation Manager, la demande arrive au RH :

1. RH examine la demande
2. Peut :
   ✅ Approuver définitivement
      → Les jours sont déduits du solde automatiquement
      → Notification à l'employé
   
   ❌ Rejeter (même si approuvé par Manager)
      → DOIT donner motif obligatoire
      → Notification à l'employé et Manager
```

**Exemple concret :**
```
Demande de Paul :
- 10 jours en Juillet
- Approuvé par Manager ✅
- Arrivé au RH

RH décide :
✅ Approuver → "Congé accordé, bonne vacances!"
   → 10 jours déduits de son solde
   → Statut "Approuvé RH"

❌ Rejeter → "Pic d'activité prévu en Juillet, reportez à Août"
   → Demande annulée
   → Pas de déduction des jours
```

#### B. CRÉER/GÉRER LES EMPLOYÉS 👥
```
Le RH peut créer de nouveaux employés :

1. Formulaire "Nouvel Employé"
2. Remplit : Nom, Prénom, Email, Rôle, Département, Manager
3. Clique "Créer"

Le système :
✅ Génère un ID unique (ex: EMP123)
✅ Génère un mot de passe temporaire aléatoire
✅ Envoie email avec credentials
✅ Force changement mot de passe à la 1ère connexion
```

**Résultat concret :**
```
Nouvel employé créé :
- ID : EMP456
- Login : EMP456
- MDP temporaire : 8 caractères aléatoires
- Email envoyé avec instructions
- À la 1ère connexion : obligé de changer le mdp
```

#### C. VOIR LES RAPPORTS GLOBAUX 📊
```
Le RH peut consulter et exporter :
- Rapport de présence (tous employés)
- Rapport de congés (par départements)
- Rapport d'anomalies
- Statistiques globales

Formats d'export : PDF, Excel, CSV
```

**Exemple Presents Aujourd'hui :**
```
📊 Présence Globale
- Total employés : 50
- Présents : 42
- Absents : 8
  ├── Congés approuvés : 5
  ├── Maladie : 2
  └── Absences non justifiées : 1 ⚠️
```

#### D. GÉRER LES ANOMALIES GLOBALES 🚨
```
Le RH peut voir et gérer TOUTES les anomalies de l'entreprise :
- Retards
- Sorties oubliées
- Pointages hors zone
- etc.

Peut les justifier, résoudre, ou contacter les managers.
```

---

## 🔴 4. ADMINISTRATEUR (admin)

### Ce qu'il peut faire concrètement :

#### A. ACCÈS ADMIN DJANGO 🔧
```
L'admin a accès à l'interface d'administration Django :
/admin/

Peut :
- Voir/modifier toutes les données
- Configurer les types de congés
- Ajouter des jours fériés
- Gérer les départements
- Voir les logs système
- etc.
```

#### B. CONFIGURER LE SYSTÈME ⚙️
```
Accès exclusif à la configuration GPS :

1. Centrer le GPS sur le bureau (lat/lng)
2. Définir le rayon autorisé (ex: 200m)
3. Définir la précision GPS max (ex: 200m)
4. Configurer les horaires de travail
5. Configurer les jours fériés de l'année
```

**Exemple Configuration GPS :**
```
📍 Coordonnées Bureau
- Latitude : 6.123456
- Longitude : 1.234567
- Rayon autorisé : 200 mètres
- Précision GPS max : 100 mètres

Si un employé est à 250m du bureau → Pointage refusé ❌
Si précision GPS > 200m → Pointage refusé ❌
```

---

## 🔄 EXEMPLE DE WORKFLOW COMPLET

### Scénario : Marie demande 3 jours de congé

```
┌─────────────────────────────────────────────────┐
│ JOUR 1 - 10h00                                  │
│ Marie (Employé) soumet demande                  │
│ Type: Congés payés                              │
│ Période: 15 au 17 Mars                          │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ JOUR 1 - 10h15                                  │
│ Le Manager (Pierre) est notifié                 │
│ Va dans "Validations"                           │
│ Voit la demande de Marie                        │
│ Vérifie : OK, période calme                     │
│ ✅ Approuve → Statut: "Approuvé Manager"        │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ JOUR 1 - 10h30                                  │
│ Le RH (Sophie) est notifié                      │
│ Va dans "Validations Congés"                    │
│ Voit la demande approuvée par Pierre            │
│ Vérifie : OK, pas de conflit                    │
│ ✅ Approuve définitivement                       │
│    → Statut: "Approuvé RH"                      │
│    → 3 jours déduits du solde de Marie          │
│    → Marie reçoit notification "Congé accordé!" │
└─────────────────────────────────────────────────┘

Résultat :
- Marie peut prendre ses 3 jours de congé
- Les jours sont déduits automatiquement
- Le calendrier est mis à jour
- Tous ont reçu les notifications
```

---

## 📊 CE QUE CALCULE LE SYSTÈME AUTOMATIQUEMENT

### 1. Heures Travaillées 🕐
```
Pointage : 08h15 → 17h30
Système calcule :
  17h30 - 08h15 = 9h15
  Pause déduite : 1h
  Total : 8h15 de travail effectif ✅
```

### 2. Jours de Congé 🏖️
```
Demande : 15 Mars au 20 Mars (6 jours calendaires)
Système calcule :
  - Weekends exclus : -2 jours (Samedi 18, Dimanche 19)
  - Jours fériés exclus : -0 jours
  = 4 jours ouvrables déduits du solde ✅
```

### 3. Anomalies 🚨
```
Retard : Arrivée à 08h20 (au lieu de 08h00)
Système détecte :
  - Tolérance : 15 minutes
  - Retard : 20 minutes
  → Anomalie "retard" créée automatiquement ⚠️
```

### 4. Heures Supplémentaires ⏰
```
Pointage : 08h00 → 20h00 (12h)
Système calcule :
  - Heures normales : 8h
  - Heures sup : 4h
  → Détecte automatiquement heures sup 📊
```

---

## 🎯 RÉSUMÉ EN 3 POINTS

### 1. Le système est un **registre électronique de présence**
   - Enregistre qui arrive/part et quand
   - Vérifie qu'ils sont bien au bureau (GPS)
   - Calcule heures travaillées automatiquement

### 2. Le système est un **workflow de validation de congés**
   - Employé demande → Manager approuve → RH valide
   - Déduit automatiquement les jours du solde
   - Exclut weekends et jours fériés

### 3. Le système est un **outil de reporting**
   - Rapports de présence par équipe/département
   - Export PDF/Excel pour injections dans paie
   - Détection automatique d'anomalies

---

## 📞 UTILISATION QUOTIDIENNE

### Le matin (8h00)
- Tout le monde pointe son arrivée
- Le système vérifie GPS et précision
- Les heures sont enregistrées

### Pendant la journée
- Les managers gèrent les demandes de congés
- Le RH fait la validation finale
- Le système calcule et met à jour les soldes

### Le soir (17h00)
- Tout le monde pointe sa sortie
- Le système calcule les heures travaillées
- Détecte anomalies (oubli de pointage, etc.)

### En fin de mois
- Le RH exporte les rapports
- Injection dans le système de paie
- Analyse des anomalies et retards

---

**Document créé le:** 26 janvier 2025  
**Version:** 1.0  
**Objectif:** Explication concrète du système



