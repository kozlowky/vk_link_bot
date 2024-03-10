#!/bin/bash

export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="${PYTHONPATH}:/app"

gunicorn -c "gunicorn.conf.py" backend.wsgi:application

python core/manage.py collectstatic --noinput
python core/manage.py migrate --noinput
python core/manage.py runserver 0.0.0.0:8000 &
python core/manage.py run_bot

