#!/bin/bash


RUN python manage.py collectstatic --noinput

RUN python manage.py migrate --noinput

python manage.py runserver 0.0.0.0:8000 &

python manage.py run_bot

gunicorn -c "gunicorn.conf.py" backend.wsgi:application