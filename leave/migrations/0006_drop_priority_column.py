from django.db import migrations


def _drop_priority_column(apps, schema_editor):
    # Migration conservée pour compatibilité historique.
    # La suppression effective de la colonne est gérée par la migration 0008.
    return


def _restore_priority_column(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0005_add_deducts_balance_field'),
    ]

    operations = [
        migrations.RunPython(
            code=_drop_priority_column,
            reverse_code=_restore_priority_column,
        ),
    ]



