FROM python:3.10-slim

ENV PROJECT_ROOT /project
ENV DEPLOY_DIR ./deploy
ENV SRC_DIR /src

RUN mkdir $PROJECT_ROOT
COPY $DEPLOY_DIR/gunicorn.conf.py $PROJECT_ROOT
COPY $DEPLOY_DIR/run_app.sh $PROJECT_ROOT

RUN apt-get update && \
    apt-get install -y build-essential libpq-dev python3-dev && \
    apt-get clean

COPY ./$SRC_DIR/requirements.txt $PROJECT_ROOT

WORKDIR $PROJECT_ROOT
RUN pip install -r requirements.txt

COPY ./$SRC_DIR $PROJECT_ROOT

RUN chmod +x $PROJECT_ROOT/run_app.sh
CMD ["/project/run_app.sh"]

