FROM nginx:alpine
RUN mkdir /etc/nginx/ssl
COPY ./default.conf /etc/nginx/conf.d/default.conf
COPY ./uploadsize.conf /etc/nginx/conf.d/uploadsize.conf
COPY ./server.key /etc/nginx/ssl/
COPY ./server.crt /etc/nginx/ssl/
RUN mkdir /etc/nginx/logs
