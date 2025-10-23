"""
Script de test pour l'interface RH de correction des anomalies.

Ce script :
1. Crée un groupe RH
2. Crée un utilisateur RH
3. Crée des anomalies de test (oublis de sortie)
4. Affiche les URLs d'accès

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User, Group
from accounts.models import EmployeeProfile
from attendance.models import Attendance, AttendanceAnomaly
from datetime import datetime, date, time, timedelta
from decimal import Decimal

def create_rh_test_data():
    """Crée les données de test pour l'interface RH."""
    
    print("=" * 70)
    print("CRÉATION DES DONNÉES DE TEST - INTERFACE RH")
    print("=" * 70)
    
    # 1. Créer le groupe RH
    print("\n[1/5] Création du groupe RH...")
    rh_group, created = Group.objects.get_or_create(name='RH')
    if created:
        print("   ✓ Groupe 'RH' créé")
    else:
        print("   → Groupe 'RH' existe déjà")
    
    # 2. Créer un utilisateur RH
    print("\n[2/5] Création d'un utilisateur RH...")
    
    # Vérifier si l'utilisateur existe déjà
    try:
        rh_user = User.objects.get(username='rh_test')
        print("   → Utilisateur RH existe déjà: rh_test")
        created = False
    except User.DoesNotExist:
        # Créer manuellement
        rh_user = User(
            username='rh_test',
            email='rh@entreprise.com',
            first_name='Marie',
            last_name='RH',
            is_staff=True
        )
        rh_user.set_password('rh123')
        rh_user.save()
        print("   ✓ Utilisateur RH créé: rh_test / rh123")
        created = True
    
    # Ajouter au groupe RH
    if not rh_user.groups.filter(name='RH').exists():
        rh_user.groups.add(rh_group)
        print("   ✓ Utilisateur ajouté au groupe RH")
    
    # 3. Créer des employés de test avec anomalies
    print("\n[3/5] Création d'employés avec anomalies...")
    
    employees_data = [
        {'username': 'jean_test', 'first_name': 'Jean', 'last_name': 'Dupont', 'in_time': '08:00'},
        {'username': 'marie_test', 'first_name': 'Marie', 'last_name': 'Martin', 'in_time': '09:00'},
        {'username': 'pierre_test', 'first_name': 'Pierre', 'last_name': 'Bernard', 'in_time': '08:30'},
    ]
    
    anomalies_created = []
    
    for emp_data in employees_data:
        # Créer l'utilisateur
        try:
            user = User.objects.get(username=emp_data['username'])
            user_created = False
        except User.DoesNotExist:
            user = User(
                username=emp_data['username'],
                email=f"{emp_data['username']}@entreprise.com",
                first_name=emp_data['first_name'],
                last_name=emp_data['last_name']
            )
            user.set_password('test123')
            user.save()
            print(f"   ✓ Employé créé: {emp_data['first_name']} {emp_data['last_name']}")
            user_created = True
        
        # Créer le profil employé
        profile, profile_created = EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'employee_id': f'EMP{user.id:04d}',
                'department': 'Test',
                'position': 'Employé Test',
                'can_punch': True
            }
        )
        
        # Créer un pointage avec oubli de sortie (hier)
        yesterday = date.today() - timedelta(days=1)
        
        attendance, att_created = Attendance.objects.get_or_create(
            employee=profile,
            date=yesterday,
            punch_type='in',
            defaults={
                'punch_in_time': datetime.strptime(emp_data['in_time'], '%H:%M').time(),
                'latitude': Decimal('48.8566'),
                'longitude': Decimal('2.3522'),
                'accuracy': Decimal('20.00'),
                'status': 'missing_out'
            }
        )
        
        if att_created:
            # Créer l'anomalie
            anomaly, anom_created = AttendanceAnomaly.objects.get_or_create(
                attendance=attendance,
                anomaly_type='missing_punch_out',
                defaults={
                    'description': f'Oubli de sortie le {yesterday.strftime("%d/%m/%Y")} - Entrée à {emp_data["in_time"]}',
                    'severity': 'medium',
                    'status': 'pending'
                }
            )
            
            if anom_created:
                anomalies_created.append({
                    'employee': f"{emp_data['first_name']} {emp_data['last_name']}",
                    'date': yesterday,
                    'in_time': emp_data['in_time']
                })
    
    print(f"\n   ✓ {len(anomalies_created)} anomalies créées")
    
    # 4. Afficher les statistiques
    print("\n[4/5] Statistiques...")
    total_pending = AttendanceAnomaly.objects.filter(
        anomaly_type='missing_punch_out',
        status='pending'
    ).count()
    print(f"   → Total anomalies en attente: {total_pending}")
    
    # 5. Afficher les informations de connexion
    print("\n[5/5] Informations de connexion")
    print("=" * 70)
    print("\n🔐 COMPTE RH:")
    print(f"   Username: rh_test")
    print(f"   Password: rh123")
    print(f"\n📊 INTERFACE RH:")
    print(f"   URL: http://localhost:8000/attendance/rh/anomalies/")
    print(f"\n👥 ANOMALIES CRÉÉES:")
    for anom in anomalies_created:
        print(f"   - {anom['employee']} | {anom['date'].strftime('%d/%m/%Y')} | Entrée: {anom['in_time']}")
    
    print("\n" + "=" * 70)
    print("✅ DONNÉES DE TEST CRÉÉES AVEC SUCCÈS !")
    print("=" * 70)
    print("\n📝 PROCHAINES ÉTAPES:")
    print("   1. Démarrer le serveur: python manage.py runserver")
    print("   2. Se connecter avec: rh_test / rh123")
    print("   3. Accéder à: http://localhost:8000/attendance/rh/anomalies/")
    print("   4. Tester la correction des anomalies")
    print("=" * 70)

if __name__ == '__main__':
    create_rh_test_data()
