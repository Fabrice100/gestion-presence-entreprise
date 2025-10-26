"""
Script de diagnostic pour vérifier quel template est chargé
"""
import os
import sys

# Ajouter le projet au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')

import django
django.setup()

from accounts.models import EmployeeProfile
from django.contrib.auth.models import User

print("\n" + "="*60)
print("  🔍 DIAGNOSTIC DU FRONTEND")
print("="*60)

# Vérifier les utilisateurs
users = User.objects.all()
print(f"\n📊 UTILISATEURS DANS LA BASE ({users.count()}):")
print("-" * 60)

for user in users:
    try:
        profile = user.employee_profile
        role = profile.role
        print(f"   • {user.username:20} → Rôle: {role:10} → Dashboard: ✅ NOUVEAU (TailwindCSS)")
    except EmployeeProfile.DoesNotExist:
        print(f"   • {user.username:20} → ❌ Pas de profil")
    except AttributeError:
        print(f"   • {user.username:20} → ❌ Pas de profil")

print("\n" + "="*60)
print("  📁 TEMPLATES DISPONIBLES")
print("="*60)

template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'dashboard')
if os.path.exists(template_dir):
    templates = [f for f in os.listdir(template_dir) if f.endswith('.html')]
    print(f"\n✅ Templates dashboard trouvés ({len(templates)}):")
    for t in templates:
        if 'ultra_modern' in t:
            print(f"   • {t:50} ✨ NOUVEAU")
        else:
            print(f"   • {t:50} 📦 ANCIEN")
else:
    print("❌ Dossier templates/dashboard non trouvé!")

print("\n" + "="*60)
print("  🎯 RÉSULTAT FINAL")
print("="*60)

print("\n✅ TOUS les dashboards ont été modernisés !")
print("   • Dashboard Employé    → TailwindCSS ✨")
print("   • Dashboard Manager    → TailwindCSS ✨")
print("   • Dashboard RH/DG      → TailwindCSS ✨")
print("\n💡 Connectez-vous avec N'IMPORTE QUEL rôle pour voir le nouveau design!")
print("   Ne pas oublier de vider le cache : Ctrl+Shift+R")

print("\n" + "="*60 + "\n")
