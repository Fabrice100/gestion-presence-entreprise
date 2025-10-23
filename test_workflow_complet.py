#!/usr/bin/env python
"""
Test du workflow complet de création d'employé avec email de bienvenue.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from accounts.user_services import UserService
from accounts.models import Department
from django.contrib.auth.models import User

def test_employee_creation_workflow():
    """Test du workflow complet de création d'employé."""
    
    print('🧪 Test workflow complet : Création employé + Email bienvenue')
    print('=' * 60)
    
    # Créer un département si nécessaire
    dept, created = Department.objects.get_or_create(
        name='Test Department',
        defaults={'description': 'Département pour les tests'}
    )
    
    # Données de test pour un nouvel employé
    user_data = {
        'username': 'test.employee',
        'email': 'test.employee@example.com',
        'first_name': 'Test',
        'last_name': 'Employee',
        'password': 'temp123'  # Sera remplacé par un mot de passe généré
    }
    
    profile_data = {
        'employee_id': 'EMP999',
        'department': dept,
        'role': 'employee',
        'can_punch': True,
        'is_active': True
    }
    
    print('📝 Création de l\'employé...')
    result = UserService.create_employee_with_credentials(user_data, profile_data)
    
    if result['success']:
        print('✅ Employé créé avec succès !')
        print(f'   - ID Employé: {result["employee_id"]}')
        print(f'   - Mot de passe: {result["temporary_password"]}')
        print(f'   - Email envoyé: {result["email_sent"]}')
        return result['user']
    else:
        print('❌ Erreur:', result['error'])
        return None

if __name__ == '__main__':
    test_employee_creation_workflow()
