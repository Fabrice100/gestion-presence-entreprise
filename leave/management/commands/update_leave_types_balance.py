"""
Management command pour mettre à jour le champ deducts_balance des types de congés.

Usage:
    python manage.py update_leave_types_balance
"""

from django.core.management.base import BaseCommand
from leave.models import LeaveType


class Command(BaseCommand):
    help = 'Met à jour le champ deducts_balance des types de congés existants'
    
    def handle(self, *args, **options):
        """Exécute la mise à jour des types de congés."""
        
        self.stdout.write(self.style.SUCCESS('\n🔄 Mise à jour des types de congés...'))
        self.stdout.write('=' * 60)
        
        # Configuration des types de congés
        updates = [
            ('Congé Annuel Payé', True, 'Déduit du solde annuel'),
            ('Congé Exceptionnel', False, 'Ne déduit PAS du solde'),
            ('Congé Maladie', False, 'Ne déduit PAS du solde'),
            ('Congé Sans Solde', False, 'Ne déduit PAS du solde'),
        ]
        
        updated_count = 0
        
        for name, deducts, description in updates:
            try:
                leave_type = LeaveType.objects.get(name=name)
                leave_type.deducts_balance = deducts
                leave_type.save(update_fields=['deducts_balance'])
                
                symbol = "✅ DÉDUIT" if deducts else "❌ NE DÉDUIT PAS"
                self.stdout.write(f"{symbol} | {name}")
                self.stdout.write(f"         {description}")
                
                updated_count += 1
                
            except LeaveType.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️  INTROUVABLE | {name}"))
        
        # Afficher tous les types
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'✅ {updated_count} types mis à jour'))
        
        self.stdout.write('\n📋 TOUS LES TYPES DE CONGÉS:')
        self.stdout.write('=' * 60)
        
        for lt in LeaveType.objects.all().order_by('name'):
            deduct = "✅ DÉDUIT" if lt.deducts_balance else "❌ NE DÉDUIT PAS"
            paid = "💰 PAYÉ" if lt.is_paid else "⛔ NON PAYÉ"
            
            self.stdout.write(f"\n{lt.name} ({lt.code})")
            self.stdout.write(f"   {deduct} du solde")
            self.stdout.write(f"   {paid}")
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Terminé !\n'))
