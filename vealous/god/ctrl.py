#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run

from god.main import *
from god.console import *

apps = webapp.WSGIApplication(
    [
        ('/god', dashboard),
        ('/god/login', login),
        ('/god/logout', logout),
        ('/god/chpasswd', chpasswd),
        ('/god/setting', vigo_setting),
        ('/god/article', view_article),
        ('/god/article/add', add_article),
        ('/god/article/edit', edit_article),
        ('/god/melody', view_melody),
        ('/god/melody/add', add_melody),
        ('/god/melody/edit', edit_melody),
        ('/god/note/add', add_note),
        ('/god/note/delete', delete_note),

        ('/god/console/memcache', console_memcache),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
