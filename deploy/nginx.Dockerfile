FROM nginx:stable-alpine

RUN rm /etc/nginx/conf.d/default.conf && \
    mkdir -p /etc/nginx/conf.d

COPY /deploy/nginx.conf /etc/nginx/conf.d/default.conf

COPY ./core/static /app/static