# Cloud Nexus — reverse proxy (TLS on 443). Self-signed cert for dev; replace in production.
FROM nginx:alpine
RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/ssl \
    && openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/server.key \
        -out /etc/nginx/ssl/server.crt \
        -subj "/CN=localhost"
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80 443
