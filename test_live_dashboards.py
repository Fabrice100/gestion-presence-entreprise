#!/usr/bin/env python
"""
Script pour tester en direct les templates chargés par les dashboards.
Simule une requête authentifiée pour chaque rôle.
"""

import os
import sys
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

def test_dashboard_rendering(username, password, role_name):
    """Teste le rendu du dashboard pour un utilisateur."""
    print(f"\n{'='*70}")
    print(f"  TEST: Dashboard {role_name} - Utilisateur: {username}")
    print(f"{'='*70}")
    
    try:
        # Crée un client de test
        client = Client()
        
        # Connexion
        print(f"📝 Connexion en cours...")
        login_response = client.post(
            reverse('login'),
            {'username': username, 'password': password},
            follow=False
        )
        
        if login_response.status_code != 302:
            print(f"❌ Échec connexion: Code {login_response.status_code}")
            return False
        
        print(f"✅ Connexion réussie (redirect {login_response.status_code})")
        
        # Accède au dashboard
        print(f"🌐 Accès au dashboard...")
        dashboard_response = client.get(reverse('dashboard:dashboard'), follow=True)
        
        print(f"📄 Code HTTP: {dashboard_response.status_code}")
        
        if dashboard_response.status_code != 200:
            print(f"❌ Erreur dashboard: Code {dashboard_response.status_code}")
            return False
        
        # Vérifie le template utilisé
        templates_used = [t.name for t in dashboard_response.templates if t.name]
        
        print(f"\n📑 Templates chargés ({len(templates_used)}):")
        for i, template in enumerate(templates_used, 1):
            is_modern = 'ultra_modern' in template
            status = "✅ MODERNE" if is_modern else "⚠️  ANCIEN"
            print(f"  {i}. {template}")
            print(f"     {status}")
        
        # Vérifie le contenu
        content = dashboard_response.content.decode('utf-8')
        
        print(f"\n🔍 Vérification du contenu:")
        
        checks = {
            'TailwindCSS': 'tailwindcss.com' in content or 'cdn.tailwindcss.com' in content,
            'Alpine.js': 'alpinejs' in content or 'Alpine.start' in content,
            'Chart.js': 'chart.js' in content or 'chartjs' in content,
            'Bootstrap (ancien)': 'bootstrap' in content.lower() and 'cdn.jsdelivr.net/npm/bootstrap' in content,
            'Base ultra-moderne': 'base_ultra_modern' in ' '.join(templates_used),
        }
        
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
        
        # Verdict
        is_modern = checks['TailwindCSS'] and not checks['Bootstrap (ancien)']
        
        print(f"\n🎯 VERDICT:")
        if is_modern:
            print(f"  ✅ Dashboard MODERNE (TailwindCSS)")
        else:
            print(f"  ❌ Dashboard ANCIEN (Bootstrap)")
            print(f"\n  🔧 PROBLÈME IDENTIFIÉ:")
            print(f"     Le template ultra_modern n'est PAS chargé")
            print(f"     Vérifiez la configuration de la vue Django")
        
        return is_modern
        
    except Exception as e:
        print(f"❌ ERREUR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║      TEST EN DIRECT - DASHBOARDS APRÈS CONNEXION                    ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    # Comptes à tester
    tests = [
        ('EMP001', 'password123', 'Employé'),
        ('manager.it', 'password123', 'Manager'),
        ('rh.dg', 'password123', 'RH/DG'),
    ]
    
    results = []
    
    for username, password, role in tests:
        success = test_dashboard_rendering(username, password, role)
        results.append((role, success))
    
    # Résumé final
    print(f"\n{'='*70}")
    print(f"  RÉSUMÉ FINAL")
    print(f"{'='*70}\n")
    
    for role, is_modern in results:
        status = "✅ MODERNE" if is_modern else "❌ ANCIEN"
        print(f"  {role:20} {status}")
    
    all_modern = all(is_modern for _, is_modern in results)
    
    if all_modern:
        print(f"\n  ✅ TOUS LES DASHBOARDS SONT MODERNES !")
        print(f"  ➡️  Si vous voyez encore l'ancien, videz le cache")
    else:
        print(f"\n  ❌ CERTAINS DASHBOARDS SONT ENCORE ANCIENS")
        print(f"  ➡️  Vérifiez la configuration des vues Django")
        print(f"\n  📝 Fichier à vérifier:")
        print(f"     accounts/dashboard_views.py")
        print(f"     Lignes template_name doivent pointer vers *_ultra_modern.html")
    
    print("\n")

if __name__ == '__main__':
    main()
