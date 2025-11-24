# 🚀 Guide Déploiement Render.com - Étape par Étape

**Objectif :** Déployer ton projet sur Render.com tout en gardant ton environnement local intact.

---

## 📋 Table des Matières

1. [Préparation](#préparation)
2. [Créer le compte Render](#créer-le-compte-render)
3. [Créer la base de données PostgreSQL](#créer-la-base-de-données-postgresql)
4. [Créer le service Web](#créer-le-service-web)
5. [Configurer les variables d'environnement](#configurer-les-variables-denvironnement)
6. [Initialiser la base de données](#initialiser-la-base-de-données)
7. [Tester le déploiement](#tester-le-déploiement)
8. [Faire des modifications après déploiement](#faire-des-modifications-après-déploiement)

---

## ✅ Préparation

### Étape 1 : Vérifier que tout est prêt localement

```bash
# Vérifier que le projet fonctionne localement
python manage.py check

# Vérifier que les migrations sont à jour
python manage.py showmigrations
```

### Étape 2 : Préparer les fichiers pour Render

**✅ Fichiers déjà créés :**
- `Procfile` - Indique à Render comment lancer l'application
- `requirements.txt` - Contient `gunicorn` (serveur WSGI)

**Vérification :**

```bash
# Vérifier que Procfile existe
cat Procfile

# Devrait afficher :
# web: gunicorn attendance_system.wsgi:application --bind 0.0.0.0:$PORT
```

### Étape 3 : Pousser le code sur GitHub

**⚠️ IMPORTANT :** Render déploie depuis GitHub. Tu dois avoir ton code sur GitHub.

```bash
# Vérifier l'état Git
git status

# Si tu as des modifications non commitées, les commiter
git add .
git commit -m "Préparation déploiement Render"

# Pousser sur GitHub (remplacer par ta branche)
git push origin full-project-snapshot
```

**Note :** Si tu n'as pas encore de repository GitHub :
1. Créer un compte sur https://github.com
2. Créer un nouveau repository
3. Suivre les instructions pour pousser ton code

---

## 🌐 Créer le compte Render

### Étape 1 : S'inscrire sur Render

1. Aller sur : **https://render.com**
2. Cliquer sur **"Get Started for Free"**
3. S'inscrire avec :
   - Email
   - OU **"Continue with GitHub"** (recommandé - plus simple)

### Étape 2 : Vérifier le compte

- Tu arrives sur le **Dashboard Render**
- Tu vois **"New +"** en haut à droite

---

## 🗄️ Créer la base de données PostgreSQL

### Étape 1 : Créer la base de données

1. Dans Render, cliquer sur **"New +"** → **"PostgreSQL"**
2. Remplir le formulaire :
   - **Name:** `presencepro-db` (ou un nom de ton choix)
   - **Database:** `presencepro_db` (ou laisser par défaut)
   - **User:** `presencepro_user` (ou laisser par défaut)
   - **Region:** Choisir la région la plus proche (ex: `Oregon (US West)`)
   - **PostgreSQL Version:** Laisser par défaut (15)
   - **Plan:** **Free** (gratuit)
3. Cliquer sur **"Create Database"**

### Étape 2 : Noter les informations de connexion

**⚠️ IMPORTANT :** Copier ces informations, tu en auras besoin !

Une fois la base créée, Render affiche :

- **Internal Database URL** (pour Render)
- **External Database URL** (pour connexion externe)
- **Host:** `dpg-xxxxx-a.oregon-postgres.render.com`
- **Port:** `5432`
- **Database:** `presencepro_db`
- **User:** `presencepro_user`
- **Password:** (affiché une seule fois - le noter !)

**💡 Astuce :** Cliquer sur **"Connect"** pour voir toutes les informations.

---

## 🌍 Créer le service Web

### Étape 1 : Créer le service

1. Dans Render, cliquer sur **"New +"** → **"Web Service"**
2. Connecter ton repository GitHub :
   - Si pas encore connecté, cliquer sur **"Connect GitHub"**
   - Autoriser Render à accéder à tes repositories
   - Sélectionner le repository contenant ton projet
3. Remplir le formulaire :

#### Configuration de base :

- **Name:** `presencepro` (ou un nom de ton choix)
- **Region:** Même région que la base de données
- **Branch:** `full-project-snapshot` (ou ta branche principale)
- **Root Directory:** `attendance_system` ⚠️ **IMPORTANT**
- **Environment:** `Python 3`
- **Build Command:** 
  ```
  pip install -r requirements.txt && python manage.py collectstatic --noinput
  ```
- **Start Command:**
  ```
  gunicorn attendance_system.wsgi:application
  ```

#### Configuration avancée (optionnel) :

- **Instance Type:** `Free` (gratuit)
- **Auto-Deploy:** `Yes` (déploie automatiquement à chaque push)

### Étape 2 : Créer le service

1. Cliquer sur **"Create Web Service"**
2. ⏳ **Attendre 5-10 minutes** (premier déploiement)
3. Tu verras les logs de build en temps réel

---

## ⚙️ Configurer les variables d'environnement

### Étape 1 : Accéder aux variables d'environnement

1. Dans le service web créé, aller dans l'onglet **"Environment"**
2. Cliquer sur **"Add Environment Variable"**

### Étape 2 : Ajouter les variables

Ajouter ces variables **une par une** :

#### Variables Django Core :

```
SECRET_KEY
```
**Valeur :** Générer avec :
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```
DEBUG
```
**Valeur :** `False` (production)

```
ALLOWED_HOSTS
```
**Valeur :** `presencepro.onrender.com` (ou ton URL Render)

```
CSRF_TRUSTED_ORIGINS
```
**Valeur :** `https://presencepro.onrender.com` (ou ton URL Render)

#### Variables Base de Données :

```
DB_NAME
```
**Valeur :** Le nom de la base (ex: `presencepro_db`)

```
DB_USER
```
**Valeur :** L'utilisateur (ex: `presencepro_user`)

```
DB_PASSWORD
```
**Valeur :** Le mot de passe de la base (copié à l'étape précédente)

```
DB_HOST
```
**Valeur :** L'host de la base (ex: `dpg-xxxxx-a.oregon-postgres.render.com`)

```
DB_PORT
```
**Valeur :** `5432`

#### Variables Email (optionnel) :

```
EMAIL_BACKEND
```
**Valeur :** `django.core.mail.backends.console.EmailBackend` (pour commencer)

OU pour Gmail :
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ton-email@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-application
```

#### Variables GPS (optionnel - utiliser les valeurs par défaut) :

```
SITE_CENTER_LAT=6.140766
SITE_CENTER_LNG=1.241907
RADIUS_METERS=200
ACCURACY_MAX_METERS=100
```

### Étape 3 : Sauvegarder

1. Cliquer sur **"Save Changes"**
2. Render redémarre automatiquement le service

---

## 🗃️ Initialiser la base de données

### Étape 1 : Accéder au Shell Render

1. Dans le service web, aller dans l'onglet **"Shell"**
2. Cliquer sur **"Open Shell"**
3. Un terminal s'ouvre

### Étape 2 : Appliquer les migrations

Dans le shell Render :

```bash
# Appliquer les migrations
python manage.py migrate

# Initialiser les données du Togo
python manage.py init_togo_setup

# Créer un superutilisateur
python manage.py createsuperuser

# Suivre les instructions :
# - Username: admin
# - Email: admin@example.com
# - Password: (choisir un mot de passe sécurisé)
```

### Étape 3 : Vérifier

1. Aller sur l'URL de ton site (ex: `https://presencepro.onrender.com`)
2. Tu devrais voir la page de connexion
3. Se connecter avec le compte admin créé

**✅ Félicitations ! Ton site est en ligne !**

---

## 🧪 Tester le déploiement

### Checklist de test :

- [ ] Site accessible sur l'URL Render
- [ ] Page de connexion s'affiche
- [ ] Connexion avec compte admin fonctionne
- [ ] Dashboard s'affiche
- [ ] Pointage GPS fonctionne (si testé)
- [ ] Gestion des utilisateurs fonctionne (RH)
- [ ] Gestion des congés fonctionne

### Si erreur 500 :

1. Aller dans l'onglet **"Logs"** du service web
2. Vérifier les erreurs
3. Vérifier que toutes les variables d'environnement sont correctes
4. Vérifier que les migrations sont appliquées

---

## 🔄 Faire des modifications après déploiement

### Comment ça fonctionne ?

**Render déploie automatiquement depuis GitHub.** Voici le workflow :

```
1. Tu modifies le code LOCALEMENT
   ↓
2. Tu commites les changements (git commit)
   ↓
3. Tu pushes sur GitHub (git push)
   ↓
4. Render détecte automatiquement le changement
   ↓
5. Render redéploie automatiquement (si Auto-Deploy activé)
   ↓
6. Ton site est mis à jour en 5-10 minutes
```

### Exemple concret :

#### Scénario : Tu veux modifier le texte de la page de connexion

**Étape 1 : Modifier localement**

```bash
# 1. Modifier le fichier (ex: templates/accounts/login_ultra_modern.html)
# 2. Tester localement
python manage.py runserver
# 3. Vérifier que ça fonctionne
```

**Étape 2 : Commiter et pousser**

```bash
# Commiter les changements
git add templates/accounts/login_ultra_modern.html
git commit -m "Modifier le texte de connexion"

# Pousser sur GitHub
git push origin full-project-snapshot
```

**Étape 3 : Render déploie automatiquement**

- Render détecte le push
- Lance un nouveau build (visible dans les logs)
- Redéploie le service
- Le site est mis à jour en 5-10 minutes

**Étape 4 : Vérifier**

- Aller sur ton site Render
- Vérifier que les modifications sont présentes

### ⚠️ Important : Garder le local et le cloud séparés

**Ton environnement local reste intact !**

- ✅ Tes modifications locales ne touchent pas Render
- ✅ Les modifications sur Render ne touchent pas ton local
- ✅ Tu peux tester localement avant de pousser
- ✅ Tu peux avoir des configurations différentes (DEBUG=True local, DEBUG=False sur Render)

### Workflow recommandé :

```
1. Développer localement
   ↓
2. Tester localement (python manage.py runserver)
   ↓
3. Si ça fonctionne → Commiter (git commit)
   ↓
4. Pousser sur GitHub (git push)
   ↓
5. Render déploie automatiquement
   ↓
6. Vérifier sur Render
```

### Modifications qui nécessitent des actions manuelles :

#### 1. Modifications de la base de données (migrations)

```bash
# Localement
python manage.py makemigrations
python manage.py migrate

# Pousser sur GitHub
git add .
git commit -m "Nouvelles migrations"
git push origin full-project-snapshot

# Sur Render (via Shell)
# Aller dans Shell Render
python manage.py migrate
```

#### 2. Modifications des variables d'environnement

- Aller dans Render → Service Web → Environment
- Modifier les variables
- Sauvegarder (redémarre automatiquement)

#### 3. Ajout de nouvelles dépendances

```bash
# Localement
pip install nouvelle-dependance
pip freeze > requirements.txt  # Mettre à jour requirements.txt

# Commiter et pousser
git add requirements.txt
git commit -m "Ajouter nouvelle dépendance"
git push origin full-project-snapshot

# Render installera automatiquement lors du prochain déploiement
```

---

## 📊 Résumé : Local vs Render

| Aspect | Local | Render |
|--------|-------|--------|
| **Code** | Sur ton ordinateur | Sur GitHub |
| **Base de données** | PostgreSQL local | PostgreSQL Render |
| **Configuration** | Fichier `.env` | Variables d'environnement Render |
| **Modifications** | Immédiates | Après `git push` (5-10 min) |
| **DEBUG** | `True` | `False` |
| **URL** | `http://127.0.0.1:8000` | `https://presencepro.onrender.com` |
| **Accès** | Seulement toi | Accessible partout |

---

## 🆘 Dépannage

### Erreur : "Build failed"

**Solution :**
1. Vérifier les logs dans Render
2. Vérifier que `requirements.txt` contient toutes les dépendances
3. Vérifier que `Procfile` existe et est correct

### Erreur : "Application error"

**Solution :**
1. Vérifier les logs dans Render
2. Vérifier les variables d'environnement
3. Vérifier que les migrations sont appliquées
4. Vérifier que `DEBUG=False` en production

### Erreur : "Database connection failed"

**Solution :**
1. Vérifier les variables `DB_*` dans Render
2. Vérifier que la base de données PostgreSQL est créée
3. Vérifier que les migrations sont appliquées

### Le site ne se met pas à jour

**Solution :**
1. Vérifier que tu as bien fait `git push`
2. Vérifier que "Auto-Deploy" est activé dans Render
3. Vérifier les logs pour voir si le déploiement est en cours

---

## ✅ Checklist finale

### Avant le déploiement :
- [ ] Code testé localement
- [ ] `Procfile` créé
- [ ] `gunicorn` dans `requirements.txt`
- [ ] Code poussé sur GitHub

### Déploiement :
- [ ] Compte Render créé
- [ ] Base de données PostgreSQL créée
- [ ] Service Web créé
- [ ] Variables d'environnement configurées
- [ ] Migrations appliquées (via Shell)
- [ ] Superutilisateur créé

### Après déploiement :
- [ ] Site accessible
- [ ] Connexion fonctionne
- [ ] Fonctionnalités testées
- [ ] Logs vérifiés

---

## 🎯 Résumé : Réponses à tes questions

### 1. Comment garder l'état local intact ?

✅ **C'est automatique !** 
- Ton code local reste sur ton ordinateur
- Render utilise une copie depuis GitHub
- Les deux sont complètement séparés

### 2. Peux-tu faire des modifications après déploiement ?

✅ **Oui, absolument !**
- Modifier localement
- Tester localement
- Commiter et pousser sur GitHub
- Render déploie automatiquement

### 3. Comment les modifications sont mises à jour ?

✅ **Automatiquement via GitHub :**
1. Tu modifies localement
2. Tu commites (`git commit`)
3. Tu pushes (`git push`)
4. Render détecte et redéploie (5-10 min)
5. Le site est mis à jour

---

**Ton projet local reste intact, et tu peux déployer sur Render sans risque ! 🚀**

