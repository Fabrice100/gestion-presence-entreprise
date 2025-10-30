#!/usr/bin/env python
"""
Script de diagnostic complet pour identifier pourquoi le pointage ne fonctionne pas.
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.admin_models import CompanySettings
from attendance.attendance_service import GPSValidationService

def main():
    print("=" * 70)
    print("🔍 DIAGNOSTIC COMPLET - Problème de Pointage GPS")
    print("=" * 70)
    print()
    
    settings = CompanySettings.load()
    
    print("📍 CONFIGURATION ACTUELLE DU BUREAU:")
    print(f"   Latitude: {settings.site_center_latitude}")
    print(f"   Longitude: {settings.site_center_longitude}")
    print(f"   Rayon autorisé: {settings.allowed_radius_meters}m")
    print(f"   Précision GPS max: {settings.gps_accuracy_max_meters}m")
    print()
    
    print("=" * 70)
    print("📱 VOS COORDONNÉES GPS (depuis votre téléphone au bureau)")
    print("=" * 70)
    print()
    print("💡 Pour obtenir vos coordonnées:")
    print("   1. Allez au bureau avec votre téléphone")
    print("   2. Ouvrez Google Maps")
    print("   3. Cliquez sur 'Votre position' (point bleu)")
    print("   4. Maintenez appuyé sur votre position")
    print("   5. Les coordonnées s'affichent → Notez-les!")
    print()
    
    while True:
        try:
            print("-" * 70)
            lat_input = input("Entrez votre LATITUDE GPS (depuis votre téléphone): ").strip()
            if not lat_input:
                print("❌ Latitude requise!")
                continue
            user_lat = float(lat_input)
            
            lon_input = input("Entrez votre LONGITUDE GPS (depuis votre téléphone): ").strip()
            if not lon_input:
                print("❌ Longitude requise!")
                continue
            user_lon = float(lon_input)
            
            accuracy_input = input("Entrez votre PRÉCISION GPS en mètres (ou appuyez Entrée pour 50): ").strip()
            if not accuracy_input:
                user_accuracy = 50.0
            else:
                user_accuracy = float(accuracy_input)
            
            print()
            print("=" * 70)
            print("📊 RÉSULTATS DU DIAGNOSTIC")
            print("=" * 70)
            print()
            
            # Calculer la distance
            distance = GPSValidationService.calculate_distance(
                user_lat, user_lon,
                float(settings.site_center_latitude),
                float(settings.site_center_longitude)
            )
            
            print(f"📍 VOS COORDONNÉES:")
            print(f"   Latitude: {user_lat}")
            print(f"   Longitude: {user_lon}")
            print(f"   Précision GPS: {user_accuracy}m")
            print()
            
            print(f"📍 BUREAU CONFIGURÉ:")
            print(f"   Latitude: {settings.site_center_latitude}")
            print(f"   Longitude: {settings.site_center_longitude}")
            print()
            
            print(f"📏 DISTANCE CALCULÉE:")
            print(f"   {distance:.2f} mètres ({distance/1000:.2f} km)")
            print()
            
            # Validation complète
            validation = GPSValidationService.validate_location(
                lat=user_lat,
                lon=user_lon,
                accuracy=user_accuracy,
                site_lat=float(settings.site_center_latitude),
                site_lon=float(settings.site_center_longitude),
                allowed_radius=settings.allowed_radius_meters,
                max_accuracy=settings.gps_accuracy_max_meters
            )
            
            if validation['valid']:
                print("✅ VALIDATION GPS: SUCCÈS")
                print(f"   Distance: {validation['distance']:.2f}m")
                print()
                print("💡 Le pointage DEVRAIT fonctionner avec ces coordonnées!")
                print("   Si ça ne marche toujours pas, le problème vient d'ailleurs.")
            else:
                print("❌ VALIDATION GPS: ÉCHEC")
                print(f"   {validation['error_message']}")
                print()
                
                # Analyser le problème
                print("🔍 ANALYSE DU PROBLÈME:")
                print()
                
                if distance > settings.allowed_radius_meters:
                    print(f"   ❌ PROBLÈME 1: Distance trop grande")
                    print(f"      - Vous êtes à {distance:.0f}m du bureau configuré")
                    print(f"      - Maximum autorisé: {settings.allowed_radius_meters}m")
                    print(f"      - Différence: {distance - settings.allowed_radius_meters:.0f}m")
                    print()
                    print(f"   💡 SOLUTIONS:")
                    print(f"      Option A: Mettre à jour les coordonnées du bureau")
                    print(f"         - Utilisez VOS coordonnées comme nouvelles coordonnées du bureau")
                    print(f"         - Latitude: {user_lat}")
                    print(f"         - Longitude: {user_lon}")
                    print()
                    print(f"      Option B: Augmenter le rayon autorisé")
                    print(f"         - Rayon actuel: {settings.allowed_radius_meters}m")
                    print(f"         - Nouveau rayon: {int(distance + 50)}m (recommandé)")
                    print()
                
                if user_accuracy > settings.gps_accuracy_max_meters:
                    print(f"   ❌ PROBLÈME 2: Précision GPS trop faible")
                    print(f"      - Votre précision: {user_accuracy:.0f}m")
                    print(f"      - Maximum autorisé: {settings.gps_accuracy_max_meters}m")
                    print()
                    print(f"   💡 SOLUTIONS:")
                    print(f"      - Sortez à l'extérieur")
                    print(f"      - Attendez 5-10 secondes que le GPS se stabilise")
                    print(f"      - Évitez les bâtiments avec beaucoup de métal/béton")
                    print(f"      - OU augmentez 'Précision GPS max' à {int(user_accuracy + 50)}m")
                    print()
            
            print("=" * 70)
            print()
            
            # Proposer la mise à jour
            if distance > settings.allowed_radius_meters:
                print("🔄 VOULEZ-VOUS METTRE À JOUR LES COORDONNÉES DU BUREAU?")
                print(f"   Remplacez ({settings.site_center_latitude}, {settings.site_center_longitude})")
                print(f"   par ({user_lat}, {user_lon})")
                print()
                confirm = input("   Mettre à jour? (oui/non): ").strip().lower()
                
                if confirm in ['oui', 'o', 'yes', 'y']:
                    settings.site_center_latitude = user_lat
                    settings.site_center_longitude = user_lon
                    settings.save()
                    
                    print()
                    print("✅ COORDONNÉES MISES À JOUR!")
                    print(f"   Nouvelle latitude: {settings.site_center_latitude}")
                    print(f"   Nouvelle longitude: {settings.site_center_longitude}")
                    print()
                    print("💡 Essayez de pointer maintenant - ça devrait fonctionner!")
                else:
                    print("❌ Mise à jour annulée.")
            
            print()
            retry = input("Voulez-vous tester d'autres coordonnées? (oui/non): ").strip().lower()
            if retry not in ['oui', 'o', 'yes', 'y']:
                break
            
        except ValueError:
            print("❌ Format invalide! Utilisez des nombres décimaux (ex: 6.1658156)")
            print()
        except KeyboardInterrupt:
            print("\n\n❌ Annulé.")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            break

if __name__ == '__main__':
    main()

