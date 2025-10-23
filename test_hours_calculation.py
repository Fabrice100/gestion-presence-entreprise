"""
Test manuel du service de calcul des heures.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.hours_calculation_service import HoursCalculationService
from datetime import time
from decimal import Decimal

print("=" * 60)
print("TEST DU SERVICE DE CALCUL DES HEURES")
print("=" * 60)

# Test 1: Journée normale 9h-18h
result1 = HoursCalculationService.calculate_worked_hours(time(9, 0), time(18, 0))
print(f"\n✅ Test 1: 9h00 - 18h00")
print(f"   Durée brute: 9h")
print(f"   Pause: -1h")
print(f"   Résultat: {result1}h (plafonné à 8h)")
assert result1 == Decimal('8.00'), f"Erreur: attendu 8.00, obtenu {result1}"

# Test 2: Journée normale 9h-17h
result2 = HoursCalculationService.calculate_worked_hours(time(9, 0), time(17, 0))
print(f"\n✅ Test 2: 9h00 - 17h00")
print(f"   Durée brute: 8h")
print(f"   Pause: -1h")
print(f"   Résultat: {result2}h")
assert result2 == Decimal('7.00'), f"Erreur: attendu 7.00, obtenu {result2}"

# Test 3: Demi-journée 10h-12h30
result3 = HoursCalculationService.calculate_worked_hours(time(10, 0), time(12, 30))
print(f"\n✅ Test 3: 10h00 - 12h30")
print(f"   Durée brute: 2.5h")
print(f"   Pause: -1h")
print(f"   Résultat: {result3}h")
assert result3 == Decimal('1.50'), f"Erreur: attendu 1.50, obtenu {result3}"

# Test 4: Journée longue 8h-19h
result4 = HoursCalculationService.calculate_worked_hours(time(8, 0), time(19, 0))
print(f"\n✅ Test 4: 8h00 - 19h00 (heures sup)")
print(f"   Durée brute: 11h")
print(f"   Pause: -1h")
print(f"   Résultat: {result4}h (plafonné à 8h)")
assert result4 == Decimal('8.00'), f"Erreur: attendu 8.00, obtenu {result4}"

# Test 5: Arrivée tardive, sortie normale 14h-18h
result5 = HoursCalculationService.calculate_worked_hours(time(14, 0), time(18, 0))
print(f"\n✅ Test 5: 14h00 - 18h00")
print(f"   Durée brute: 4h")
print(f"   Pause: -1h")
print(f"   Résultat: {result5}h")
assert result5 == Decimal('3.00'), f"Erreur: attendu 3.00, obtenu {result5}"

# Test 6: Journée complète 8h-17h
result6 = HoursCalculationService.calculate_worked_hours(time(8, 0), time(17, 0))
print(f"\n✅ Test 6: 8h00 - 17h00")
print(f"   Durée brute: 9h")
print(f"   Pause: -1h")
print(f"   Résultat: {result6}h (plafonné à 8h)")
assert result6 == Decimal('8.00'), f"Erreur: attendu 8.00, obtenu {result6}"

print("\n" + "=" * 60)
print("✅ TOUS LES TESTS RÉUSSIS !")
print("=" * 60)
print("\n📋 RÈGLES VALIDÉES:")
print("   ✓ Pause fixe de 1h déduite automatiquement")
print("   ✓ Plafonnement à 8h maximum")
print("   ✓ Calcul précis avec 2 décimales")
