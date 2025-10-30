#!/usr/bin/env python
"""
Script pour vérifier la distance GPS entre deux points.
Utile pour déboguer les problèmes de pointage.
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.admin_models import CompanySettings
from attendance.attendance_service import GPSValidationService

def calculate_and_show_distance(point_lat, point_lon, label):
    """Calcule et affiche la distance d'un point au bureau."""
    settings = CompanySettings.load()
    distance = GPSValidationService.calculate_distance(
        point_lat,
        point_lon,
        float(settings.site_center_latitude),
        float(settings.site_center_longitude)
    )
    
    print(f"\n📍 {label}")
    print(f"   Coordonnées: {point_lat}, {point_lon}")
    print(f"   Distance du bureau: {distance:.2f} mètres ({distance/1000:.2f} km)")
    
    # Vérifier si c'est dans la zone autorisée
    if distance <= settings.allowed_radius_meters:
        print(f"   ✅ DANS LA ZONE (rayon max: {settings.allowed_radius_meters}m)")
    else:
        print(f"   ❌ HORS ZONE (rayon max: {settings.allowed_radius_meters}m)")
        print(f"   📏 Il faut se rapprocher de {distance - settings.allowed_radius_meters:.0f}m")
    
    return distance

def main():
    print("=" * 60)
    print("VÉRIFICATION GPS - Distance du bureau")
    print("=" * 60)
    
    settings = CompanySettings.load()
    
    print("\n🏢 CONFIGURATION DU BUREAU:")
    print(f"   Latitude: {settings.site_center_latitude}")
    print(f"   Longitude: {settings.site_center_longitude}")
    print(f"   Rayon autorisé: {settings.allowed_radius_meters} mètres")
    
    # Coordonnées du bureau
    bureau_lat = float(settings.site_center_latitude)
    bureau_lon = float(settings.site_center_longitude)
    
    print("\n" + "=" * 60)
    print("TESTS DE DISTANCE")
    print("=" * 60)
    
    # Test 1: Bureau exactement
    calculate_and_show_distance(bureau_lat, bureau_lon, "Bureau (coordonnées configurées)")
    
    # Test 2: Position à 100m (devrait être OK si rayon = 200m)
    # Approximation: ~0.0009 degré ≈ 100m à l'équateur
    test_lat = bureau_lat + 0.0009
    test_lon = bureau_lon
    calculate_and_show_distance(test_lat, test_lon, "Position à ~100m du bureau")
    
    # Test 3: Position à 3.7km (cas d'erreur de l'utilisateur)
    # Approximation: ~0.033 degré ≈ 3700m à l'équateur
    test_lat_far = bureau_lat + 0.033
    test_lon_far = bureau_lon
    calculate_and_show_distance(test_lat_far, test_lon_far, "Position à ~3.7km (simulation erreur)")
    
    print("\n" + "=" * 60)
    print("💡 SOLUTIONS")
    print("=" * 60)
    print("\nSi vous êtes vraiment au bureau mais recevez 3679m:")
    print("1. ⚠️ Les coordonnées du bureau sont peut-être incorrectes")
    print("2. ✅ Vérifiez vos coordonnées GPS réelles dans Google Maps")
    print("3. ✅ Mettez à jour les coordonnées du bureau dans /attendance/settings/")
    print("4. ✅ Ou augmentez le rayon autorisé si vous êtes vraiment loin")
    print("\nPour obtenir vos coordonnées GPS:")
    print("- Ouvrez Google Maps")
    print("- Cliquez droit sur votre position → 'Plus d'infos sur ce lieu'")
    print("- Les coordonnées s'affichent en bas")
    
    print("\n" + "=" * 60)
    print("TESTEZ VOS COORDONNÉES")
    print("=" * 60)
    print("\nEntrez vos coordonnées GPS réelles pour tester la distance:")
    print("(Laissez vide pour quitter)")
    
    while True:
        try:
            lat_input = input("\nLatitude: ").strip()
            if not lat_input:
                break
            
            lon_input = input("Longitude: ").strip()
            if not lon_input:
                break
            
            test_lat = float(lat_input)
            test_lon = float(lon_input)
            
            calculate_and_show_distance(test_lat, test_lon, "Vos coordonnées")
            
        except ValueError:
            print("❌ Format invalide. Utilisez des nombres décimaux (ex: 6.1658156)")
        except KeyboardInterrupt:
            print("\n\nAu revoir!")
            break

if __name__ == '__main__':
    main()

