#!/usr/bin/env python
"""
Script RAPIDE pour corriger le problème GPS immédiatement.
Augmente le rayon autorisé pour permettre le pointage.
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.admin_models import CompanySettings

def main():
    print("=" * 60)
    print("CORRECTION GPS IMMÉDIATE")
    print("=" * 60)
    print()
    
    settings = CompanySettings.load()
    
    print("📊 CONFIGURATION ACTUELLE:")
    print(f"   Latitude: {settings.site_center_latitude}")
    print(f"   Longitude: {settings.site_center_longitude}")
    print(f"   Rayon autorisé: {settings.allowed_radius_meters}m")
    print(f"   Précision max: {settings.gps_accuracy_max_meters}m")
    print()
    
    # Augmenter le rayon à 5000m (5km) pour permettre le pointage
    print("🔧 AUGMENTATION DU RAYON AUTORISÉ...")
    settings.allowed_radius_meters = 5000  # 5 km
    settings.gps_accuracy_max_meters = 500  # Augmenter aussi la précision max
    settings.save()
    
    print("✅ RAYON AUGMENTÉ À 5000m (5 km)")
    print("✅ PRÉCISION MAX AUGMENTÉE À 500m")
    print()
    print("💡 MAINTENANT:")
    print("   - Vous pouvez pointer depuis n'importe quel endroit à moins de 5 km")
    print("   - Le pointage devrait fonctionner immédiatement")
    print()
    print("⚠️  NOTE:")
    print("   - C'est une solution temporaire pour que ça fonctionne")
    print("   - Vous pourrez ajuster les coordonnées du bureau après")
    print("   - Ou réduire le rayon si vous voulez être plus strict")
    print()

if __name__ == '__main__':
    main()

