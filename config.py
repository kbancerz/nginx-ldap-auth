import json
import random
import string


DEFAULT_CONFIG_FILE = 'config.json'
DEFAULT_SECRET_LENGTH = 32
DEFAULT_SESSION_EXPIRATION = 86400  # session lasts 1 day by default
GROUPS_CACHE_MAX_AGE = 300  # cache user's groups query for 5 minutes

CONFIG_TEMPLATE = {
    'basic': {
        'enabled': False,
        'users': {
            'sample_user': {
                'password': '/HDrxmQBj6Xl7/gl6UwrcZKq7fjjH1knVUAxwX0v/'
                            'Yvb3zHET3+lfZ+tpAN/nYGp',  # welcome
                'groups': ['TestGroup'],
            }
        }
    },
    'ldap': {
        'enabled': True,
        'host': 'ldap.example.com',
        'port': 389,
        'username': 'admin',
        'password': 'password',
        'user_attr': 'mail',
        'user_base_dn': 'ou=users,dc=example,dc=com',
        'group_base_dn': 'ou=groups,dc=example,dc=com',
        'group_cache_max_age': GROUPS_CACHE_MAX_AGE,
    },
    'session': {
        'cookie_session': 'EXAMPLE_COM_SSO',
        'cookie_redirect': 'EXAMPLE_COM_REDIRECT',
        'cookie_domain': '.example.com',
        'cookie_secret': ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(DEFAULT_SECRET_LENGTH)),
        'cookie_max_age': DEFAULT_SESSION_EXPIRATION,
    },
    'pages': {
        'login_template': './pages/templates/login.html.j2',
        'noauth_template': './pages/templates/noauth.html.j2',
        'static_root': './pages/static',
        'fallback_redirect': 'https://internal.example.com',
    },
    'passthrough': {
        'ignored_ingress': [],
        'ignored_remote': [],
    },
}


class Config(object):
    def __init__(self, config_data):
        self._config_dict = json.loads(config_data)

        basic = self._config_dict.get('basic', {})
        ldap = self._config_dict.get('ldap', {})
        session = self._config_dict.get('session', {})
        pages = self._config_dict.get('pages', {})
        passthrough = self._config_dict.get('passthrough', {})

        self.basic_enabled = basic.get('enabled', False)
        self.basic_users = basic.get('users', {})

        self.ldap_enabled = ldap.get('enabled', False)
        self.host = ldap.get('host', None)
        self.port = ldap.get('port', None)
        self.username = ldap.get('username', None)
        self.password = ldap.get('password', None)
        self.user_attr = ldap.get('user_attr', None)
        self.user_base_dn = ldap.get('user_base_dn', None)
        self.group_base_dn = ldap.get('group_base_dn', None)
        self.group_cache_max_age = int(ldap.get('group_cache_max_age', 0))

        self.cookie_session = session.get('cookie_session', None)
        self.cookie_redirect = session.get('cookie_redirect', None)
        self.cookie_domain = session.get('cookie_domain', None)
        self.cookie_secret = session.get('cookie_secret', None)
        self.cookie_max_age = int(session.get('cookie_max_age', 0))

        self.login_template = pages.get('login_template', None)
        self.noauth_template = pages.get('noauth_template', None)
        self.static_root = pages.get('static_root', None)
        self.fallback_redirect = pages.get('fallback_redirect', None)

        self.ignored_ingress = passthrough.get('ignored_ingress', [])
        self.ignored_remote = passthrough.get('ignored_remote', [])

    def check_consistency(self):
        invalid = []

        # check Basic authentication configuration
        if self.basic_enabled:
            if not self.basic_users:
                invalid.append('basic.users')
            elif not isinstance(self.basic_users, dict):
                invalid.append('basic.users')
            else:
                for user, data in self.basic_users.items():
                    if not isinstance(data.get('password', None), str):
                        invalid.append(f'basic.users.{user}.password')
                    if not isinstance(data.get('groups', None), list):
                        invalid.append(f'basic.users.{user}.groups')

        # check LDAP authentication configuration
        if self.ldap_enabled:
            if self.host is None:
                invalid.append('ldap.host')
            if self.port is None:
                invalid.append('ldap.port')
            if self.username is None:
                invalid.append('ldap.username')
            if self.password is None:
                invalid.append('ldap.password')
            if self.user_attr is None:
                invalid.append('ldap.user_attr')
            if self.group_base_dn is None:
                invalid.append('ldap.group_base_dn')
            if self.group_cache_max_age is None:
                invalid.append('ldap.group_cache_max_age')

        # check HTTP session configuration
        if self.cookie_session is None:
            invalid.append('session.cookie_session')
        if self.cookie_redirect is None:
            invalid.append('session.cookie_redirect')
        if self.cookie_domain is None:
            invalid.append('session.cookie_domain')
        if self.cookie_secret is None:
            invalid.append('session.cookie_secret')
        if self.cookie_session is None:
            invalid.append('session.cookie_session')

        # check pages configuration
        if self.login_template is None:
            invalid.append('pages.login_template')
        if self.noauth_template is None:
            invalid.append('pages.noauth_template')
        if self.static_root is None:
            invalid.append('pages.static_root')
        if self.fallback_redirect is None:
            invalid.append('pages.fallback_redirect')

        return invalid

    @staticmethod
    def get_sample_config(indent):
        return json.dumps(CONFIG_TEMPLATE, indent=indent)
