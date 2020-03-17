nginx-ldap-auth: LDAP Authentication Page
----
This solution enables granular access control to proxied nginx sites, based on LDAP directory data.

### Features
* LDAP-based authentication
* Access control based on LDAP group membership
* Custom login page - instead of basic authentication popup
* Custom authorization error page (403)
* Configurable pass-through based on request source address (e.g. to allow unrestricted access inside internal network)

Preparation of the Docker image
----

Clone this repo and build a docker image:

```
git clone https://github.com/kbancerz/nginx-ldap-auth.git && cd nginx-ldap-auth
docker build -t nginx-ldap-auth .
```

Generate a sample config file:

```
docker run --rm nginx-ldap-auth ./nginx-ldap-auth-server get-sample-config > config.json
```

Maintain the file as described in 'Configuration' section and create a docker container:

```
docker run --rm -p 8088:8088 -v ./config.json:/usr/src/app/config.json nginx-ldap-auth
```

or alternatively use **docker-compose**:

```
docker-compose up -d
```

This will open authentication server on port 8088.

Server Configuration
----
Server requires configuration file to be maintained. It is divided into several different sections:

#### LDAP
* **host** (e.g. _"ldap.example.com"_) - LDAP server host
* **port** (e.g. _389_) - LDAP server port
* **username** (e.g. _"admin"_) - LDAP read-only account
* **password** (e.g. _"password"_) - LDAP account password
* **user_attr** (e.g. _"uid"_) - LDAP user attribute used as login during authentication
* **user_base_dn** (e.g. _"ou=users,dc=example,dc=com"_) - base DN for user search
* **group_base_dn** (e.g. _"ou=groups,dc=example,dc=com"_) - base DN for group search
* **group_cache_max_age** (e.g. _300_) - server caches list of groups of which an account used for authentication is member of, set this to change invalidation period (in seconds)


#### Session
* **cookie_session** (e.g. _"EXAMPLE_COM_SSO"_) - name of session cookie
* **cookie_redirect** (e.g. _"EXAMPLE_COM_REDIRECT"_) - name of redirection cookie (holds referrer URL)
* **cookie_domain** (e.g. _".example.com"_) - cookie domain - use it to change the scope of the session cookie
* **cookie_secret** (e.g. _"4ZRL5a0emNFTMI7wn1PBe1JWXlZ59C5D"_) - secret, that is used to encrypt session information
* **cookie_max_age** (e.g. _86400_) - max age of the cookie:
    * if a positive number - treated as a number of seconds
    * if zero or a negative number - treated as a number of full days of validity before expiring at 23:59:59 - e.g. if set to -1, then a cookie created at 15:00 will expire at midnight of the next day (one full day + 9h)

#### Pages
* **login_template** (e.g. _"./pages/templates/login.html.j2"_) - path to login page template (Bottle template language)
* **noauth_template** (e.g. _"./pages/templates/noauth.html.j2"_) - path to 403 page template (Bottle template language)
* **static_root** (e.g. _"./pages/static"_) - path to static files root folder
* **fallback_redirect** (e.g. _"https://internal.example.com"_) - redirection fallback address - if redirection cookie is not set (e.g. login page was accessed directly), a user will be redirected to this address after successfully logging in

#### Ingress
* **ignored_addresses** (e.g. _["192.168.0.1"]_) - list of source hosts, for which authentication should not be checked (e.g. when accessed from within an internal network/VPN/etc.)

nginx Configuration
----
When the server is running, nginx needs to be configured to utilize authentication service provided.

Sample configuration snippets are presented below - each can be placed as a separate config file in _/etc/nginx_ directory and referred to with **include** clause.

### Enable access control

For each **server** configuration clause a set of generic locations needs to be defined:

**auth_locations.conf**:
```
location /__auth {
        internal;
        proxy_pass_request_body off;

        proxy_set_header   Host $host;
        proxy_set_header   Content-Length "";
        proxy_set_header   X-LDAP-AUTH-USERS $ldap_allowed_users;
        proxy_set_header   X-LDAP-AUTH-GROUPS $ldap_allowed_groups;
        proxy_set_header   X-LDAP-AUTH-INGRESS $server_addr;

        proxy_cache auth;
        proxy_cache_valid 200 1m;
        proxy_cache_key "$cookie_eccsso$server_addr$host";

        proxy_pass http://localhost:8088/auth;
}

location @access_error401 {
        add_header Set-Cookie "EXAMPLE_COM_REDIRECT=$scheme://$http_host$request_uri;Domain=.example.com;Path=/";
        return 302 http://access.example.com/;
}

location @access_error403 {
        add_header Set-Cookie "EXAMPLE_COM_REDIRECT=$scheme://$http_host$request_uri;Domain=.example.com;Path=/";
        return 302 http://access.example.com/noauth;
}
```

The first location is the actual authentication server. For each incoming request nginx will access this location first, to authenticate the user. Please notice, that _ldap_allowed_users_ and _ldap_allowed_groups_ parameters are used here. These can be set for each resource separately. Multiple values are separated with a semicolon. Authentication flow is following:
* Check login and password
    * if _incorrect_ - return 401
    * if _correct_ - continue
* Check user name
    * if _ldap_allowed_users_ is defined **and** user is on the list - authorize the user, return 200
    * if _ldap_allowed_users_ is not defined **or** user is not on the list - continue
* Check user group membership
    * if _ldap_allowed_groups_ is defined **and** user is a member of **any** of the defined groups - authorize the user, return 200
    * if _ldap_allowed_groups_ is defined **and** user is **not** a member of **any** of the defined groups - unauthorized, return 403
    * if _ldap_allowed_groups_ is **not** defined - authorize the user, return 200

Auth server responses are cached - please check _Caching_ section for more details.

The second location is a generic response to a 401 status returned by the auth server - this will set the redirection cookie to the referring URL and send the user to the login page.

Last location is a response to a 403 - unauthorized error - in this case user is sent to the error page on the auth server. On this page optional information can be shown, so that the user can - for example - contact administrators and request access.

Please notice, that error locations set the redirection cookie, so **make sure**, that the name (here _EXAMPLE_COM_REDIRECT_) matches the one set in the auth server configuration - **cookie_redirect**. The same goes for the domain (here: _.example.com_), **make sure** it matches **cookie_domain** parameter.

Both login and 403 error page need to be accessible to the end-users - in this example they are proxied and available at http://access.example.com.

### Access to resources

Access control is enabled by adding configuration a snippet to the **server** clause:

**auth_enable.conf**:
```
auth_request /__auth;
error_page 401 = @access_error401;
error_page 403 = @access_error403;
```

A sample website configuration with access restriction enabled:

```
server {
    listen 80;
    server_name internal.example.com;

    location / {
        # enable access control for this location - notice,
        # that this is set location-wide - thanks to this,
        # additional locations can be set, without LDAP access
        # control - useful for WebService or REST endpoints etc.
        include /etc/nginx/auth_enable.conf;

        root /var/www/html;
        index index.html;
    }

    set $ldap_allowed_users "cn=User1,ou=Users,dc=example,dc=com;cn=User2,ou=Users,dc=example,dc=com";
    set $ldap_allowed_groups "cn=Internal Users,ou=Groups,dc=example,dc=com";

    # include the set of generic auth locations
    include /etc/nginx/auth_locations.conf;
}
```

In this sample configuration access to this internal site will be granted only to:
* _User1_
* _User2_
* any member of the _Internal Users_ group

### Caching

To limit performance hit, authentication server responses are cached by nginx - this is set in the **/__auth** location definition. Caching requires setting up the file system caching location - to do this, set it in the **nginx.conf** file, **http** section by adding e.g.:
```
proxy_cache_path /etc/nginx/cache/auth levels=1:2 keys_zone=auth:10m max_size=1g inactive=60m use_temp_path=off;
```

This will allow nginx limit the requests sent to the auth server.
