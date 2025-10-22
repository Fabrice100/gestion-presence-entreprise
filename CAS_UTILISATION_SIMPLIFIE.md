# 📋 CAS D'UTILISATION - VERSION SIMPLIFIÉE

## Liste épurée des cas d'utilisation essentiels

---

## 📊 **TOTAL : 20 CAS D'UTILISATION**

*Note : Les cas communs (connexion, pointage) sont comptés une seule fois*

---

## 🔴 **ADMINISTRATEUR (6 cas)**

### **CU-01 : Configurer le système**
```
Description : Configurer GPS, horaires, paramètres techniques
Acteur : Administrateur
Fréquence : Initial + 2-3 fois/an
```

### **CU-02 : Gérer les départements**
```
Description : Créer, modifier, supprimer départements
Acteur : Administrateur
Fréquence : 1-2 fois/an
```

### **CU-03 : Accéder Django Admin**
```
Description : Maintenance base de données
Acteur : Administrateur
Fréquence : Selon besoins techniques
```

### **CU-04 : Consulter rapports globaux**
```
Description : Vue d'ensemble système
Acteur : Administrateur
Fréquence : Hebdomadaire
```

### **CU-05 : Exporter données système**
```
Description : Export complet pour audit
Acteur : Administrateur
Fréquence : Mensuel
```

### **CU-06 : Gérer anomalies système**
```
Description : Traiter anomalies techniques
Acteur : Administrateur
Fréquence : Selon détections
```

---

## 🟠 **RH/DG (8 cas)**

### **CU-07 : Gérer les employés**
```
Description : Créer, modifier, désactiver employés
Acteur : RH/DG
Fréquence : 5-10 fois/mois
Détails :
- Création : Génération auto credentials + email
- Modification : Département, manager, rôle
- Désactivation : Départs, suspensions
```

### **CU-08 : Configurer horaires de travail**
```
Description : Modifier horaires et tolérance retard
Acteur : RH/DG
Fréquence : 2-4 fois/an
Utilité : Horaires été, changement règlement
```

### **CU-09 : Valider congés (validation finale)**
```
Description : Approuver/rejeter après validation manager
Acteur : RH/DG
Fréquence : 10-20 fois/mois
Workflow : Manager → RH (2 niveaux)
```

### **CU-10 : Gérer départements et managers**
```
Description : Créer départements, assigner managers
Acteur : RH/DG
Fréquence : 2-3 fois/an
```

### **CU-11 : Générer rapports RH**
```
Description : Rapports présences, congés, anomalies
Acteur : RH/DG
Fréquence : Mensuel
Formats : PDF, Excel
```

### **CU-12 : Analyser statistiques critiques**
```
Description : Taux présence, heures supp, tendances
Acteur : RH/DG
Fréquence : Hebdomadaire
Utilité : Décisions stratégiques
```

### **CU-13 : Exporter données RH**
```
Description : Export employés, présences (Excel/CSV)
Acteur : RH/DG
Fréquence : Mensuel
Utilité : Reporting Direction, audit
```

### **CU-14 : Consulter soldes congés**
```
Description : Voir soldes tous employés
Acteur : RH/DG
Fréquence : Hebdomadaire
Utilité : Planification, conformité
```

---

## 🟡 **MANAGER (4 cas)**

### **CU-15 : Valider congés équipe (1ère validation)**
```
Description : Approuver/rejeter demandes équipe
Acteur : Manager
Fréquence : 5-15 fois/mois
Workflow : Employé → Manager → RH
Critères : Planning équipe, charge travail
```

### **CU-16 : Superviser présences équipe**
```
Description : Consulter qui est présent, taux équipe
Acteur : Manager
Fréquence : Quotidien
Utilité : Gestion opérationnelle
```

### **CU-17 : Générer rapports équipe**
```
Description : Rapports présences/congés équipe
Acteur : Manager
Fréquence : Mensuel
Utilité : Évaluation, reporting
```

### **CU-18 : Valider heures supplémentaires**
```
Description : Approuver heures supp équipe
Acteur : Manager
Fréquence : Mensuel
```

---

## 🟢 **EMPLOYÉ (4 cas)**

### **CU-19 : Pointer sa présence**
```
Description : Pointer entrée et sortie avec GPS
Acteur : Employé
Fréquence : 2 fois/jour (entrée + sortie)
Processus :
1. Autoriser GPS
2. Validation zone (< 200m)
3. Validation horaires
4. Enregistrement
Détection auto : Retards, sorties anticipées
```

### **CU-20 : Demander un congé**
```
Description : Créer demande congé
Acteur : Employé
Fréquence : 2-4 fois/an
Workflow :
1. Employé demande
2. Manager valide
3. RH valide (final)
4. Notifications à chaque étape
```

### **CU-21 : Consulter son historique**
```
Description : Voir présences, congés, solde
Acteur : Employé
Fréquence : Hebdomadaire
Contenu :
- Historique pointages
- Statut demandes congés
- Solde congés restant
- Retards éventuels
```

### **CU-22 : Déclarer heures supplémentaires**
```
Description : Déclarer heures supp effectuées
Acteur : Employé
Fréquence : Mensuel
Workflow : Employé → Manager → Validation
```

---

## 📊 **RÉCAPITULATIF SIMPLIFIÉ**

### **Par module**

```
📍 Pointage : 1 cas (CU-19)
🏖️ Congés : 3 cas (CU-09, CU-15, CU-20)
👥 Gestion employés : 2 cas (CU-07, CU-10)
📊 Rapports : 3 cas (CU-11, CU-17, CU-04)
⚙️ Configuration : 2 cas (CU-01, CU-08)
📈 Statistiques : 2 cas (CU-12, CU-16)
⏰ Heures supp : 2 cas (CU-18, CU-22)
🔧 Maintenance : 2 cas (CU-03, CU-06)
📤 Exports : 2 cas (CU-05, CU-13)
👤 Profil : 1 cas (CU-21)

TOTAL : 20 cas essentiels
```

---

## 🎯 **POUR VOTRE RAPPORT**

### **Diagramme Use Case simplifié**

```
┌──────────────────────────────────────┐
│  SYSTÈME PRESENCEPRO                 │
├──────────────────────────────────────┤
│                                      │
│  🔴 ADMIN                            │
│  • Configurer système                │
│  • Gérer départements                │
│  • Maintenance technique             │
│                                      │
│  🟠 RH/DG                            │
│  • Gérer employés                    │
│  • Valider congés (final)            │
│  • Rapports RH                       │
│  • Exporter données                  │
│                                      │
│  🟡 MANAGER                          │
│  • Valider congés équipe             │
│  • Superviser équipe                 │
│  • Rapports équipe                   │
│                                      │
│  🟢 EMPLOYÉ                          │
│  • Pointer (GPS)                     │
│  • Demander congés                   │
│  • Consulter historique              │
│                                      │
│  📊 COMMUN À TOUS                    │
│  • Se connecter                      │
│  • Changer mot de passe              │
│                                      │
└──────────────────────────────────────┘
```

---

## ✅ **VERSION SIMPLIFIÉE**

```
AVANT : 45 cas (détaillé)
MAINTENANT : 20 cas (regroupé)

Avantage :
✅ Plus clair
✅ Moins verbeux
✅ Essentiel seulement
✅ Parfait pour rapport

Les deux documents disponibles :
📄 CAS_UTILISATION.md → Version détaillée (45)
📄 CAS_UTILISATION_SIMPLIFIE.md → Version épurée (20)

Utilisez la version simplifiée pour votre rapport ! ✅
```

---

Date : 11/10/2025
Projet : PresencePro
Cas d'utilisation : 20 cas essentiels ✅




