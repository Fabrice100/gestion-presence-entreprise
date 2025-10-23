# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_employeeprofile_force_password_change'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employeeprofile',
            name='phone',
        ),
    ]





