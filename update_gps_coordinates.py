#!/usr/bin/env python
"""
Script pour mettre à jour les coordonnées GPS du bureau.
Utilisez les coordonnées de votre téléphone quand vous êtes au bureau.
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
    print("=" * 60)
    print("MISE À JOUR DES COORDONNÉES GPS DU BUREAU")
    print("=" * 60)
    print()
    
    settings = CompanySettings.load()
    
    print("📍 COORDONNÉES ACTUELLES:")
    print(f"   Latitude: {settings.site_center_latitude}")
    print(f"   Longitude: {settings.site_center_longitude}")
    print(f"   Rayon autorisé: {settings.allowed_radius_meters}m")
    print()
    print("📱 POUR OBTENIR VOS COORDONNÉES:")
    print("   1. Ouvrez Google Maps sur votre téléphone")
    print("   2. Activez la géolocalisation")
    print("   3. Allez au bureau (exactement où vous pointez)")
    print("   4. Cliquez sur 'Votre position' (point bleu)")
    print("   5. Maintenez appuyé sur votre position")
    print("   6. Les coordonnées s'affichent en haut")
    print("   7. Notez la latitude et la longitude")
    print()
    print("   OU")
    print()
    print("   1. Ouvrez Google Maps web")
    print("   2. Tapez l'adresse exacte de votre bureau")
    print("   3. Cliquez droit sur le point rouge")
    print("   4. Sélectionnez 'Coordonnées'")
    print("   5. Copiez les deux nombres")
    print()
    print("=" * 60)
    print()
    
    while True:
        try:
            # Demander la nouvelle latitude
            lat_input = input("Entrez la NOUVELLE latitude du bureau (ex: 6.1658156): ").strip()
            if not lat_input:
                print("❌ Latitude requise!")
                continue
            new_lat = float(lat_input)
            
            if not (-90 <= new_lat <= 90):
                print("❌ Latitude invalide! Doit être entre -90 et 90.")
                continue
            
            # Demander la nouvelle longitude
            lon_input = input("Entrez la NOUVELLE longitude du bureau (ex: 1.2542084): ").strip()
            if not lon_input:
                print("❌ Longitude requise!")
                continue
            new_lon = float(lon_input)
            
            if not (-180 <= new_lon <= 180):
                print("❌ Longitude invalide! Doit être entre -180 et 180.")
                continue
            
            # Afficher la distance avec l'ancienne position
            old_distance = GPSValidationService.calculate_distance(
                new_lat, new_lon,
                float(settings.site_center_latitude),
                float(settings.site_center_longitude)
            )
            
            print()
            print("=" * 60)
            print("CONFIRMATION")
            print("=" * 60)
            print(f"Anciennes coordonnées: {settings.site_center_latitude}, {settings.site_center_longitude}")
            print(f"Nouvelles coordonnées: {new_lat}, {new_lon}")
            print(f"Distance entre ancien et nouveau: {old_distance:.2f}m ({old_distance/1000:.2f}km)")
            print()
            
            confirm = input("✅ Confirmer la mise à jour? (oui/non): ").strip().lower()
            if confirm in ['oui', 'o', 'yes', 'y']:
                # Mettre à jour
                settings.site_center_latitude = new_lat
                settings.site_center_longitude = new_lon
                settings.save()
                
                print()
                print("✅ COORDONNÉES MISES À JOUR AVEC SUCCÈS!")
                print()
                print(f"   Nouvelle latitude: {settings.site_center_latitude}")
                print(f"   Nouvelle longitude: {settings.site_center_longitude}")
                print(f"   Rayon autorisé: {settings.allowed_radius_meters}m")
                print()
                print("💡 MAINTENANT:")
                print("   - Essayez de pointer depuis le bureau")
                print("   - Ça devrait fonctionner si vous êtes à moins de 200m")
                print()
                
                # Test rapide: distance depuis les nouvelles coordonnées (doit être 0)
                test_distance = GPSValidationService.calculate_distance(
                    new_lat, new_lon,
                    float(settings.site_center_latitude),
                    float(settings.site_center_longitude)
                )
                print(f"   ✅ Distance de test: {test_distance:.2f}m (devrait être 0)")
                break
            else:
                print("❌ Mise à jour annulée.")
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

