"""
Script pour créer un superutilisateur Django.

Ce script crée automatiquement un superutilisateur pour l'interface d'administration.
"""

import os
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile

def create_admin_user():
    """Crée un utilisateur administrateur avec profil employé."""
    
    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(username='admin').exists():
        print("L'utilisateur 'admin' existe déjà.")
        return
    
    # Créer l'utilisateur administrateur
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123',
        first_name='Administrateur',
        last_name='Système'
    )
    
    # Mettre à jour le profil employé
    try:
        profile = admin_user.employee_profile
        profile.role = 'admin'
        profile.employee_id = 'ADM001'
        profile.can_punch = False  # L'admin ne pointe pas
        profile.save()
        print("Profil administrateur mis à jour.")
    except EmployeeProfile.DoesNotExist:
        print("Erreur: Profil employé non trouvé.")
    
    print("Superutilisateur créé avec succès:")
    print(f"  Username: admin")
    print(f"  Email: admin@example.com")
    print(f"  Password: admin123")
    print(f"  ID Employé: ADM001")
    print(f"  Rôle: Administrateur")

if __name__ == "__main__":
    create_admin_user()

