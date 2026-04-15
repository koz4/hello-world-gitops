FROM nginxinc/nginx-unprivileged:latest
COPY html/ /usr/share/nginx/html/
