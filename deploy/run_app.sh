#!/bin/bash

python src/manage.py collectstatic --noinput
python src/manage.py migrate --noinput
python src/manage.py runserver 0.0.0.0:8000 &
python src/manage.py run_bot

gunicorn -c "$PROJECT_ROOT/gunicorn.conf.py" server.wsgi:application

