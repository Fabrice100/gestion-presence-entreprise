#!/usr/bin/env python
"""Script pour vérifier la configuration des soldes de congés."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from leave.models import LeaveType, LeaveBalance
from django.contrib.auth.models import User

print("\n=== VÉRIFICATION DES TYPES DE CONGÉS ===\n")

leave_types = LeaveType.objects.all()
for lt in leave_types:
    print(f"Type: {lt.name} ({lt.code})")
    print(f"  - Allocation: {lt.allocation_amount} jours")
    print(f"  - Déduit du solde: {lt.deducts_balance}")
    print(f"  - Rémunéré: {lt.is_paid}")
    print()

print("\n=== VÉRIFICATION DES SOLDES DES EMPLOYÉS ===\n")

# Chercher un employé
employee = User.objects.filter(employee_profile__role='employee').first()
if employee:
    print(f"Employé: {employee.get_full_name()}")
    balances = LeaveBalance.objects.filter(employee=employee)
    
    for balance in balances:
        print(f"\nType: {balance.leave_type.name}")
        print(f"  - Alloué: {balance.allocated_balance} jours")
        print(f"  - Pris: {balance.taken_balance} jours")
        print(f"  - Restant: {balance.remaining_balance} jours")
else:
    print("Aucun employé trouvé")

print()

