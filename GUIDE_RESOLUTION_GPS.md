# GUIDE DE RÉSOLUTION: Problème de Distance GPS

## 🔍 DIAGNOSTIC RAPIDE

### Étapes de vérification:
1. **Aller sur**: http://127.0.0.1:8000/attendance/test-gps/
2. **Cliquer sur** "Tester GPS"
3. **Autoriser** la géolocalisation si demandé

### ✅ RÉSULTATS ATTENDUS:
- GPS OK avec coordonnées réelles
- Distance du bureau < 200m si vous êtes au bureau
- Précision < 100m

## 🚨 PROBLÈMES FRÉQUENTS

### Problème 1: Permission GPS refusée
**Solution**: 
- Cliquer sur l'icône de verrou dans la barre d'adresse
- Autoriser la géolocalisation
- Actualiser la page

### Problème 2: Coordonnées 0.0, 0.0
**Causes possibles**:
- GPS pas autorisé
- Mode bureau activé (normal)
- Timeout GPS (> 10 secondes)

### Problème 3: Distance trop importante
**Vérifications**:
1. Les coordonnées du bureau: 6.140766, 1.241907
2. Votre position réelle
3. Mode GPS activé (pas mode bureau)

## 🔧 SOLUTIONS RAPIDES

### Solution A: Forcer mode bureau
```javascript
// Dans la console navigateur:
document.getElementById('latitude').value = '6.140766';
document.getElementById('longitude').value = '1.241907';
```

### Solution B: Test manuel des coordonnées
```python
# Dans Django shell:
from attendance.models import Attendance
test = Attendance(latitude=6.140766, longitude=1.241907)
print(f"Distance: {test.calculate_distance_from_site()}m")  # Doit être 0.0
```

### Solution C: Vérifier configuration
```python
from attendance.admin_models import CompanySettings
settings = CompanySettings.load()
print(f"Bureau: {settings.site_center_latitude}, {settings.site_center_longitude}")
```

## 📱 UTILISATION RECOMMANDÉE

### Pour les employés au bureau:
1. **Utiliser mode bureau** (bouton GPS désactivé)
2. Les coordonnées seront automatiquement 6.140766, 1.241907
3. Distance = 0.0m garantie

### Pour les employés en déplacement:
1. **Activer GPS** avant de pointer
2. Attendre confirmation de position
3. Pointer normalement

## ⚠️ NOTES IMPORTANTES

- Le système accepte jusqu'à 200m du bureau
- La précision GPS doit être < 100m
- En cas d'échec GPS, le système bascule en mode bureau automatiquement
- Les anciens enregistrements avec 0.0, 0.0 sont normaux

## 🎯 TEST FINAL

Une fois configuré:
1. Aller sur: http://127.0.0.1:8000/attendance/punch/
2. Activer/désactiver GPS selon besoin
3. Faire un pointage test
4. Vérifier que la distance est correcte

---
*Guide créé le 15/10/2025 - Système de pointage v1.0*