from django.core.management.base import BaseCommand
from django.db import connection


TABLES_TO_FIX = [
    ('auth_user', 'id'),
    ('leave_leavebalance', 'id'),
]


def reset_sequence(table: str, col: str = 'id') -> None:
    sql = (
        f"SELECT setval(pg_get_serial_sequence('{table}','{col}'), "
        f"COALESCE((SELECT MAX({col}) FROM {table}), 0) + 1, false);"
    )
    with connection.cursor() as cursor:
        cursor.execute(sql)


class Command(BaseCommand):
    help = "Réinitialise proprement les séquences Postgres pour éviter les erreurs de clé primaire dupliquée."

    def add_arguments(self, parser):
        parser.add_argument(
            '--tables', nargs='*', default=None,
            help='Liste des tables à corriger (par défaut: auth_user, leave_leavebalance)'
        )

    def handle(self, *args, **options):
        tables = options.get('tables')
        targets = TABLES_TO_FIX if not tables else [(t, 'id') for t in tables]

        for table, col in targets:
            self.stdout.write(self.style.WARNING(f"Reset sequence for {table}.{col} ..."))
            reset_sequence(table, col)
            self.stdout.write(self.style.SUCCESS(f"OK: {table}"))

        self.stdout.write(self.style.SUCCESS("Séquences réinitialisées."))





