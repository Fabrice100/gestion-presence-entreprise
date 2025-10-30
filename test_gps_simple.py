#!/usr/bin/env python
"""Script simple pour tester et corriger rapidement le GPS."""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.admin_models import CompanySettings
from attendance.attendance_service import GPSValidationService

print("=" * 60)
print("DIAGNOSTIC RAPIDE GPS")
print("=" * 60)
print()

settings = CompanySettings.load()

print(f"📍 Coordonnées du bureau:")
print(f"   Latitude: {settings.site_center_latitude}")
print(f"   Longitude: {settings.site_center_longitude}")
print(f"   Rayon: {settings.allowed_radius_meters}m")
print()

print("❓ PROBLÈME PROBABLE:")
print()
print("1. Les coordonnées du bureau sont incorrectes")
print("   → Vous êtes au bureau mais le système pense que vous êtes à 3679m")
print()
print("2. Les coordonnées GPS de votre téléphone changent à chaque fois")
print("   → Le GPS peut varier de quelques mètres, donc si vous êtes")
print("     juste à la limite, ça peut échouer")
print()

print("✅ SOLUTION IMMÉDIATE:")
print()
print("Augmenter temporairement le rayon à 500m pour que ça fonctionne:")
print()

confirm = input("Augmenter le rayon à 500m? (oui/non): ").strip().lower()

if confirm in ['oui', 'o', 'yes', 'y']:
    settings.allowed_radius_meters = 500
    settings.gps_accuracy_max_meters = 300
    settings.save()
    print()
    print("✅ RAYON AUGMENTÉ À 500m")
    print("✅ PRÉCISION MAX AUGMENTÉE À 300m")
    print()
    print("💡 Essayez de pointer maintenant - ça devrait fonctionner!")
    print()
    print("⚠️  Note: Après, vous pourrez:")
    print("   - Corriger les coordonnées du bureau")
    print("   - Réduire le rayon à 200m si vous voulez")
else:
    print()
    print("❌ Annulé.")
    print()
    print("💡 Pour corriger les coordonnées:")
    print("   1. Ouvrez Google Maps sur votre téléphone")
    print("   2. Allez au bureau")
    print("   3. Obtenez vos coordonnées GPS")
    print("   4. Allez dans /attendance/settings/ (admin)")
    print("   5. Mettez à jour latitude et longitude")

