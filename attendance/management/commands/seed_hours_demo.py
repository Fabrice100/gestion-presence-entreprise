from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time

from django.contrib.auth.models import User

from attendance.models import Attendance
from accounts.models import EmployeeProfile
from attendance.hours_calculation_service import HoursCalculationService


class Command(BaseCommand):
    help = "Génère des pointages d'entrée/sortie de démonstration pour alimenter le rapport Heures travaillées."

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=1, help='Nombre de jours à générer (à partir d\'aujourd\'hui en remontant)')
        parser.add_argument('--in-time', default='09:00', help="Heure d'entrée HH:MM")
        parser.add_argument('--out-time', default='17:00', help="Heure de sortie HH:MM")

    def handle(self, *args, **options):
        days = options['days']
        in_time_str = options['in_time']
        out_time_str = options['out_time']

        in_h, in_m = [int(x) for x in in_time_str.split(':')]
        out_h, out_m = [int(x) for x in out_time_str.split(':')]
        in_t = time(in_h, in_m)
        out_t = time(out_h, out_m)

        today = timezone.now().date()

        # Cibler tous les employés actifs (exclure RH)
        profiles = EmployeeProfile.objects.filter(is_active=True).exclude(role='rh')
        if not profiles.exists():
            self.stdout.write(self.style.WARNING("Aucun profil employé actif trouvé (hors RH)."))
            return

        created_count = 0
        for d in range(days):
            the_date = today - timedelta(days=d)
            for profile in profiles:
                user = profile.user

                # Entrée
                att_in, _ = Attendance.objects.get_or_create(
                    employee=user,
                    date=the_date,
                    punch_type='in',
                    defaults={
                        'time': in_t,
                        'latitude': 6.140766,
                        'longitude': 1.241907,
                        'accuracy': 30.0,
                        'status': 'normal',
                        'source': 'web',
                    }
                )

                # Sortie
                att_out, created_out = Attendance.objects.get_or_create(
                    employee=user,
                    date=the_date,
                    punch_type='out',
                    defaults={
                        'time': out_t,
                        'latitude': 6.140766,
                        'longitude': 1.241907,
                        'accuracy': 30.0,
                        'status': 'normal',
                        'source': 'web',
                    }
                )

                # Calculer les heures travaillées pour la sortie
                HoursCalculationService.update_worked_hours_on_punch_out(att_out)

                if created_out:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Pointages de démo générés pour {created_count} sorties sur {days} jour(s)."))







