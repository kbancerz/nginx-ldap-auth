import json
import random
import string


DEFAULT_CONFIG_FILE = 'config.json'
DEFAULT_SECRET_LENGTH = 32
DEFAULT_SESSION_EXPIRATION = 86400  # session lasts 1 day by default
GROUPS_CACHE_MAX_AGE = 300  # cache user's groups query for 5 minutes

CONFIG_TEMPLATE = {
    'basic_authentication': {
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
    'ingress': {
        'ignored_addresses': [],
    },
}


class Config(object):
    def __init__(self, config_data):
        self._config_dict = json.loads(config_data)

        basic = self._config_dict.get('basic_authentication', {})
        ldap = self._config_dict.get('ldap', {})
        session = self._config_dict.get('session', {})
        pages = self._config_dict.get('pages', {})
        ingress = self._config_dict.get('ingress', {})

        self.basic_enabled = basic.get('enabled', False)
        self.basic_users = basic.get('users', None)

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

        self.ignored_addresses = ingress.get('ignored_addresses', None)

    @staticmethod
    def get_sample_config(indent):
        return json.dumps(CONFIG_TEMPLATE, indent=indent)
