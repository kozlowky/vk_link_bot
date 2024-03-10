#!/bin/bash

export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="${PYTHONPATH}:/app"

gunicorn -c "gunicorn.conf.py" backend.wsgi:application

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000 &
python manage.py run_bot

