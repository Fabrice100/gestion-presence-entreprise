#!/usr/bin/env python
"""
Test du système de rapports
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

print("TEST DU SYSTÈME DE RAPPORTS")
print("=" * 50)

try:
    from django.test import Client
    from django.contrib.auth.models import User
    from reports.models import SystemSettings, ReportTemplate
    from accounts.models import EmployeeProfile, Department
    from attendance.models import Attendance, AttendanceAnomaly
    from leave.models import LeaveRequest, LeaveBalance, LeaveType
    
    client = Client()
    
    print("1. TEST DES MODÈLES DE RAPPORTS")
    print("-" * 30)
    
    total_settings = SystemSettings.objects.count()
    total_templates = ReportTemplate.objects.count()
    
    print(f"Paramètres système : {total_settings}")
    print(f"Templates de rapports : {total_templates}")
    
    print("\n2. TEST DES CONNEXIONS")
    print("-" * 30)
    
    users_to_test = [
        ('admin', 'admin123', 'Admin'),
        ('rh.dg', 'password123', 'RH/DG'),
        ('manager.it', 'password123', 'Manager'),
        ('dev1', 'password123', 'Employé'),
    ]
    
    for username, password, role in users_to_test:
        login_success = client.login(username=username, password=password)
        status = "OK" if login_success else "ECHEC"
        print(f"{role} ({username}): {status}")
        client.logout()
    
    print("\n3. TEST DES URLs DE RAPPORTS")
    print("-" * 30)
    
    # Test RH/DG (accès complet)
    client.login(username='rh.dg', password='password123')
    report_urls = [
        ('/reports/', 'Dashboard rapports'),
        ('/reports/attendance/', 'Rapport présence'),
        ('/reports/leave/', 'Rapport congés'),
        ('/reports/anomalies/', 'Rapport anomalies'),
        ('/reports/api/export/', 'API export'),
    ]
    
    for url, description in report_urls:
        response = client.get(url)
        status = "OK" if response.status_code == 200 else "ERREUR"
        print(f"{description}: {status} ({response.status_code})")
    
    client.logout()
    
    # Test Manager (accès limité)
    client.login(username='manager.it', password='password123')
    manager_urls = [
        ('/reports/', 'Dashboard rapports manager'),
        ('/reports/attendance/', 'Rapport présence équipe'),
        ('/reports/leave/', 'Rapport congés équipe'),
    ]
    
    for url, description in manager_urls:
        response = client.get(url)
        status = "OK" if response.status_code == 200 else "ERREUR"
        print(f"{description}: {status} ({response.status_code})")
    
    client.logout()
    
    # Test Employé (accès personnel)
    client.login(username='dev1', password='password123')
    employee_urls = [
        ('/reports/', 'Dashboard rapports employé'),
        ('/reports/attendance/', 'Rapport présence personnel'),
        ('/reports/leave/', 'Rapport congés personnel'),
    ]
    
    for url, description in employee_urls:
        response = client.get(url)
        status = "OK" if response.status_code == 200 else "ERREUR"
        print(f"{description}: {status} ({response.status_code})")
    
    client.logout()
    
    print("\n4. STATISTIQUES DES DONNÉES")
    print("-" * 30)
    
    total_employees = EmployeeProfile.objects.filter(is_active=True).count()
    total_departments = Department.objects.count()
    total_attendance = Attendance.objects.count()
    total_leave_requests = LeaveRequest.objects.count()
    total_anomalies = AttendanceAnomaly.objects.count()
    
    print(f"Employés actifs : {total_employees}")
    print(f"Départements : {total_departments}")
    print(f"Pointages : {total_attendance}")
    print(f"Demandes de congés : {total_leave_requests}")
    print(f"Anomalies : {total_anomalies}")
    
    print("\n5. TEST API EXPORT")
    print("-" * 30)
    
    client.login(username='rh.dg', password='password123')
    
    # Test export présence
    response = client.get('/reports/api/export/?type=attendance&format=pdf')
    if response.status_code == 200:
        print("Export présence PDF: OK")
    else:
        print(f"Export présence PDF: ERREUR ({response.status_code})")
    
    # Test export congés
    response = client.get('/reports/api/export/?type=leave&format=excel')
    if response.status_code == 200:
        print("Export congés Excel: OK")
    else:
        print(f"Export congés Excel: ERREUR ({response.status_code})")
    
    client.logout()
    
    print("\n6. VÉRIFICATION DES TEMPLATES")
    print("-" * 30)
    
    import os
    template_files = [
        'templates/reports/reports_dashboard.html',
        'templates/reports/attendance_report.html',
        'templates/reports/leave_report.html',
    ]
    
    for template_file in template_files:
        if os.path.exists(template_file):
            print(f"{template_file}: OK")
        else:
            print(f"{template_file}: MANQUANT")
    
    print("\n" + "=" * 50)
    print("TEST TERMINÉ")
    print("=" * 50)
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
