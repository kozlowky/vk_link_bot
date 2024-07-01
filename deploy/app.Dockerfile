#FROM python:3.10-slim
#
#ENV PYTHONDONTWRITEBYTECODE 1
#ENV PYTHONUNBUFFERED 1
#
#WORKDIR /app
#
#COPY . .
#
#COPY deploy/gunicorn.conf.py /app/core
#
#RUN apt-get update && \
#    apt-get install -y build-essential libpq-dev python3-dev && \
#    apt-get clean
#
#RUN pip install --upgrade pip && \
#    pip install -r deploy/requirements.txt
#
#EXPOSE 8000
#
#RUN chmod +x /app/deploy/run_app.sh
#CMD ["/app/deploy/run_app.sh"]
FROM python:3.10-slim

ENV PROJECT_ROOT /project
ENV DEPLOY_DIR ./deploy
ENV SRC_DIR /src

RUN mkdir $PROJECT_ROOT
COPY $DEPLOY_DIR/gunicorn.conf.py $PROJECT_ROOT
COPY $DEPLOY_DIR/run_django.sh $PROJECT_ROOT

RUN apt-get update && \
    apt-get install -y build-essential libpq-dev python3-dev nodejs npm && \
    apt-get clean

COPY ./$SRC_DIR/requirements.txt $PROJECT_ROOT

WORKDIR $PROJECT_ROOT
RUN pip install -r requirements.txt

COPY ./$SRC_DIR $PROJECT_ROOT

RUN chmod +x $PROJECT_ROOT/run_django.sh
CMD ["/project/run_app.sh"]

