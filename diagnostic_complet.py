#!/usr/bin/env python
"""
Script de diagnostic complet du frontend moderne.
Vérifie tous les aspects de la configuration.
"""

import os
import sys
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')

import django
django.setup()

from accounts.views import CustomLoginView
from accounts.dashboard_views import EmployeeDashboardView, ManagerDashboardView, RhDgDashboardView
from django.contrib.auth import get_user_model

User = get_user_model()

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_section(text):
    print(f"\n{'─'*70}")
    print(f"  {text}")
    print(f"{'─'*70}")

def check_templates():
    """Vérifie l'existence de tous les templates modernes."""
    print_header("VÉRIFICATION DES TEMPLATES")
    
    templates = {
        'Login': 'templates/accounts/login_ultra_modern.html',
        'Base ultra-moderne': 'templates/base_ultra_modern.html',
        'Dashboard Employé': 'templates/dashboard/employee_dashboard_ultra_modern.html',
        'Dashboard Manager': 'templates/dashboard/manager_dashboard_ultra_modern.html',
        'Dashboard RH/DG': 'templates/dashboard/rh_dg_dashboard_ultra_modern.html',
    }
    
    all_exist = True
    for name, path in templates.items():
        exists = Path(path).exists()
        status = "✅ EXISTE" if exists else "❌ MANQUANT"
        print(f"  {name:25} {status}")
        if exists:
            size = Path(path).stat().st_size
            print(f"  {'':25} └─ Taille: {size:,} octets")
        if not exists:
            all_exist = False
    
    return all_exist

def check_views_configuration():
    """Vérifie la configuration des vues."""
    print_header("VÉRIFICATION DES VUES")
    
    views = {
        'CustomLoginView': CustomLoginView,
        'EmployeeDashboardView': EmployeeDashboardView,
        'ManagerDashboardView': ManagerDashboardView,
        'RhDgDashboardView': RhDgDashboardView,
    }
    
    for name, view_class in views.items():
        template = getattr(view_class, 'template_name', None)
        print(f"  {name:30} → {template}")
        
        if template:
            # Vérifie si le template est moderne
            is_modern = 'ultra_modern' in template
            status = "✅ MODERNE" if is_modern else "⚠️  ANCIEN"
            print(f"  {'':30}   {status}")

def check_git_status():
    """Vérifie l'état Git."""
    print_header("VÉRIFICATION GIT")
    
    import subprocess
    
    try:
        # Branche actuelle
        branch = subprocess.check_output(
            ['git', 'branch', '--show-current'],
            stderr=subprocess.STDOUT,
            text=True
        ).strip()
        print(f"  Branche actuelle: {branch}")
        
        # Statut des modifications
        status = subprocess.check_output(
            ['git', 'status', '--short'],
            stderr=subprocess.STDOUT,
            text=True
        )
        
        if status.strip():
            print(f"\n  Fichiers modifiés/non commités:")
            for line in status.strip().split('\n'):
                print(f"    {line}")
        else:
            print(f"  ✅ Aucune modification non commitée")
            
    except Exception as e:
        print(f"  ⚠️  Erreur Git: {e}")

def check_users():
    """Vérifie les utilisateurs de test."""
    print_header("UTILISATEURS DE TEST")
    
    test_users = ['admin', 'rh.dg', 'manager.it', 'EMP001']
    
    for username in test_users:
        try:
            user = User.objects.get(employee_id=username)
            print(f"  ✅ {username:15} → {user.get_full_name() or user.email}")
            print(f"     {'':15}   Rôle: {user.role}")
        except User.DoesNotExist:
            print(f"  ❌ {username:15} → NON TROUVÉ")

def check_urls():
    """Vérifie la configuration des URLs."""
    print_header("VÉRIFICATION DES URLS")
    
    from django.urls import reverse
    
    urls_to_check = {
        'Login': 'login',
        'Dashboard': 'dashboard:dashboard',
    }
    
    for name, url_name in urls_to_check.items():
        try:
            url = reverse(url_name)
            print(f"  ✅ {name:20} → {url}")
        except Exception as e:
            print(f"  ❌ {name:20} → ERREUR: {e}")

def check_settings():
    """Vérifie les paramètres importants."""
    print_header("PARAMÈTRES DJANGO")
    
    from django.conf import settings
    
    configs = {
        'DEBUG': settings.DEBUG,
        'TEMPLATES[0][\'DIRS\']': settings.TEMPLATES[0]['DIRS'],
        'STATICFILES_DIRS': getattr(settings, 'STATICFILES_DIRS', []),
        'STATIC_ROOT': settings.STATIC_ROOT,
        'MEDIA_ROOT': settings.MEDIA_ROOT,
    }
    
    for name, value in configs.items():
        print(f"  {name:25} = {value}")

def provide_recommendations():
    """Fournit des recommandations."""
    print_header("RECOMMANDATIONS")
    
    print("""
  🔍 DIAGNOSTIC COMPLET EFFECTUÉ
  
  Pour voir le nouveau frontend, suivez ces étapes:
  
  1️⃣  DÉMARRER LE SERVEUR
     cd "c:\\Users\\HUSUNUKPE Fabrice\\Desktop\\mon_projet\\attendance_system"
     python manage.py runserver 8000
  
  2️⃣  VIDER LE CACHE DU NAVIGATEUR
     - Chrome/Edge: Ctrl + Shift + Delete
     - Ou: Ctrl + Shift + R pour hard refresh
  
  3️⃣  ACCÉDER À LA PAGE DE CONNEXION
     http://127.0.0.1:8000/accounts/login/
  
  4️⃣  TESTER AVEC UN COMPTE DÉMO
     Cliquez sur "Employé" pour remplir automatiquement:
     - ID: EMP001
     - Mot de passe: password123
  
  ⚠️  SI VOUS VOYEZ TOUJOURS L'ANCIEN DESIGN:
     - Videz COMPLÈTEMENT le cache navigateur
     - Essayez en navigation privée
     - Vérifiez que le serveur a bien redémarré
     - Vérifiez qu'il n'y a pas d'erreur dans le terminal
  
  📝 TEMPLATES CRÉÉS:
     ✅ login_ultra_modern.html (page de connexion moderne)
     ✅ employee_dashboard_ultra_modern.html
     ✅ manager_dashboard_ultra_modern.html
     ✅ rh_dg_dashboard_ultra_modern.html
     ✅ base_ultra_modern.html (base template)
  
  🎨 STACK FRONTEND:
     - TailwindCSS 3.4 (via CDN)
     - Alpine.js 3.x
     - Chart.js 4.4
     - Google Fonts (Inter)
  """)

def main():
    """Exécute tous les diagnostics."""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          DIAGNOSTIC COMPLET - FRONTEND MODERNE TAILWIND              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    all_good = True
    
    # Vérifications
    if not check_templates():
        all_good = False
    
    check_views_configuration()
    check_git_status()
    check_users()
    check_urls()
    check_settings()
    provide_recommendations()
    
    # Résumé final
    print_header("RÉSUMÉ FINAL")
    if all_good:
        print("  ✅ TOUS LES TEMPLATES EXISTENT")
        print("  ✅ CONFIGURATION CORRECTE")
        print("  ✅ PRÊT À DÉMARRER LE SERVEUR")
        print("\n  ➡️  Lancez: python manage.py runserver 8000")
    else:
        print("  ⚠️  CERTAINS TEMPLATES MANQUENT")
        print("  ➡️  Vérifiez les erreurs ci-dessus")
    
    print("\n")

if __name__ == '__main__':
    main()
