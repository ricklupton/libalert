from ConfigParser import RawConfigParser

def parse_weekday_set(text):
    """Map string containing digits 1-7 to a set of integers"""
    days = map(int, text)
    return set(days)

class LibalertConfig(object):
    def __init__(self, config_filename):
        self.config_filename = config_filename
        self.users = {}
        self.libraries = {}

        # ConfigParser with some default values
        config = RawConfigParser({
            'admin-name': 'Admin',    # not really required so set default
            'returns-days': '1234567', # can return books every day of week
        })
        config.read(config_filename)
        usernames = config.get('libalert', 'users').split(',')
        for username in usernames:
            # Load all user settings
            username = username.strip()
            self.users[username] = {
                'email':       config.get(username, 'email'),
                'number':      config.get(username, 'number'),
                'pin':         config.get(username, 'pin'),
                'library':     config.get(username, 'library'),
                'days-notice': config.getint(username, 'days-notice'),
                'returns-days':parse_weekday_set(config.get(username, 'returns-days'))
            }
            
            # Load library details
            library = self.users[username]['library']
            if library not in self.libraries:
                self.libraries[library] = {
                    'type': config.get(library, 'server-type'),
                    'url':  config.get(library, 'server-url'),
                }
                
        self.admin_name    = config.get('libalert', 'admin-name')
        self.admin_email   = config.get('libalert', 'admin-email')
        self.smtp_server   = config.get('libalert', 'smtp-server')
        self.smtp_email    = config.get('libalert', 'smtp-email')
        self.smtp_password = config.get('libalert', 'smtp-password')
        self.debug_level   = config.getint('libalert', 'debug-level')
