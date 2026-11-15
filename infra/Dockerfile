# Образ шлюза: nginx + конфиг + документация API.
# Собирается из корня репозитория: docker build -f infra/Dockerfile .
FROM nginx:1.25.4-alpine
COPY infra/nginx.conf /etc/nginx/conf.d/default.conf
COPY docs/ /usr/share/nginx/html/api/docs/
