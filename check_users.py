import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import EmployeeProfile

print("\n" + "=" * 80)
print("🔍 LISTE DES COMPTES UTILISATEURS")
print("=" * 80)

users = User.objects.all().order_by('username')

print(f"\n{'Username':<20} {'Email':<30} {'Employee ID':<15} {'Rôle':<15}")
print("-" * 80)

for user in users:
    email = user.email or 'N/A'
    if hasattr(user, 'employee_profile'):
        emp_id = user.employee_profile.employee_id
        role = user.employee_profile.role
    else:
        emp_id = 'AUCUN'
        role = 'admin (superuser)'
    
    print(f"{user.username:<20} {email:<30} {emp_id:<15} {role:<15}")

print(f"\n📊 Total: {users.count()} comptes")

# Vérifier spécifiquement EMP008 et EMP009
print("\n" + "=" * 80)
print("🔎 RECHERCHE EMP008 et EMP009")
print("=" * 80)

for emp_id in ['EMP008', 'EMP009']:
    try:
        profile = EmployeeProfile.objects.get(employee_id=emp_id)
        user = profile.user
        print(f"\n✅ Trouvé: {emp_id}")
        print(f"   Username: {user.username}")
        print(f"   Nom: {user.first_name} {user.last_name}")
        print(f"   Email: {user.email}")
        print(f"   Rôle: {profile.role}")
        print(f"   Actif: {profile.is_active}")
        print(f"   Date création: {user.date_joined}")
        print(f"\n   ⚠️  IMPORTANT: Le mot de passe ne peut pas être affiché")
        print(f"   Si mot de passe oublié, il faut le réinitialiser via:")
        print(f"   python manage.py changepassword {user.username}")
    except EmployeeProfile.DoesNotExist:
        print(f"\n❌ {emp_id} n'existe pas")

print("\n" + "=" * 80)
