python manage.py collectstatic --noinput
python manage.py migrate
gunicorn greatcart.wsgi:application --workers 1 --threads 4 --timeout 0 --log-level debug --bind 0.0.0.0:8000
