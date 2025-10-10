# 🔔 SYSTÈME DE NOTIFICATIONS - Explications simples

## 📧 QU'EST-CE QU'UNE NOTIFICATION ?

Une notification = **un email automatique** envoyé quand quelque chose d'important se passe.

---

## 📋 LES 5 NOTIFICATIONS AUTOMATIQUES

### 1️⃣ Création d'employé

**Déclencheur :** RH crée un nouvel employé

**Email envoyé à :** Le nouvel employé

**Contenu :** ID employé + Mot de passe temporaire + Lien de connexion

**Exemple :**
```
À : pierre.adjovi@example.com
Sujet : Bienvenue - Vos accès PresencePro

Bonjour Pierre ADJOVI,
Votre compte a été créé !
ID Employé : EMP010
Mot de passe : Xy9@mK2p
```

---

### 2️⃣ Demande de congé créée

**Déclencheur :** Un employé demande un congé

**Email envoyé à :** Son manager (pour validation)

**Contenu :** Détails de la demande + Lien de validation

**Exemple :**
```
À : manager@example.com
Sujet : Nouvelle demande de congé à valider

Pierre ADJOVI a demandé un congé :
- Type : Congés payés
- Période : 15/01/2025 - 20/01/2025
- Durée : 6 jours
```

---

### 3️⃣ Manager approuve

**Déclencheur :** Manager valide la demande

**Emails envoyés à :**
- L'employé (information)
- Le RH (pour validation finale)

**Exemple pour l'employé :**
```
À : pierre.adjovi@example.com
Sujet : Demande de congé approuvée par votre manager

Votre demande a été approuvée par votre manager.
Elle attend maintenant la validation RH.
```

---

### 4️⃣ RH approuve (validation finale)

**Déclencheur :** RH valide définitivement

**Email envoyé à :** L'employé

**Contenu :** Confirmation finale

**Exemple :**
```
À : pierre.adjovi@example.com
Sujet : Demande de congé approuvée

Félicitations ! Votre congé est validé.
Vous pouvez partir du 15/01 au 20/01.
```

---

### 5️⃣ Rejet de demande

**Déclencheur :** Manager ou RH rejette

**Email envoyé à :** L'employé

**Contenu :** Motif du rejet

**Exemple :**
```
À : pierre.adjovi@example.com
Sujet : Demande de congé rejetée

Votre demande a été rejetée.

Motif : "Période trop chargée, choisissez une autre date"
```

---

## 🖥️ OÙ VOIR LES EMAILS ?

### Mode Console (par défaut)

Les emails s'affichent dans le **terminal** où tourne le serveur.

**Format :**
```
================================================================================
📧 NOUVEL EMAIL ENVOYÉ
================================================================================
De      : noreply@presencepro.local
À       : pierre.adjovi@example.com
Sujet   : Bienvenue - Vos accès
================================================================================
[Contenu complet]
================================================================================
✅ Email envoyé avec succès
================================================================================
```

### Mode Mailtrap (optionnel)

Les emails apparaissent sur https://mailtrap.io/ avec le design HTML.

---

## 🎓 POUR LA SOUTENANCE

### Comment démontrer les notifications :

**Étape 1 : Préparez 2 fenêtres**
- Fenêtre 1 : Navigateur (application)
- Fenêtre 2 : Terminal (emails)

**Étape 2 : Scénario de démonstration**

1. **Création employé**
   - Connectez-vous en RH
   - Créez un employé
   - → Terminal affiche l'email de bienvenue

2. **Demande de congé**
   - Connectez-vous en Employé
   - Créez une demande
   - → Terminal affiche l'email au manager

3. **Validation manager**
   - Connectez-vous en Manager
   - Approuvez la demande
   - → Terminal affiche 2 emails (employé + RH)

4. **Validation RH**
   - Connectez-vous en RH
   - Approuvez la demande
   - → Terminal affiche l'email à l'employé

**Total : 5 emails envoyés automatiquement !**

---

## ✅ AVANTAGES DU SYSTÈME

1. ✅ **Automatique** : Aucune action manuelle
2. ✅ **Traçabilité** : Tous les événements sont notifiés
3. ✅ **Communication** : Tout le monde est informé
4. ✅ **Professionnel** : Comme SAP, Workday, etc.

---

**Voilà ! Les notifications sont des emails automatiques. Simple et efficace.** 📧

