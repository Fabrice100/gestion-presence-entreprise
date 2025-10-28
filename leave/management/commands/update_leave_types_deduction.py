"""
Management command pour mettre à jour le champ deducts_balance des types de congés existants.

Conforme aux spécifications: MODULE 2 - Types de Congés
- Congé Annuel Payé → déduit du solde (deducts_balance=True)
- Congés Exceptionnels/Événements → NE déduit PAS (deducts_balance=False)
- Congés Maladie → NE déduit PAS (deducts_balance=False)
- Congé sans solde → NE déduit PAS (deducts_balance=False)
"""

from django.core.management.base import BaseCommand
from leave.models import LeaveType


class Command(BaseCommand):
    help = 'Met à jour le champ deducts_balance pour les types de congés existants'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n🔄 Mise à jour des types de congés...'))
        
        updated_count = 0
        
        # 1. Congés payés → DÉDUIT du solde
        annual_leave = LeaveType.objects.filter(code='CP').first()
        if annual_leave:
            annual_leave.deducts_balance = True
            annual_leave.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {annual_leave.name} → deducts_balance=True')
            )
            updated_count += 1
        
        # 2. Congé maladie → NE DÉDUIT PAS
        sick_leave = LeaveType.objects.filter(code='MAL').first()
        if sick_leave:
            sick_leave.deducts_balance = False
            sick_leave.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {sick_leave.name} → deducts_balance=False (ne déduit PAS)')
            )
            updated_count += 1
        
        # 3. Événements familiaux → NE DÉDUIT PAS
        family_leave = LeaveType.objects.filter(code='EVT').first()
        if family_leave:
            family_leave.deducts_balance = False
            family_leave.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {family_leave.name} → deducts_balance=False (ne déduit PAS)')
            )
            updated_count += 1
        
        # 4. Congé sans solde → NE DÉDUIT PAS
        unpaid_leave = LeaveType.objects.filter(code='CSS').first()
        if unpaid_leave:
            unpaid_leave.deducts_balance = False
            unpaid_leave.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {unpaid_leave.name} → deducts_balance=False (ne déduit PAS)')
            )
            updated_count += 1
        
        # 5. Tous les autres types non mentionnés → Par défaut TRUE (déduit)
        other_types = LeaveType.objects.exclude(code__in=['CP', 'MAL', 'EVT', 'CSS'])
        if other_types.exists():
            other_types.update(deducts_balance=True)
            self.stdout.write(
                self.style.WARNING(f'⚠️  {other_types.count()} autre(s) type(s) → deducts_balance=True (par défaut)')
            )
            updated_count += other_types.count()
        
        # Résumé
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Mise à jour terminée : {updated_count} type(s) de congé(s) mis à jour')
        )
        
        # Afficher le résumé final
        self.stdout.write(self.style.WARNING('\n📊 RÉSUMÉ DES TYPES DE CONGÉS:'))
        for leave_type in LeaveType.objects.all():
            deducts_emoji = '✅ Déduit' if leave_type.deducts_balance else '❌ Ne déduit PAS'
            self.stdout.write(f'   {leave_type.code}: {leave_type.name} → {deducts_emoji}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Configuration conforme aux spécifications !'))
