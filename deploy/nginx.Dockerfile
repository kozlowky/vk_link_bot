FROM nginx:stable-alpine

ENV DOLLAR $

COPY ./deploy/nginx.conf /etc/nginx/conf.d/default.conf
