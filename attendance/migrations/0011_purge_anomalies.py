from django.db import migrations


def purge_anomalies(apps, schema_editor):
    AttendanceAnomaly = apps.get_model('attendance', 'AttendanceAnomaly')
    # Supprimer toutes les entrées d'anomalies
    AttendanceAnomaly.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0010_remove_technical_anomalies'),
    ]

    operations = [
        migrations.RunPython(purge_anomalies, migrations.RunPython.noop),
    ]







