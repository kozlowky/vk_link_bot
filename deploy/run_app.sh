#!/bin/bash

export DJANGO_SETTINGS_MODULE=src.settings
export PYTHONPATH="${PYTHONPATH}:/app"

python src/manage.py collectstatic --noinput
python src/manage.py migrate --noinput
python src/manage.py runserver 0.0.0.0:8000 &
python src/manage.py run_bot

gunicorn -c "core/gunicorn.conf.py" src.wsgi:application

