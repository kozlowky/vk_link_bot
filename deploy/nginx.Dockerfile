FROM nginx:stable-alpine

ENV DOLLAR $

COPY deploy/default.conf.template /etc/nginx/templates/default.conf.template