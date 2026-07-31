release: python manage.py migrate --noinput
web: gunicorn jobportal_project.wsgi:application --log-file -
