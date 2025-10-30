# 📍 GUIDE : Corriger les Coordonnées GPS du Bureau

## ❌ Problème : "Vous êtes trop loin (3679m)"

Si vous recevez cette erreur alors que vous êtes au bureau, c'est que **les coordonnées GPS du bureau sont incorrectes**.

---

## ✅ SOLUTION 1 : Obtenir les Bonnes Coordonnées

### Méthode 1 : Google Maps (Recommandé)

1. **Ouvrez Google Maps** (web ou app mobile)
2. **Tapez l'adresse exacte de votre bureau** dans la recherche
3. **Cliquez droit** sur le point rouge qui apparaît
4. **Sélectionnez "Plus d'infos sur ce lieu"** ou "Coordonnées"
5. **Les coordonnées s'affichent** en bas de l'écran (format: `6.1658156, 1.2542084`)
   - Le premier nombre = **Latitude**
   - Le deuxième nombre = **Longitude**

### Méthode 2 : Depuis votre téléphone au bureau

1. **Activez la géolocalisation** sur votre téléphone
2. **Ouvrez Google Maps**
3. **Appuyez sur l'icône "Votre position"** (point bleu)
4. **Maintenez appuyé** sur votre position
5. **Les coordonnées s'affichent** en haut de l'écran
6. **Notez ces coordonnées** (latitude et longitude)

---

## ✅ SOLUTION 2 : Mettre à Jour les Coordonnées

### Étape 1 : Connectez-vous en tant qu'Admin (superuser)

### Étape 2 : Allez dans la Configuration GPS

**Option A : Interface Web**
- URL : `/attendance/settings/`
- Connectez-vous avec le compte admin

**Option B : Admin Django**
- URL : `/admin/attendance/companysettings/`
- Modifiez les coordonnées

### Étape 3 : Entrez les Nouvelles Coordonnées

1. **Latitude du bureau** : Entre `-90` et `90`
   - Exemple : `6.1658156`
   
2. **Longitude du bureau** : Entre `-180` et `180`
   - Exemple : `1.2542084`

3. **Cliquez sur "Enregistrer les paramètres GPS"**

### Étape 4 : Testez

Retournez sur la page de pointage et essayez de pointer à nouveau.

---

## ✅ SOLUTION 3 : Augmenter le Rayon (Solution Temporaire)

Si vous êtes vraiment au bureau mais légèrement loin :

1. **Allez dans `/attendance/settings/`** (admin)
2. **Augmentez "Rayon autorisé"** de `200m` à `500m` ou `1000m`
3. **Enregistrez**

⚠️ **Note** : C'est une solution temporaire. Il vaut mieux corriger les coordonnées.

---

## 🔍 VÉRIFICATION

### Test avec le Script

Exécutez le script de vérification :

```bash
python check_gps_distance.py
```

Entrez vos coordonnées GPS réelles (depuis votre téléphone au bureau) et le script calculera :
- ✅ La distance réelle entre vos coordonnées et le bureau configuré
- ✅ Si vous êtes dans la zone autorisée

---

## 📊 COORDONNÉES ACTUELLES

**Configuration actuelle :**
- **Latitude** : `6.1658156`
- **Longitude** : `1.2542084`
- **Rayon autorisé** : `200 mètres`

**Si vous êtes à 3679m**, cela signifie que :
- Soit les coordonnées du bureau sont incorrectes
- Soit vous êtes vraiment loin (mais vous dites être au bureau)

---

## 💡 EXEMPLE : Lomé, Togo

Les coordonnées approximatives de Lomé sont :
- **Latitude** : `6.1304`
- **Longitude** : `1.2158`

Si votre bureau est à Lomé et que les coordonnées configurées sont différentes, c'est normal d'avoir une distance importante.

---

## ✅ CHECKLIST

- [ ] J'ai obtenu les coordonnées GPS réelles de mon bureau (Google Maps)
- [ ] J'ai vérifié que je suis bien au bureau (géolocalisation activée)
- [ ] J'ai mis à jour les coordonnées dans `/attendance/settings/`
- [ ] J'ai testé le pointage à nouveau
- [ ] Si ça ne marche toujours pas, j'ai augmenté le rayon autorisé

---

## 🆘 SI ÇA NE MARCHE TOUJOURS PAS

1. **Vérifiez que vos coordonnées GPS sont correctes** (Google Maps)
2. **Vérifiez que vous êtes bien connecté en admin** (superuser)
3. **Augmentez temporairement le rayon** à `1000m` ou `5000m` pour tester
4. **Testez depuis un autre appareil** pour isoler le problème
5. **Consultez les logs** : `logs/django.log`

