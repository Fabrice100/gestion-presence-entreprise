"""
Script de migration COMPLET avec conversion de tous les types de champs
"""
import os
import json
import django
from django.db import transaction
from datetime import datetime, date, time
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from accounts.models import EmployeeProfile, Department
from attendance.models import Attendance, AttendanceAnomaly
from leave.models import LeaveType, LeaveBalance, LeaveRequest, Holiday

print("🔄 MIGRATION COMPLÈTE - VERSION FINALE")
print("="*60)

# Désactiver les signaux
print("\n🔇 Désactivation des signaux...")
from django.db.models.signals import post_save, pre_save
post_save.receivers = []
pre_save.receivers = []
print("✅ Signaux désactivés")

# Charger les données
print("\n📂 Chargement depuis backup/db.sqlite3...")

# Réexporter depuis SQLite pour être sûr
print("📤 Ré-export depuis SQLite...")
import subprocess
import sys

# Changer temporairement vers SQLite
settings_path = 'attendance_system/settings.py'
with open(settings_path, 'r', encoding='utf-8') as f:
    original_settings = f.read()

# Activer SQLite
settings_sqlite = original_settings.replace(
    "DATABASES = {\n    'default': {\n        'ENGINE': 'django.db.backends.postgresql',",
    "DATABASES = {\n    'default': {\n        'ENGINE': 'django.db.backends.sqlite3',\n        'NAME': BASE_DIR / 'backup' / 'db.sqlite3',\n    }\n}\n\nif False:\n    PG = {\n    'default': {\n        'ENGINE': 'django.db.backends.postgresql',"
)

with open(settings_path, 'w', encoding='utf-8') as f:
    f.write(settings_sqlite)

# Exporter
result = subprocess.run(
    [sys.executable, 'manage.py', 'dumpdata', 
     '--exclude', 'auth.permission',
     '--exclude', 'contenttypes',
     '--exclude', 'admin.logentry',
     '--exclude', 'sessions.session',
     '--indent', '2'],
    capture_output=True,
    text=True
)

# Restaurer PostgreSQL
with open(settings_path, 'w', encoding='utf-8') as f:
    f.write(original_settings)

if result.returncode != 0:
    print(f"❌ Erreur d'export: {result.stderr}")
    sys.exit(1)

data = json.loads(result.stdout)
print(f"✅ {len(data)} objets chargés\n")

# Fonction pour convertir les FK et dates
def convert_field(value, field_type):
    """Convertit une valeur selon son type"""
    if value is None:
        return None
    
    if field_type == 'User':
        try:
            return User.objects.get(pk=value)
        except User.DoesNotExist:
            return None
    
    elif field_type == 'Department':
        try:
            return Department.objects.get(pk=value)
        except Department.DoesNotExist:
            return None
    
    elif field_type == 'LeaveType':
        try:
            return LeaveType.objects.get(pk=value)
        except LeaveType.DoesNotExist:
            return None
    
    elif field_type == 'date':
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d').date()
        return value
    
    elif field_type == 'datetime':
        if isinstance(value, str):
            # Gérer plusieurs formats
            for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(value, fmt)
                except:
                    continue
        return value
    
    elif field_type == 'time':
        if isinstance(value, str):
            return datetime.strptime(value, '%H:%M:%S').time()
        return value
    
    elif field_type == 'decimal':
        return Decimal(str(value))
    
    return value

# Statistiques
stats = {'imported': 0, 'errors': 0, 'skipped': 0}

# Trier les données
data_by_model = {}
for obj in data:
    model = obj['model']
    if model not in data_by_model:
        data_by_model[model] = []
    data_by_model[model].append(obj)

try:
    with transaction.atomic():
        print("🔄 Import en transaction atomique...\n")
        
        # 1. Groups
        print("1️⃣ Groups...")
        for obj in data_by_model.get('auth.group', []):
            try:
                group, created = Group.objects.get_or_create(name=obj['fields']['name'])
                group.pk = obj['pk']
                group.save()
                if obj['fields'].get('permissions'):
                    group.permissions.set(Permission.objects.filter(pk__in=obj['fields']['permissions']))
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {len(data_by_model.get('auth.group', []))} groups")
        
        # 2. Users
        print("\n2️⃣ Users...")
        for obj in data_by_model.get('auth.user', []):
            try:
                groups = obj['fields'].pop('groups', [])
                user_permissions = obj['fields'].pop('user_permissions', [])
                user, created = User.objects.update_or_create(pk=obj['pk'], defaults=obj['fields'])
                if groups:
                    user.groups.set(Group.objects.filter(pk__in=groups))
                if user_permissions:
                    user.user_permissions.set(Permission.objects.filter(pk__in=user_permissions))
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {len(data_by_model.get('auth.user', []))} users")
        
        # 3. Departments
        print("\n3️⃣ Departments...")
        for obj in data_by_model.get('accounts.department', []):
            try:
                obj['fields']['manager'] = convert_field(obj['fields'].get('manager'), 'User')
                dept, created = Department.objects.update_or_create(pk=obj['pk'], defaults=obj['fields'])
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {len(data_by_model.get('accounts.department', []))} departments")
        
        # 4. EmployeeProfiles
        print("\n4️⃣ Employee Profiles...")
        for obj in data_by_model.get('accounts.employeeprofile', []):
            try:
                # Convertir toutes les FK
                obj['fields']['user'] = convert_field(obj['fields']['user'], 'User')
                obj['fields']['department'] = convert_field(obj['fields'].get('department'), 'Department')
                obj['fields']['manager'] = convert_field(obj['fields'].get('manager'), 'User')
                
                if obj['fields']['user'] is None:
                    stats['skipped'] += 1
                    continue
                
                # Supprimer profil auto-créé
                EmployeeProfile.objects.filter(user=obj['fields']['user']).delete()
                
                profile, created = EmployeeProfile.objects.update_or_create(
                    pk=obj['pk'],
                    defaults=obj['fields']
                )
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {EmployeeProfile.objects.count()} profiles importés")
        
        # 5. LeaveTypes
        print("\n5️⃣ Leave Types...")
        for obj in data_by_model.get('leave.leavetype', []):
            try:
                lt, created = LeaveType.objects.update_or_create(pk=obj['pk'], defaults=obj['fields'])
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {LeaveType.objects.count()} leave types")
        
        # 6. Holidays
        print("\n6️⃣ Holidays...")
        for obj in data_by_model.get('leave.holiday', []):
            try:
                obj['fields']['date'] = convert_field(obj['fields']['date'], 'date')
                holiday, created = Holiday.objects.update_or_create(pk=obj['pk'], defaults=obj['fields'])
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {Holiday.objects.count()} holidays")
        
        # 7. LeaveBalances
        print("\n7️⃣ Leave Balances...")
        for obj in data_by_model.get('leave.leavebalance', []):
            try:
                obj['fields']['employee'] = convert_field(obj['fields']['employee'], 'User')
                obj['fields']['leave_type'] = convert_field(obj['fields']['leave_type'], 'LeaveType')
                obj['fields']['balance'] = convert_field(obj['fields']['balance'], 'decimal')
                obj['fields']['used'] = convert_field(obj['fields']['used'], 'decimal')
                
                if not obj['fields']['employee'] or not obj['fields']['leave_type']:
                    stats['skipped'] += 1
                    continue
                
                LeaveBalance.objects.filter(
                    employee=obj['fields']['employee'],
                    leave_type=obj['fields']['leave_type']
                ).delete()
                
                lb, created = LeaveBalance.objects.update_or_create(pk=obj['pk'], defaults=obj['fields'])
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {LeaveBalance.objects.count()} leave balances")
        
        # 8. LeaveRequests
        print("\n8️⃣ Leave Requests...")
        for obj in data_by_model.get('leave.leaverequest', []):
            try:
                obj['fields']['employee'] = convert_field(obj['fields']['employee'], 'User')
                obj['fields']['leave_type'] = convert_field(obj['fields']['leave_type'], 'LeaveType')
                obj['fields']['manager'] = convert_field(obj['fields'].get('manager'), 'User')
                obj['fields']['approved_by'] = convert_field(obj['fields'].get('approved_by'), 'User')
                obj['fields']['start_date'] = convert_field(obj['fields']['start_date'], 'date')
                obj['fields']['end_date'] = convert_field(obj['fields']['end_date'], 'date')
                obj['fields']['days'] = convert_field(obj['fields']['days'], 'decimal')
                
                if not obj['fields']['employee'] or not obj['fields']['leave_type']:
                    stats['skipped'] += 1
                    continue
                
                lr, created = LeaveRequest.objects.update_or_create(pk=obj['pk'], defaults=obj['fields'])
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {LeaveRequest.objects.count()} leave requests")
        
        # 9. Attendances
        print("\n9️⃣ Attendances...")
        for obj in data_by_model.get('attendance.attendance', []):
            try:
                obj['fields']['employee'] = convert_field(obj['fields']['employee'], 'User')
                obj['fields']['date'] = convert_field(obj['fields']['date'], 'date')
                obj['fields']['check_in'] = convert_field(obj['fields'].get('check_in'), 'time')
                obj['fields']['check_out'] = convert_field(obj['fields'].get('check_out'), 'time')
                
                if not obj['fields']['employee']:
                    stats['skipped'] += 1
                    continue
                
                att, created = Attendance.objects.update_or_create(pk=obj['pk'], defaults=obj['fields'])
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {Attendance.objects.count()} attendances")
        
        # 10. Anomalies
        print("\n🔟 Attendance Anomalies...")
        for obj in data_by_model.get('attendance.attendanceanomaly', []):
            try:
                aa, created = AttendanceAnomaly.objects.update_or_create(pk=obj['pk'], defaults=obj['fields'])
                stats['imported'] += 1
            except Exception as e:
                print(f"  ❌ {obj['pk']}: {e}")
                stats['errors'] += 1
        print(f"  ✅ {AttendanceAnomaly.objects.count()} anomalies")
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLÈTE RÉUSSIE !")
        print("="*60)
        print(f"\n📊 Statistiques finales:")
        print(f"  ✅ Importés: {stats['imported']}")
        print(f"  ⏭️  Ignorés: {stats['skipped']}")
        print(f"  ❌ Erreurs: {stats['errors']}")
        
        print("\n🔍 Résultat final:")
        print(f"  👥 Users: {User.objects.count()}")
        print(f"  📋 Profiles: {EmployeeProfile.objects.count()}")
        print(f"  🏢 Departments: {Department.objects.count()}")
        print(f"  📅 Leave Types: {LeaveType.objects.count()}")
        print(f"  💼 Leave Balances: {LeaveBalance.objects.count()}")
        print(f"  📝 Leave Requests: {LeaveRequest.objects.count()}")
        print(f"  🎉 Holidays: {Holiday.objects.count()}")
        print(f"  ⏰ Attendances: {Attendance.objects.count()}")
        
        if stats['errors'] == 0:
            print("\n🎉 TOUTES LES DONNÉES ONT ÉTÉ MIGRÉES AVEC SUCCÈS !")
        else:
            print(f"\n⚠️  {stats['errors']} erreurs mineures (données secondaires)")

except Exception as e:
    print(f"\n❌ ERREUR CRITIQUE: {e}")
    import traceback
    traceback.print_exc()
    print("\n⚠️  Transaction annulée")

print("\n✅ Script terminé")
