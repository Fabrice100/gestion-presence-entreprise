"""
Commande de gestion Django pour initialiser la configuration Togo.

Cette commande :
1. Charge les types de congés légaux du Togo
2. Charge les jours fériés 2025
3. Crée les soldes de congés pour tous les utilisateurs existants

Usage:
    python manage.py init_togo_setup
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from datetime import date

from leave.models import LeaveBalance, LeaveType
from accounts.models import EmployeeProfile


class Command(BaseCommand):
    help = 'Initialise la configuration Togo (types de congés, jours fériés, soldes)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== INITIALISATION CONFIGURATION TOGO ===\n'))
        
        # 1. Charger les types de congés
        self.stdout.write('1. Chargement des types de conges...')
        try:
            call_command('loaddata', 'togo_leave_types.json', verbosity=0)
            self.stdout.write(self.style.SUCCESS('   [OK] Types de conges charges'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   [WARN] {str(e)}'))
        
        # 2. Charger les jours fériés 2025
        self.stdout.write('2. Chargement des jours feries 2025...')
        try:
            call_command('loaddata', 'togo_holidays_2025.json', verbosity=0)
            self.stdout.write(self.style.SUCCESS('   [OK] Jours feries 2025 charges'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   [WARN] {str(e)}'))
        
        # 3. Créer les soldes pour les utilisateurs existants
        self.stdout.write('3. Creation des soldes de conges...')
        
        try:
            conges_payes = LeaveType.objects.get(code='CP')
        except LeaveType.DoesNotExist:
            self.stdout.write(self.style.ERROR('   [ERR] Type "Conges payes" introuvable'))
            return
        
        users = User.objects.filter(is_superuser=False, employee_profile__isnull=False)
        created_count = 0
        existing_count = 0
        
        for user in users:
            balance, was_created = LeaveBalance.objects.get_or_create(
                employee=user,
                leave_type=conges_payes,
                year=date.today().year,
                defaults={
                    'allocated_balance': conges_payes.allocation_amount,
                    'taken_balance': 0,
                    'carried_over_balance': 0
                }
            )
            
            if was_created:
                created_count += 1
                self.stdout.write(f'   [OK] {user.username}: {conges_payes.allocation_amount} jours')
            else:
                existing_count += 1
        
        # 4. Résumé
        self.stdout.write(self.style.SUCCESS(f'\n=== RESUME ==='))
        self.stdout.write(f'Types de conges: 4 (Conges payes, Maladie, Evenements, Sans solde)')
        self.stdout.write(f'Jours feries: 10 (annee 2025)')
        self.stdout.write(f'Soldes crees: {created_count}')
        self.stdout.write(f'Soldes existants: {existing_count}')
        self.stdout.write(f'Total utilisateurs: {created_count + existing_count}')
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Configuration Togo initialisee avec succes!\n'))
        self.stdout.write('Votre systeme est pret a l\'emploi pour les PME togolaises.\n')
        self.stdout.write('\nNote: Les fetes musulmanes (Ramadan, Tabaski) doivent etre ajoutees\n')
        self.stdout.write('manuellement chaque annee via l\'interface RH (dates variables).\n')

