# 🚀 GUIDE RAPIDE : Corriger les Coordonnées GPS (200m)

## ⚡ SOLUTION RAPIDE EN 3 ÉTAPES

### Étape 1 : Obtenir vos Coordonnées GPS Réelles

**Sur votre téléphone (au bureau exactement) :**

1. Ouvrez **Google Maps**
2. Activez la **géolocalisation**
3. Allez **exactement où vous pointez habituellement**
4. Cliquez sur **"Votre position"** (le point bleu)
5. **Maintenez appuyé** sur votre position sur la carte
6. Les coordonnées s'affichent → **Notez-les !**

**Format attendu :**
```
Latitude: 6.1658156
Longitude: 1.2542084
```

---

### Étape 2 : Mettre à Jour les Coordonnées

**Option A : Script Python (Recommandé)**

```bash
python update_gps_coordinates.py
```

Suivez les instructions et entrez vos nouvelles coordonnées.

**Option B : Interface Web (Admin)**

1. Connectez-vous avec le compte **admin** (superuser)
2. Allez dans : `/attendance/settings/`
3. Modifiez :
   - **Latitude du bureau** : Vos coordonnées latitude
   - **Longitude du bureau** : Vos coordonnées longitude
4. Cliquez sur **"Enregistrer les paramètres GPS"**

---

### Étape 3 : Tester

1. Retournez sur la page de **pointage**
2. Essayez de pointer
3. **Ça devrait fonctionner !** ✅

---

## 📍 EXEMPLE

**Coordonnées actuelles (incorrectes ?) :**
- Latitude: `6.1658156`
- Longitude: `1.2542084`

**Si vous êtes au bureau et le système dit "3679m" :**
→ Les coordonnées du bureau sont **incorrectes** ou **mal configurées**.

---

## ✅ VÉRIFICATION

Pour vérifier vos coordonnées :

1. Utilisez **Google Maps** avec l'adresse **exacte** de votre bureau
2. Comparez les coordonnées affichées avec celles dans `/attendance/settings/`
3. Si elles sont différentes → **Mettez à jour !**

---

## 🆘 SI ÇA NE MARCHE TOUJOURS PAS

1. Vérifiez que vous êtes bien **au bureau** (pas à côté)
2. Vérifiez que votre **GPS fonctionne** (l'icône GPS dans Maps)
3. Attendez **5-10 secondes** que le GPS se stabilise avant de pointer
4. **Augmentez temporairement le rayon** à 500m pour tester, puis réduisez après

---

## 💡 ASTUCE

**Pour obtenir les coordonnées exactes de votre bureau :**

1. Google Maps Web → Tapez votre adresse → Cliquez droit → "Coordonnées"
2. C'est plus précis que depuis le téléphone (qui peut varier)

