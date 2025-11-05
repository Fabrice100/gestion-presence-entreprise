from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0011_purge_anomalies'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AttendanceAnomaly',
        ),
    ]





