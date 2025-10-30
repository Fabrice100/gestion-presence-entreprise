#!/usr/bin/env python
"""
Script de diagnostic GPS pour le système de pointage.

Ce script vérifie:
1. Les coordonnées GPS configurées
2. Le rayon autorisé
3. La précision GPS maximale acceptée
4. Teste une validation GPS avec des coordonnées d'exemple
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.admin_models import CompanySettings
from attendance.attendance_service import GPSValidationService


def main():
    print("=" * 60)
    print("DIAGNOSTIC GPS - Système de Pointage")
    print("=" * 60)
    print()
    
    # 1. Charger les paramètres
    settings = CompanySettings.load()
    
    print("📍 CONFIGURATION ACTUELLE:")
    print(f"   GPS Obligatoire: {'✅ Oui' if settings.gps_required else '❌ Non'}")
    print(f"   Latitude du bureau: {settings.site_center_latitude}")
    print(f"   Longitude du bureau: {settings.site_center_longitude}")
    print(f"   Rayon autorisé: {settings.allowed_radius_meters} mètres")
    print(f"   Précision GPS max: {settings.gps_accuracy_max_meters} mètres")
    print()
    
    # 2. Test avec les coordonnées du bureau (doit toujours passer)
    print("🧪 TEST 1: Pointage depuis le bureau exactement")
    result = GPSValidationService.validate_location(
        lat=float(settings.site_center_latitude),
        lon=float(settings.site_center_longitude),
        accuracy=10.0,  # Excellente précision
        site_lat=float(settings.site_center_latitude),
        site_lon=float(settings.site_center_longitude),
        allowed_radius=settings.allowed_radius_meters,
        max_accuracy=settings.gps_accuracy_max_meters
    )
    
    if result['valid']:
        print(f"   ✅ SUCCÈS - Distance: {result['distance']:.2f} m")
    else:
        print(f"   ❌ ÉCHEC - {result['error_message']}")
    print()
    
    # 3. Test avec une distance proche (dans le rayon)
    print("🧪 TEST 2: Pointage à 50m du bureau")
    # Ajouter environ 50m de décalage (approximation: ~0.00045 degré ≈ 50m à l'équateur)
    test_lat = float(settings.site_center_latitude) + 0.00045
    test_lon = float(settings.site_center_longitude)
    
    result = GPSValidationService.validate_location(
        lat=test_lat,
        lon=test_lon,
        accuracy=15.0,
        site_lat=float(settings.site_center_latitude),
        site_lon=float(settings.site_center_longitude),
        allowed_radius=settings.allowed_radius_meters,
        max_accuracy=settings.gps_accuracy_max_meters
    )
    
    if result['valid']:
        print(f"   ✅ SUCCÈS - Distance: {result['distance']:.2f} m")
    else:
        print(f"   ❌ ÉCHEC - {result['error_message']}")
    print()
    
    # 4. Test avec précision trop faible
    print(f"🧪 TEST 3: Pointage avec précision trop faible ({settings.gps_accuracy_max_meters + 50}m)")
    result = GPSValidationService.validate_location(
        lat=float(settings.site_center_latitude),
        lon=float(settings.site_center_longitude),
        accuracy=float(settings.gps_accuracy_max_meters + 50),
        site_lat=float(settings.site_center_latitude),
        site_lon=float(settings.site_center_longitude),
        allowed_radius=settings.allowed_radius_meters,
        max_accuracy=settings.gps_accuracy_max_meters
    )
    
    if result['valid']:
        print(f"   ✅ SUCCÈS - Distance: {result['distance']:.2f} m")
    else:
        print(f"   ❌ ÉCHEC (attendu) - {result['error_message']}")
    print()
    
    # 5. Test avec distance trop grande
    print(f"🧪 TEST 4: Pointage trop loin du bureau (> {settings.allowed_radius_meters}m)")
    # Ajouter un décalage important (environ 500m = ~0.0045 degré)
    far_lat = float(settings.site_center_latitude) + 0.0045
    far_lon = float(settings.site_center_longitude)
    
    result = GPSValidationService.validate_location(
        lat=far_lat,
        lon=far_lon,
        accuracy=10.0,
        site_lat=float(settings.site_center_latitude),
        site_lon=float(settings.site_center_longitude),
        allowed_radius=settings.allowed_radius_meters,
        max_accuracy=settings.gps_accuracy_max_meters
    )
    
    if result['valid']:
        print(f"   ✅ SUCCÈS - Distance: {result['distance']:.2f} m")
    else:
        print(f"   ❌ ÉCHEC (attendu) - {result['error_message']}")
    print()
    
    # 6. Recommandations
    print("💡 RECOMMANDATIONS:")
    print()
    print("   Si le pointage échoue, vérifiez:")
    print(f"   1. ✅ Votre distance du bureau < {settings.allowed_radius_meters}m")
    print(f"   2. ✅ Votre précision GPS < {settings.gps_accuracy_max_meters}m")
    print("   3. ✅ Vos coordonnées GPS sont correctes")
    print("   4. ✅ Le GPS de votre appareil fonctionne")
    print()
    print("   Pour ajuster les paramètres:")
    print("   - Admin → /attendance/settings/ (interface web)")
    print("   - Admin Django → /admin/attendance/companysettings/")
    print()


if __name__ == '__main__':
    main()

