FROM python:3.8-alpine

WORKDIR /usr/src/app
COPY . /usr/src/app/

RUN apk --no-cache add build-base openldap-dev && \
    pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "nginx-ldap-auth-server", "run-server" ]
