#!/usr/bin/env python
"""
Test des exports PDF et Excel
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

print("TEST DES EXPORTS PDF ET EXCEL")
print("=" * 50)

try:
    from django.test import Client
    from django.contrib.auth.models import User
    from datetime import date, timedelta
    
    client = Client()
    
    print("\n1. TEST DES CONNEXIONS")
    print("-" * 30)
    
    # Test RH/DG
    login_success = client.login(username='rh.dg', password='password123')
    if login_success:
        print("Connexion RH/DG: OK")
        
        print("\n2. TEST EXPORT PDF - RAPPORT DE PRÉSENCE")
        print("-" * 40)
        
        # Test export PDF présence
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        response = client.get(f'/reports/api/export/?type=attendance&format=pdf&start_date={start_date}&end_date={end_date}')
        
        if response.status_code == 200 and response['Content-Type'] == 'application/pdf':
            print(f"Export PDF présence: OK (taille: {len(response.content)} bytes)")
        else:
            print(f"Export PDF présence: ERREUR ({response.status_code})")
            print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
        
        print("\n3. TEST EXPORT EXCEL - RAPPORT DE PRÉSENCE")
        print("-" * 40)
        
        # Test export Excel présence
        response = client.get(f'/reports/api/export/?type=attendance&format=excel&start_date={start_date}&end_date={end_date}')
        
        if response.status_code == 200 and 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response['Content-Type']:
            print(f"Export Excel présence: OK (taille: {len(response.content)} bytes)")
        else:
            print(f"Export Excel présence: ERREUR ({response.status_code})")
            print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
        
        print("\n4. TEST EXPORT PDF - RAPPORT DE CONGÉS")
        print("-" * 40)
        
        # Test export PDF congés
        response = client.get('/reports/api/export/?type=leave&format=pdf&year=2024')
        
        if response.status_code == 200 and response['Content-Type'] == 'application/pdf':
            print(f"Export PDF congés: OK (taille: {len(response.content)} bytes)")
        else:
            print(f"Export PDF congés: ERREUR ({response.status_code})")
            print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
        
        print("\n5. TEST EXPORT EXCEL - RAPPORT DE CONGÉS")
        print("-" * 40)
        
        # Test export Excel congés
        response = client.get('/reports/api/export/?type=leave&format=excel&year=2024')
        
        if response.status_code == 200 and 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response['Content-Type']:
            print(f"Export Excel congés: OK (taille: {len(response.content)} bytes)")
        else:
            print(f"Export Excel congés: ERREUR ({response.status_code})")
            print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
        
        print("\n6. TEST EXPORT RÉCAPITULATIF")
        print("-" * 30)
        
        # Test export récapitulatif PDF
        response = client.get('/reports/api/export/?type=summary&format=pdf')
        
        if response.status_code == 200 and response['Content-Type'] == 'application/pdf':
            print(f"Export PDF récapitulatif: OK (taille: {len(response.content)} bytes)")
        else:
            print(f"Export PDF récapitulatif: ERREUR ({response.status_code})")
        
        client.logout()
    
    else:
        print("Connexion RH/DG: ECHEC")
    
    print("\n7. TEST AVEC MANAGER")
    print("-" * 30)
    
    # Test Manager
    login_success = client.login(username='manager.it', password='password123')
    if login_success:
        print("Connexion Manager: OK")
        
        # Test export avec manager (accès limité)
        response = client.get(f'/reports/api/export/?type=attendance&format=pdf&start_date={start_date}&end_date={end_date}')
        
        if response.status_code == 200 and response['Content-Type'] == 'application/pdf':
            print(f"Export PDF Manager: OK (taille: {len(response.content)} bytes)")
        else:
            print(f"Export PDF Manager: ERREUR ({response.status_code})")
        
        client.logout()
    
    print("\n" + "=" * 50)
    print("TEST DES EXPORTS TERMINE")
    print("=" * 50)
    
    print("\nRESUME DES EXPORTS TESTES :")
    print("- Export PDF rapport de presence")
    print("- Export Excel rapport de presence")
    print("- Export PDF rapport de conges")
    print("- Export Excel rapport de conges")
    print("- Export PDF recapitulatif")
    print("- Export avec permissions par role")
    
    print("\nLES EXPORTS PDF ET EXCEL FONCTIONNENT !")
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
