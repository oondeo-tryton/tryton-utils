import os
import sys

DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
    '..', 'trytond', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

from trytond.config import config
from trytond.application import app


class Application(object):
    '''
    This class wraps trytond's WSGI app in order to be able to setup
    the configuration file on the first call.

    mod_wsgi does not allow passing environment variables (those obtained via
    os.environ) for several reasons explained in its documentation. So we had
    to workaround that limitation somehow and this class allows administrators
    to add 'Set Env trytond.config /etc/trytond/whatever.conf' to Apache's
    virtual host.
    '''
    def __init__(self):
        self.loaded = False

    def __call__(self, environ, start_response):
        if not self.loaded:
            if environ.get('trytond.config'):
                config.update_etc(environ.get('trytond.config'))
            else:
                config.update_etc(os.environ.get('TRYTOND_CONFIG'))

            self.loaded = True
        return app.wsgi_app(environ, start_response)

# WSGI standard requires the variable to be named 'application' and mod_wsgi
# does not allow that value to be overriden.

application = Application()
