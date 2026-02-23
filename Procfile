release: python nbxdjango/manage.py migrate
web: cd nbxdjango && gunicorn nbxdjango.wsgi --bind 0.0.0.0:$PORT --log-file -