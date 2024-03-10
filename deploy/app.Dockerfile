FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . .

COPY deploy/gunicorn.conf.py /app/core

RUN apt-get update && \
    apt-get install -y build-essential libpq-dev python3-dev && \
    apt-get clean

RUN pip install --upgrade pip && \
    pip install -r deploy/requirements.txt

EXPOSE 8000

RUN chmod +x /app/deploy/run_app.sh
CMD ["/app/deploy/run_app.sh"]

