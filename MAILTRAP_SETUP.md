# 📧 CONFIGURATION MAILTRAP - Guide pas à pas

## 🎯 Qu'est-ce que Mailtrap ?

Mailtrap est un service qui capture les emails de test et les affiche dans une interface web professionnelle.
Parfait pour les démonstrations et le développement.

---

## 📋 ÉTAPES D'INSTALLATION (10 minutes)

### Étape 1 : Créer un compte Mailtrap

1. Allez sur : **https://mailtrap.io/**
2. Cliquez sur **"Sign Up"** (en haut à droite)
3. Choisissez **"Sign up with Google"** ou entrez votre email
4. Confirmez votre email (vérifiez votre boîte mail)

### Étape 2 : Créer une Inbox

1. Une fois connecté, vous êtes sur le dashboard
2. Vous voyez déjà une inbox par défaut : **"My Inbox"**
3. Ou créez-en une nouvelle : cliquez sur **"+ Add Inbox"**
4. Nommez-la : **"PresencePro"**

### Étape 3 : Récupérer les credentials

1. Cliquez sur votre inbox **"PresencePro"** (ou "My Inbox")
2. Dans l'onglet **"SMTP Settings"**
3. Dans le dropdown **"Integrations"**, sélectionnez : **"Django"**
4. Vous verrez quelque chose comme :

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_HOST_USER = '1a2b3c4d5e6f7g'  # ← COPIEZ CETTE VALEUR
EMAIL_HOST_PASSWORD = '9z8y7x6w5v4u3t'  # ← COPIEZ CETTE VALEUR
EMAIL_PORT = '2525'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
```

### Étape 4 : Configurer Django

1. Ouvrez : `attendance_system/attendance_system/settings.py`
2. Trouvez la section "Configuration des emails" (ligne ~177)
3. **Commentez** la ligne du backend console :
   ```python
   # EMAIL_BACKEND = 'accounts.email_backend.EnhancedConsoleEmailBackend'
   ```

4. **Décommentez et remplissez** les lignes Mailtrap :
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
   EMAIL_PORT = 2525
   EMAIL_HOST_USER = 'COLLEZ_VOTRE_USERNAME_ICI'
   EMAIL_HOST_PASSWORD = 'COLLEZ_VOTRE_PASSWORD_ICI'
   EMAIL_USE_TLS = True
   ```

### Étape 5 : Redémarrer le serveur

1. Arrêtez le serveur : `Ctrl+C` dans le terminal
2. Relancez : `python manage.py runserver`

### Étape 6 : Tester

1. Connectez-vous avec EMP009 (RH)
2. Créez un nouvel employé
3. Allez sur **Mailtrap.io** dans votre navigateur
4. Cliquez sur votre inbox
5. **L'email apparaît** avec le rendu HTML complet !

---

## 🎓 POUR LA SOUTENANCE

### Stratégie recommandée :

**Avant la soutenance :**
- Configurez Mailtrap en avance
- Testez que ça fonctionne
- Gardez les 2 configurations dans settings.py

**Pendant la soutenance :**

**Scénario 1 : Pas d'internet fiable**
- Utilisez Console (décommentez la ligne console)
- Projetez le terminal
- 100% fiable

**Scénario 2 : Internet OK**
- Utilisez Mailtrap (décommentez les lignes SMTP)
- Projetez Mailtrap.io dans le navigateur
- Plus impressionnant visuellement

**Scénario 3 : Les 2 (optimal)**
- Commencez avec Console (montrez que ça marche)
- Puis passez à Mailtrap (montrez l'interface web)
- Prouve que vous maîtrisez les 2 approches

---

## 🔧 DÉPANNAGE

### Erreur : "Authentication failed"
- Vérifiez username/password (pas d'espaces)
- Vérifiez que vous avez copié depuis Mailtrap

### Erreur : "Connection refused"
- Vérifiez votre connexion internet
- Vérifiez le port : 2525 (pas 25 ou 587)

### Les emails n'apparaissent pas
- Attendez 5-10 secondes
- Rafraîchissez la page Mailtrap
- Vérifiez que le serveur Django tourne

---

## 📞 SUPPORT

- Documentation Mailtrap : https://help.mailtrap.io/
- Support Mailtrap : support@mailtrap.io
- Compte gratuit : 500 emails/mois (largement suffisant)

---

**Bonne chance pour votre soutenance ! 🎓**

