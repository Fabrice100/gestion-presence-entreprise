from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0005_add_deducts_balance_field'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE leave_leaverequest "
                "DROP COLUMN IF EXISTS priority CASCADE;"
            ),
            reverse_sql=(
                "ALTER TABLE leave_leaverequest "
                "ADD COLUMN IF NOT EXISTS priority integer DEFAULT 1 NOT NULL;"
            ),
        ),
    ]



