"""
Commande Django pour détecter automatiquement les oublis de pointage de sortie.

Cette commande doit être exécutée quotidiennement (par exemple via Windows Task Scheduler
ou cron) pour détecter les employés qui ont oublié de pointer leur sortie la veille.

Usage:
    python manage.py detect_missing_punches
    python manage.py detect_missing_punches --date 2025-10-22
    python manage.py detect_missing_punches --days 7 (derniers 7 jours)
    python manage.py detect_missing_punches --notify (envoyer notifications)

Configuration Windows Task Scheduler:
    - Nom de la tâche: Détection oublis de pointage
    - Déclencheur: Quotidien à 01:00
    - Action: Démarrer un programme
    - Programme: python.exe
    - Arguments: manage.py detect_missing_punches --notify
    - Commencer dans: C:\\Users\\...\\attendance_system
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import date, timedelta
from attendance.hours_calculation_service import HoursCalculationService
from accounts.models import EmployeeProfile


class Command(BaseCommand):
    help = 'Détecte automatiquement les oublis de pointage de sortie'

    def add_arguments(self, parser):
        """Ajouter les arguments de la commande."""
        parser.add_argument(
            '--date',
            type=str,
            help='Date spécifique à vérifier (format: YYYY-MM-DD). Par défaut: hier'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            help='Nombre de jours à vérifier en arrière (ex: 7 pour la dernière semaine)'
        )
        
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Envoyer des notifications par email aux managers'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher plus de détails'
        )

    def handle(self, *args, **options):
        """Exécution de la commande."""
        
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write(self.style.HTTP_INFO('   DÉTECTION AUTOMATIQUE DES OUBLIS DE POINTAGE'))
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        
        # Déterminer les dates à vérifier
        dates_to_check = self._get_dates_to_check(options)
        
        if not dates_to_check:
            raise CommandError("Aucune date à vérifier")
        
        self.stdout.write(f"\nDates a verifier: {len(dates_to_check)} jour(s)")
        for check_date in dates_to_check:
            self.stdout.write(f"   - {check_date.strftime('%A %d/%m/%Y')}")
        
        # Statistiques globales
        total_anomalies = 0
        total_employees_affected = set()
        
        # Vérifier chaque date
        for check_date in dates_to_check:
            self.stdout.write(f"\nVerification du {check_date.strftime('%d/%m/%Y')}...")
            
            anomalies = HoursCalculationService.detect_missing_punch_outs(check_date)
            
            if anomalies:
                total_anomalies += len(anomalies)
                self.stdout.write(
                    self.style.WARNING(f"   [!] {len(anomalies)} oubli(s) de sortie detecte(s)")
                )
                
                for anomaly in anomalies:
                    employee = anomaly.attendance.employee
                    total_employees_affected.add(employee.id)
                    
                    if options['verbose']:
                        self.stdout.write(
                            f"      - {employee.get_full_name()} - "
                            f"Entree a {anomaly.attendance.time.strftime('%H:%M')}"
                        )
            else:
                self.stdout.write(self.style.SUCCESS("   [OK] Aucun oubli detecte"))
        
        # Résumé final
        self.stdout.write(f"\n{'=' * 70}")
        self.stdout.write(self.style.HTTP_INFO("RESUME"))
        self.stdout.write(f"{'=' * 70}")
        self.stdout.write(f"- Total anomalies creees: {total_anomalies}")
        self.stdout.write(f"- Employes concernes: {len(total_employees_affected)}")
        
        # Envoyer notifications si demandé
        if options['notify'] and total_anomalies > 0:
            self.stdout.write(f"\nEnvoi des notifications...")
            notifications_sent = self._send_notifications(total_employees_affected)
            self.stdout.write(
                self.style.SUCCESS(f"[OK] {notifications_sent} notification(s) envoyee(s)")
            )
        
        # Message de succès final
        if total_anomalies > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[!] {total_anomalies} anomalie(s) detectee(s) et enregistree(s)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n[OK] Aucune anomalie detectee - Tout est en ordre !")
            )
        
        self.stdout.write(f"{'=' * 70}\n")
    
    def _get_dates_to_check(self, options):
        """
        Détermine les dates à vérifier selon les options.
        
        Returns:
            list: Liste d'objets date à vérifier
        """
        today = date.today()
        
        # Option --date spécifique
        if options['date']:
            try:
                specific_date = date.fromisoformat(options['date'])
                return [specific_date]
            except ValueError:
                raise CommandError(
                    f"Format de date invalide: {options['date']}. "
                    "Utilisez le format YYYY-MM-DD"
                )
        
        # Option --days (derniers X jours)
        if options['days']:
            days = options['days']
            if days < 1:
                raise CommandError("Le nombre de jours doit être >= 1")
            
            dates = []
            for i in range(1, days + 1):
                dates.append(today - timedelta(days=i))
            return dates
        
        # Par défaut: hier
        return [today - timedelta(days=1)]
    
    def _send_notifications(self, employee_ids):
        """
        Envoie des notifications aux managers des employés concernés.
        
        Args:
            employee_ids (set): IDs des employés avec anomalies
            
        Returns:
            int: Nombre de notifications envoyées
        """
        from django.contrib.auth.models import User
        from attendance.models import AttendanceAnomaly
        
        notifications_sent = 0
        managers_notified = set()
        
        # Grouper les anomalies par manager/département
        for emp_id in employee_ids:
            try:
                employee = User.objects.get(id=emp_id)
                profile = EmployeeProfile.objects.get(user=employee)
                
                # Trouver le manager
                if profile.department and profile.department.manager:
                    manager = profile.department.manager
                    
                    # Éviter d'envoyer plusieurs emails au même manager
                    if manager.id not in managers_notified:
                        # Compter les anomalies de ce département
                        dept_anomalies = AttendanceAnomaly.objects.filter(
                            attendance__employee__employeeprofile__department=profile.department,
                            status='pending',
                            anomaly_type='missing_punch_out'
                        ).count()
                        
                        # TODO: Implémenter l'envoi d'email réel
                        # self._send_email_to_manager(manager, dept_anomalies)
                        
                        self.stdout.write(
                            f"   [EMAIL] Notification pour {manager.get_full_name()} "
                            f"({dept_anomalies} anomalie(s) dans son departement)"
                        )
                        
                        managers_notified.add(manager.id)
                        notifications_sent += 1
                        
            except (User.DoesNotExist, EmployeeProfile.DoesNotExist):
                continue
        
        return notifications_sent
    
    def _send_email_to_manager(self, manager, anomalies_count):
        """
        Envoie un email au manager (à implémenter).
        
        Args:
            manager (User): Manager à notifier
            anomalies_count (int): Nombre d'anomalies dans son département
        """
        # TODO: Implémenter avec Django email
        # from django.core.mail import send_mail
        # 
        # subject = f"⚠️ {anomalies_count} oubli(s) de pointage dans votre département"
        # message = f"""
        # Bonjour {manager.get_full_name()},
        # 
        # {anomalies_count} employé(s) de votre département ont oublié de pointer leur sortie.
        # 
        # Veuillez vous connecter à l'interface RH pour vérifier et corriger ces anomalies:
        # https://votre-site.com/rh/anomalies
        # 
        # Cordialement,
        # Système de gestion de présence
        # """
        # 
        # send_mail(
        #     subject,
        #     message,
        #     'noreply@votreentreprise.com',
        #     [manager.email],
        #     fail_silently=False,
        # )
        pass
