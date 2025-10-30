"""
Commande de gestion pour initialiser les soldes de congés des employés.

Usage:
    python manage.py init_leave_balances
    python manage.py init_leave_balances --year 2024
    python manage.py init_leave_balances --user username
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth.models import User
from leave.leave_balance_service import leave_balance_service


class Command(BaseCommand):
    help = 'Initialise les soldes de congés des employés pour une année'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Année pour laquelle initialiser les soldes (défaut: année courante)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Nom d\'utilisateur spécifique à traiter',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la mise à jour même si les soldes existent déjà',
        )

    def handle(self, *args, **options):
        year = options['year'] or timezone.now().year
        username = options['user']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(f'Initialisation des soldes de congés pour l\'année {year}')
        )
        
        # Récupérer les utilisateurs à traiter
        if username:
            try:
                users = [User.objects.get(username=username)]
                self.stdout.write(f'Traitement de l\'utilisateur: {username}')
            except User.DoesNotExist:
                raise CommandError(f'Utilisateur "{username}" non trouvé')
        else:
            # Tous les utilisateurs avec un profil employé
            users = User.objects.filter(employee_profile__isnull=False)
            self.stdout.write(f'Traitement de {users.count()} utilisateurs')
        
        total_created = 0
        total_updated = 0
        errors = []
        
        for user in users:
            try:
                result = leave_balance_service.initialize_employee_balance(user, year)
                
                if result['created']:
                    total_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {user.username}: Solde créé')
                    )
                elif result['updated']:
                    total_updated += 1
                    self.stdout.write(
                        self.style.WARNING(f'~ {user.username}: Solde mis à jour')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'- {user.username}: Solde déjà existant')
                    )
                
            except Exception as e:
                error_msg = f'Erreur pour {user.username}: {str(e)}'
                errors.append(error_msg)
                self.stdout.write(
                    self.style.ERROR(f'✗ {error_msg}')
                )
        
        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Résumé: {total_created} soldes créés, {total_updated} mis à jour'
            )
        )
        
        if errors:
            self.stdout.write(
                self.style.ERROR(f'{len(errors)} erreurs rencontrées:')
            )
            for error in errors:
                self.stdout.write(f'  - {error}')
        else:
            self.stdout.write(
                self.style.SUCCESS('Tous les soldes ont été initialisés avec succès!')
            )



