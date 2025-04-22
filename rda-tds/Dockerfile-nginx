FROM nginx:1.24.0
#COPY ./default.conf /etc/nginx/conf.d/default.conf
RUN mkdir -p /etc/letsencrypt/live/rda-tds.ucar.edu/
COPY ./index.html /usr/share/nginx/html/
COPY http_default.conf /etc/nginx/conf.d/default.conf
