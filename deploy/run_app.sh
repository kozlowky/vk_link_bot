#!/bin/bash

APPDIR=$(dirname $(pwd))
echo $APPDIR

export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="${PYTHONPATH}:$APPDIR"

gunicorn -c "gunicorn.conf.py" backend.wsgi:application

python ${APPDIR}core/manage.py collectstatic --noinput
python ${APPDIR}core/manage.py migrate --noinput
python ${APPDIR}core/manage.py runserver 0.0.0.0:8000 &
python ${APPDIR}core/manage.py run_bot

