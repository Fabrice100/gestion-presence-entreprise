# 🔧 GUIDE : Résolution des Problèmes de Pointage GPS

## ❌ Erreur : "Le pointage ne passe pas"

### Causes possibles :

#### 1️⃣ **Distance trop grande du bureau**

**Erreur typique :**
```
Vous êtes trop loin du lieu de travail (XXXm). Distance maximale autorisée: 200m.
```

**Solution :**
- ✅ Vérifiez que vous êtes **à moins de 200 mètres** du bureau
- ✅ Si vous êtes plus loin, rapprochez-vous du bureau
- ✅ Ou demandez à l'admin d'augmenter le "Rayon autorisé" dans les paramètres

**Comment vérifier votre distance :**
- Utilisez Google Maps pour mesurer la distance entre votre position et le bureau
- Vérifiez vos coordonnées GPS actuelles

---

#### 2️⃣ **Précision GPS trop faible**

**Erreur typique :**
```
Précision GPS trop faible (XXXm). Précision maximale autorisée: 200m.
Veuillez vous rapprocher d'une fenêtre ou sortir à l'extérieur.
```

**Solution :**
- ✅ **Sortez à l'extérieur** si vous êtes à l'intérieur
- ✅ **Approchez-vous d'une fenêtre** si vous ne pouvez pas sortir
- ✅ **Attendez quelques secondes** pour que le GPS se stabilise (l'icône GPS doit cesser de clignoter)
- ✅ **Évitez les bâtiments avec beaucoup de béton/métal**

**Améliorer la précision GPS :**
- Activer la localisation précise dans les paramètres de votre téléphone
- Désactiver le mode économie d'énergie pendant le pointage
- Attendre 5-10 secondes que le GPS se calcule

---

#### 3️⃣ **Coordonnées GPS invalides**

**Erreur typique :**
```
Données GPS invalides.
Format de latitude invalide.
```

**Solution :**
- ✅ Autorisez l'accès à la géolocalisation dans votre navigateur
- ✅ Vérifiez que le GPS de votre appareil fonctionne
- ✅ Actualisez la page et réessayez

---

## 📋 VÉRIFICATION ÉTAPE PAR ÉTAPE

### Étape 1 : Vérifiez votre configuration GPS

1. Allez dans `/attendance/settings/` (en tant qu'admin)
2. Vérifiez :
   - **Latitude du bureau** : Les coordonnées sont-elles correctes ?
   - **Longitude du bureau** : Les coordonnées sont-elles correctes ?
   - **Rayon autorisé** : Est-il suffisant ? (défaut: 200m)
   - **Précision GPS max** : Est-elle raisonnable ? (défaut: 200m)

### Étape 2 : Testez votre position

Lancez le script de diagnostic :
```bash
python diagnose_gps.py
```

Cela vous montrera :
- ✅ Votre configuration actuelle
- ✅ Des tests de validation GPS
- ✅ Des recommandations

### Étape 3 : Vérifiez les logs

Consultez les logs pour voir l'erreur exacte :
```bash
# Windows PowerShell
Get-Content logs\django.log -Tail 50 | Select-String -Pattern "GPS|punch"
```

---

## 💡 SOLUTIONS SPÉCIFIQUES

### Problème : Distance toujours trop grande

**Solutions :**

1. **Augmenter le rayon autorisé** (Admin seulement) :
   - Aller dans `/attendance/settings/`
   - Augmenter "Rayon autorisé" à 500m ou plus (selon besoin)

2. **Vérifier les coordonnées du bureau** :
   - Utiliser Google Maps pour obtenir les coordonnées précises
   - Vérifier que les coordonnées entrées sont correctes

### Problème : Précision GPS toujours trop faible

**Solutions :**

1. **Augmenter la précision GPS max** (Admin seulement) :
   - Aller dans `/attendance/settings/`
   - Augmenter "Précision GPS maximale" à 300m ou plus

2. **Pour l'employé** :
   - Sortir dehors avant de pointer
   - Attendre que le GPS se stabilise (5-10 secondes)
   - Éviter les zones avec beaucoup d'interférences

---

## 🔍 DIAGNOSTIC RAPIDE

### Test rapide : Êtes-vous dans la zone ?

1. **Ouvrez Google Maps** sur votre téléphone
2. **Tapez votre adresse de bureau** et notez les coordonnées
3. **Activez "Votre position"** sur Google Maps
4. **Mesurez la distance** entre votre position et le bureau
5. **Comparez avec le rayon autorisé** dans les paramètres

### Test rapide : Précision GPS

1. **Ouvrez une app GPS** (ex: Google Maps)
2. **Regardez l'icône de précision** (cercle bleu)
3. **Si le cercle est très grand (> 200m)** → précision trop faible
4. **Sortez dehors** et attendez que le cercle se réduise

---

## ⚙️ AJUSTEMENT DES PARAMÈTRES (Admin)

### Interface Web (`/attendance/settings/`)

1. Connectez-vous en tant qu'admin (superuser)
2. Allez dans "Configuration GPS"
3. Modifiez :
   - **Rayon autorisé** : Distance max du bureau (ex: 200m → 500m)
   - **Précision GPS max** : Précision minimale acceptée (ex: 200m → 300m)
4. Cliquez sur "Enregistrer les paramètres GPS"

### Admin Django (`/admin/attendance/companysettings/`)

Même interface mais via l'admin Django.

---

## 📞 EN CAS DE PROBLÈME PERSISTANT

1. **Vérifiez les logs** (`logs/django.log`)
2. **Lancez le diagnostic** (`python diagnose_gps.py`)
3. **Vérifiez les coordonnées** dans Google Maps
4. **Testez depuis un autre appareil** pour isoler le problème

---

## ✅ CHECKLIST DE VÉRIFICATION

Avant de pointer, vérifiez :

- [ ] Vous êtes à moins de **200m** (ou rayon configuré) du bureau
- [ ] Votre précision GPS est inférieure à **200m** (ou max configuré)
- [ ] Votre GPS est activé et fonctionne
- [ ] Vous avez autorisé la géolocalisation dans le navigateur
- [ ] Vous avez attendu 5-10 secondes pour que le GPS se stabilise
- [ ] Vous êtes dehors ou près d'une fenêtre

Si tous les points sont OK et que ça ne marche toujours pas :
→ Consultez les logs et contactez l'admin système.

