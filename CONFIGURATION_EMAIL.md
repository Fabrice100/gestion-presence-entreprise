# 📧 CONFIGURATION EMAIL - PresencePro

## 🎯 Configuration actuelle : Console améliorée (par défaut)

Les emails s'affichent dans le terminal avec un format très visible.

### ✅ Avantages
- Toujours fonctionnel (pas de dépendance)
- Instantané
- Parfait pour démonstration en soutenance

### 📋 Comment démontrer
1. Projetez 2 fenêtres : navigateur + terminal
2. Créez un employé dans le navigateur
3. L'email apparaît immédiatement dans le terminal avec ce format :

```
================================================================================
📧 NOUVEL EMAIL ENVOYÉ
================================================================================
De      : noreply@presencepro.local
À       : nouvel.employe@example.com
Sujet   : Bienvenue - Vos accès au système de gestion de présence
================================================================================

CONTENU (Texte):
--------------------------------------------------------------------------------
Bonjour Pierre ADJOVI,

Votre compte a été créé avec succès !

Voici vos identifiants de connexion :
- ID Employé : EMP010
- Mot de passe temporaire : Xy9@mK2pL5qR

Connectez-vous sur : http://localhost:8000/accounts/login/
--------------------------------------------------------------------------------

================================================================================
✅ Email envoyé avec succès (mode console)
================================================================================
```

---

## 🌐 OPTION 2 : Mailtrap (Interface web)

### Étape 1 : Inscription Mailtrap (5 minutes)

1. Allez sur : https://mailtrap.io/
2. Cliquez sur "Sign Up" (gratuit)
3. Créez un compte avec votre email étudiant
4. Confirmez votre email

### Étape 2 : Récupérer les credentials

1. Connectez-vous à Mailtrap
2. Allez dans "Email Testing" → "Inboxes"
3. Cliquez sur votre inbox (ou créez-en une)
4. Cliquez sur "Show Credentials"
5. Sélectionnez "Django" dans le dropdown
6. Copiez les informations :
   - Host : sandbox.smtp.mailtrap.io
   - Port : 2525
   - Username : (votre username)
   - Password : (votre password)

### Étape 3 : Configuration dans Django

Ouvrez `attendance_system/settings.py` et modifiez :

```python
# Commentez cette ligne :
# EMAIL_BACKEND = 'accounts.email_backend.EnhancedConsoleEmailBackend'

# Décommentez et remplissez ces lignes :
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_PORT = 2525
EMAIL_HOST_USER = 'VOTRE_USERNAME_ICI'  # Collez votre username
EMAIL_HOST_PASSWORD = 'VOTRE_PASSWORD_ICI'  # Collez votre password
EMAIL_USE_TLS = True
```

### Étape 4 : Tester

1. Redémarrez le serveur Django
2. Créez un employé
3. Allez sur Mailtrap.io
4. L'email apparaît dans votre inbox avec le rendu HTML complet

### ✅ Avantages Mailtrap
- Interface web professionnelle
- Voir l'email avec le design HTML
- Pas de risque (pas d'envoi réel)
- Gratuit (jusqu'à 500 emails/mois)

---

## 🎯 RECOMMANDATION POUR LA SOUTENANCE

### Stratégie à 2 niveaux :

**Plan A (principal) : Console améliorée**
- Utilisez par défaut
- Montrez le terminal pendant la démo
- 100% fiable

**Plan B (backup) : Mailtrap**
- Configurez en avance
- Si le jury veut voir l'interface web
- Vous décommentez les lignes et redémarrez

---

## 🚀 PROCHAINES ÉTAPES

1. ✅ **Console améliorée** : Déjà configurée et fonctionnelle
2. ⏸️ **Mailtrap** : À configurer si vous voulez (optionnel)

**Voulez-vous que je vous aide à configurer Mailtrap maintenant ?**

Ou vous préférez **tester d'abord la console améliorée** ?

**Testez maintenant :**
1. Connectez-vous avec EMP009 (RH)
2. Créez un nouvel employé
3. Regardez le terminal → L'email apparaît avec le nouveau format !

**Dites-moi ce que vous voyez !** 📧

