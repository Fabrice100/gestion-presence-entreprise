#!/usr/bin/env python
"""
Script pour débugger les données GPS envoyées depuis le formulaire.
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from common.secure_validation import SecureDataValidator

def test_gps_validation(lat, lon, acc):
    """Teste la validation GPS avec différentes valeurs."""
    validator = SecureDataValidator()
    
    print(f"Test avec:")
    print(f"  Latitude: {lat} (type: {type(lat)})")
    print(f"  Longitude: {lon} (type: {type(lon)})")
    print(f"  Accuracy: {acc} (type: {type(acc)})")
    print()
    
    result = validator.validate_gps_coordinates(
        str(lat) if lat is not None else '',
        str(lon) if lon is not None else '',
        str(acc) if acc is not None else '50'
    )
    
    if result['valid']:
        print("✅ VALIDATION RÉUSSIE")
        print(f"   Latitude: {result.get('latitude')}")
        print(f"   Longitude: {result.get('longitude')}")
        print(f"   Accuracy: {result.get('accuracy')}")
    else:
        print("❌ VALIDATION ÉCHOUÉE")
        print(f"   Erreur: {result.get('error_message')}")
    
    print()
    print("-" * 60)
    print()

if __name__ == '__main__':
    print("=" * 60)
    print("TESTS DE VALIDATION GPS")
    print("=" * 60)
    print()
    
    # Test 1: Valeurs normales
    print("TEST 1: Valeurs normales")
    test_gps_validation('6.1410797', '1.2328214', '50')
    
    # Test 2: Valeurs vides (chaînes vides)
    print("TEST 2: Valeurs vides (chaînes vides)")
    test_gps_validation('', '', '')
    
    # Test 3: None
    print("TEST 3: None")
    test_gps_validation(None, None, None)
    
    # Test 4: 'None' comme string
    print("TEST 4: 'None' comme string")
    test_gps_validation('None', 'None', 'None')
    
    # Test 5: '0' et '0.0'
    print("TEST 5: '0' et '0.0'")
    test_gps_validation('0', '0', '0')
    
    # Test 6: Float Python
    print("TEST 6: Float Python (comme depuis le template)")
    test_gps_validation(6.1410797, 1.2328214, 50.0)
    
    # Test 7: NaN (cas d'erreur)
    print("TEST 7: NaN")
    import math
    test_gps_validation(str(float('nan')), str(float('nan')), '50')

