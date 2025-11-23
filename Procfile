web: cd attendance_system && python manage.py migrate --noinput && python manage.py create_superuser_if_not_exists && gunicorn attendance_system.wsgi:application --bind 0.0.0.0:$PORT

