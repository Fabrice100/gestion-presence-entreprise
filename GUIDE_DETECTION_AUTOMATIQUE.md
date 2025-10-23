# Guide d'installation - Détection automatique des oublis de pointage

## 📋 Vue d'ensemble

Cette commande Django détecte automatiquement les employés qui ont oublié de pointer leur sortie et crée des anomalies pour correction par les managers.

## 🚀 Utilisation manuelle

### Commande de base
```bash
python manage.py detect_missing_punches
```

### Options disponibles

#### Vérifier une date spécifique
```bash
python manage.py detect_missing_punches --date 2025-10-22
```

#### Vérifier les 7 derniers jours
```bash
python manage.py detect_missing_punches --days 7
```

#### Avec notifications aux managers
```bash
python manage.py detect_missing_punches --notify
```

#### Mode verbose (détails complets)
```bash
python manage.py detect_missing_punches --verbose
```

#### Combinaison d'options
```bash
python manage.py detect_missing_punches --days 3 --notify --verbose
```

## ⏰ Configuration automatique (Windows Task Scheduler)

### Étape 1 : Ouvrir le Planificateur de tâches
1. Appuyez sur `Windows + R`
2. Tapez `taskschd.msc`
3. Appuyez sur `Entrée`

### Étape 2 : Créer une nouvelle tâche
1. Cliquez sur **"Créer une tâche..."** (panneau de droite)
2. Ne pas utiliser "Créer une tâche de base" (moins d'options)

### Étape 3 : Onglet "Général"
- **Nom** : `Détection oublis de pointage`
- **Description** : `Détecte automatiquement les oublis de sortie chaque jour à 1h du matin`
- **Compte d'utilisateur** : Sélectionnez votre compte Windows
- **Cochez** : "Exécuter même si l'utilisateur n'est pas connecté"
- **Cochez** : "Exécuter avec les autorisations maximales"
- **Configuration pour** : Windows 10

### Étape 4 : Onglet "Déclencheurs"
1. Cliquez sur **"Nouveau..."**
2. **Commencer la tâche** : "Selon une planification"
3. **Paramètres** : 
   - Type : Quotidien
   - Démarrer le : Date actuelle
   - À : `01:00:00` (1h du matin)
   - Répéter tous les : 1 jours
4. **Cochez** : "Activé"
5. Cliquez sur **OK**

### Étape 5 : Onglet "Actions"
1. Cliquez sur **"Nouveau..."**
2. **Action** : "Démarrer un programme"
3. **Programme/script** : 
   ```
   C:\Users\HUSUNUKPE Fabrice\Desktop\mon_projet\attendance_system\run_detect_missing_punches.bat
   ```
   OU (si vous préférez appeler Python directement) :
   ```
   python
   ```
4. **Arguments** (si vous utilisez python directement) :
   ```
   manage.py detect_missing_punches --notify
   ```
5. **Commencer dans** (optionnel) :
   ```
   C:\Users\HUSUNUKPE Fabrice\Desktop\mon_projet\attendance_system
   ```
6. Cliquez sur **OK**

### Étape 6 : Onglet "Conditions"
- **Décochez** : "Démarrer la tâche uniquement si l'ordinateur est alimenté sur secteur"
- **Décochez** : "Arrêter si l'ordinateur bascule sur l'alimentation par batterie"
- **Cochez** : "Sortir l'ordinateur du mode veille pour exécuter cette tâche"

### Étape 7 : Onglet "Paramètres"
- **Cochez** : "Autoriser l'exécution de la tâche à la demande"
- **Cochez** : "Exécuter la tâche dès que possible si un démarrage planifié est manqué"
- **Si la tâche échoue** : "Redémarrer toutes les 1 minutes"
- **Tentatives de redémarrage** : 3

### Étape 8 : Finaliser
1. Cliquez sur **OK**
2. Entrez votre mot de passe Windows si demandé
3. La tâche apparaît dans la liste

### Étape 9 : Tester la tâche
1. Cliquez droit sur la tâche
2. Sélectionnez **"Exécuter"**
3. Vérifiez les résultats dans :
   ```
   C:\Users\HUSUNUKPE Fabrice\Desktop\mon_projet\attendance_system\logs\
   ```

## 📁 Fichiers de logs

Les logs sont automatiquement créés dans le dossier `logs/` avec le format :
```
detect_missing_punches_YYYYMMDD.log
```

Exemple :
```
logs/detect_missing_punches_20251023.log
```

## 🔍 Vérification du fonctionnement

### Vérifier la dernière exécution
1. Ouvrir le Planificateur de tâches
2. Trouver la tâche "Détection oublis de pointage"
3. Onglet **"Historique"** (en bas)
4. Vérifier les événements récents

### Vérifier les logs
```bash
# Voir le dernier log
type logs\detect_missing_punches_20251023.log

# Voir tous les logs
dir logs\detect_missing_punches_*.log
```

## 🐛 Dépannage

### La tâche ne s'exécute pas
1. Vérifier que l'ordinateur est allumé à 1h du matin
2. Vérifier les permissions Windows
3. Tester manuellement : clic droit → "Exécuter"
4. Consulter l'onglet "Historique" pour les erreurs

### Erreur "Python n'est pas reconnu"
Modifier le fichier `.bat` pour utiliser le chemin complet de Python :
```batch
set PYTHON_PATH=C:\Users\HUSUNUKPE Fabrice\AppData\Local\Programs\Python\Python313\python.exe
```

### Pas de notifications envoyées
1. Vérifier que l'option `--notify` est présente
2. Implémenter la fonction d'envoi d'email (actuellement TODO)
3. Configurer les paramètres SMTP dans Django settings.py

## 📊 Ce que fait la commande

1. **Détecte** les entrées sans sortie pour la date spécifiée (par défaut : hier)
2. **Met** `worked_hours = NULL` pour ces pointages
3. **Crée** des anomalies de type `missing_punch_out`
4. **Notifie** les managers (si `--notify` est utilisé)
5. **Log** tous les résultats dans un fichier

## 🔔 Notifications (à implémenter)

Pour activer les notifications par email, décommenter et configurer la fonction `_send_email_to_manager()` dans :
```
attendance/management/commands/detect_missing_punches.py
```

Configuration email dans `settings.py` :
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@gmail.com'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe-application'
DEFAULT_FROM_EMAIL = 'noreply@votreentreprise.com'
```

## 📝 Exemples de résultats

### Aucune anomalie
```
======================================================================
   DÉTECTION AUTOMATIQUE DES OUBLIS DE POINTAGE
======================================================================

📅 Dates à vérifier: 1 jour(s)
   • Wednesday 22/10/2025

🔍 Vérification du 22/10/2025...
   ✅ Aucun oubli détecté

======================================================================
📊 RÉSUMÉ
======================================================================
• Total anomalies créées: 0
• Employés concernés: 0

✅ Aucune anomalie détectée - Tout est en ordre !
======================================================================
```

### Anomalies détectées
```
======================================================================
   DÉTECTION AUTOMATIQUE DES OUBLIS DE POINTAGE
======================================================================

📅 Dates à vérifier: 1 jour(s)
   • Wednesday 22/10/2025

🔍 Vérification du 22/10/2025...
   ⚠️  3 oubli(s) de sortie détecté(s)
      • Jean Dupont - Entrée à 08:30
      • Marie Martin - Entrée à 09:00
      • Pierre Durand - Entrée à 08:45

======================================================================
📊 RÉSUMÉ
======================================================================
• Total anomalies créées: 3
• Employés concernés: 3

📧 Envoi des notifications...
   📧 Notification pour Sophie Manager (3 anomalie(s) dans son département)
✅ 1 notification(s) envoyée(s)

⚠️  3 anomalie(s) détectée(s) et enregistrée(s)
======================================================================
```

## 🎯 Fréquence recommandée

- **Production** : Quotidien à 01:00 (après minuit, pour vérifier la veille)
- **Test** : Manuel ou toutes les heures pour validation
- **Week-end** : La tâche peut tourner mais ne détectera rien (scope Lun-Ven)

## 📞 Support

En cas de problème, vérifier :
1. Les logs dans le dossier `logs/`
2. L'historique du Planificateur de tâches
3. Que Python et Django fonctionnent correctement
4. Les permissions de l'utilisateur Windows
