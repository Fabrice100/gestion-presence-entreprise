"""
Commande de gestion pour initialiser les jours fériés du Togo.

Usage:
    python manage.py init_togo_holidays
    python manage.py init_togo_holidays --year 2024
    python manage.py init_togo_holidays --year 2024 --year 2025
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from leave.holiday_service import holiday_service


class Command(BaseCommand):
    help = 'Initialise les jours fériés du Togo pour une ou plusieurs années'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            action='append',
            help='Année(s) pour laquelle(s) initialiser les jours fériés (peut être répété)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la mise à jour même si les jours fériés existent déjà',
        )

    def handle(self, *args, **options):
        years = options['year']
        force = options['force']
        
        if not years:
            # Par défaut, initialiser pour l'année courante et la suivante
            current_year = timezone.now().year
            years = [current_year, current_year + 1]
        
        self.stdout.write(
            self.style.SUCCESS(f'Initialisation des jours fériés du Togo pour les années: {", ".join(map(str, years))}')
        )
        
        total_created = 0
        total_updated = 0
        
        for year in years:
            try:
                result = holiday_service.initialize_togo_holidays(year)
                total_created += result['created']
                total_updated += result['updated']
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Année {year}: {result["created"]} créés, {result["updated"]} mis à jour'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur pour l\'année {year}: {str(e)}')
                )
                raise CommandError(f'Échec de l\'initialisation pour l\'année {year}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nRésumé: {total_created} jours fériés créés, {total_updated} mis à jour au total'
            )
        )



