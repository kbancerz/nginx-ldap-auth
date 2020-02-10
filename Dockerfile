FROM python:3.8-alpine

WORKDIR /usr/src/app
COPY . /usr/src/app/

RUN apk --no-cache add build-base openldap-dev && \
    pip install --no-cache-dir -r requirements.txt

ENV NGINX_LDAP_AUTH_CONFIG_FILE=/usr/src/app/config.json
ENV NGINX_LDAP_AUTH_JSON_INDENT=4
ENV NGINX_LDAP_AUTH_HOST="0.0.0.0"
ENV NGINX_LDAP_AUTH_PORT=8088

CMD [ "python", "-u", "nginx-ldap-auth-server", "run-server" ]
