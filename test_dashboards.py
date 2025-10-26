#!/usr/bin/env python
"""
Script de test pour identifier les erreurs dans les dashboards.
"""

import os
import sys
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')

import django
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from accounts.dashboard_views import EmployeeDashboardView, ManagerDashboardView, RhDgDashboardView

User = get_user_model()

def test_dashboard_view(username, view_class, view_name):
    """Teste une vue de dashboard."""
    print(f"\n{'='*70}")
    print(f"  TEST: {view_name} pour {username}")
    print(f"{'='*70}")
    
    try:
        # Récupère l'utilisateur
        user = User.objects.get(username=username)
        print(f"✅ Utilisateur trouvé: {user.get_full_name() or user.email}")
        
        # Crée une requête simulée
        factory = RequestFactory()
        request = factory.get(f'/dashboard/{username}/')
        request.user = user
        
        # Crée une instance de la vue
        view = view_class()
        view.request = request
        view.args = ()
        view.kwargs = {}
        
        # Teste get_context_data
        print(f"📊 Test get_context_data()...")
        context = view.get_context_data()
        
        print(f"✅ Context récupéré avec {len(context)} éléments")
        
        # Affiche les clés du contexte
        print(f"\n  Clés du contexte:")
        for key in sorted(context.keys()):
            value = context[key]
            value_type = type(value).__name__
            if hasattr(value, '__len__') and not isinstance(value, str):
                print(f"    - {key}: {value_type} ({len(value)} éléments)")
            else:
                print(f"    - {key}: {value_type}")
        
        # Teste le template
        print(f"\n📄 Template configuré: {view.template_name}")
        template_path = Path('templates') / view.template_name
        if template_path.exists():
            print(f"✅ Template existe ({template_path.stat().st_size:,} octets)")
        else:
            print(f"❌ Template MANQUANT: {template_path}")
        
        return True
        
    except User.DoesNotExist:
        print(f"❌ Utilisateur '{username}' non trouvé")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {type(e).__name__}: {e}")
        import traceback
        print("\nTraceback complet:")
        traceback.print_exc()
        return False

def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║        TEST DES DASHBOARDS - IDENTIFICATION DES ERREURS              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    tests = [
        ('dev1', EmployeeDashboardView, 'Dashboard Employé'),
        ('manager.it', ManagerDashboardView, 'Dashboard Manager'),
        ('rh.dg', RhDgDashboardView, 'Dashboard RH/DG'),
    ]
    
    results = []
    
    for username, view_class, view_name in tests:
        success = test_dashboard_view(username, view_class, view_name)
        results.append((view_name, success))
    
    # Résumé
    print(f"\n{'='*70}")
    print(f"  RÉSUMÉ DES TESTS")
    print(f"{'='*70}\n")
    
    for view_name, success in results:
        status = "✅ OK" if success else "❌ ÉCHEC"
        print(f"  {view_name:30} {status}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        print(f"\n  ✅ TOUS LES DASHBOARDS FONCTIONNENT")
        print(f"  ➡️  Le serveur devrait démarrer sans erreur")
    else:
        print(f"\n  ❌ CERTAINS DASHBOARDS ONT DES ERREURS")
        print(f"  ➡️  Corrigez les erreurs ci-dessus avant de redémarrer")
    
    print("\n")

if __name__ == '__main__':
    main()
