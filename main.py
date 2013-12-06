#!/usr/bin/env python

__author__  = 'Haydn Strauss'
__website__ = 'www.beecoss.com'

import os, sys

# Third party libraries path must be fixed before importing webapp2
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'external'))

import webapp2

import routes
from admin import routes as admin_routes
import config
from lib.error_handler import handle_error

webapp2_config = config.config

app = webapp2.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), config=webapp2_config)

# for status_int in app.config['error_templates']:
#     app.error_handlers[status_int] = handle_error

routes.add_routes(app)
admin_routes.add_routes(app)


