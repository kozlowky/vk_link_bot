FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

#COPY deploy/requirements.txt /app
#COPY deploy/run_app.sh /app

COPY . .

COPY deploy/gunicorn.conf.py /app/core

RUN apt-get update && \
    apt-get install -y build-essential libpq-dev python3-dev && \
    apt-get clean

RUN pip install --upgrade pip && \
    pip install -r deploy/requirements.txt

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=core.settings
ENV PYTHONPATH="${PYTHONPATH}:/app"

#RUN chmod +x /app/deploy/run_app.sh
#CMD ["/app/deploy/run_app.sh"]
CMD ["python core/manage.py collectstatic --noinput",
     "python core/manage.py migrate --noinput",
     "python core/manage.py runserver 0.0.0.0:8000",
     "python core/manage.py run_bot",
     "gunicorn -c 'core/gunicorn.conf.py' core.wsgi:application"]
