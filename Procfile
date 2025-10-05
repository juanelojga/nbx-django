release: python nbxdjango/manage.py migrate
web: gunicorn nbxdjango.wsgi:application --bind 0.0.0.0:$PORT --workers=3 --log-file -