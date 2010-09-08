#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run

from service.main import *
from god.main import *
from god.third import *
from god.console import *

apps = webapp.WSGIApplication(
    [
        ('/', index),
        ('/search', search),
        ('/a/(.*)', article),
        ('/k/(.*)', keyword_article),
        ('/s5/(.*)', melody_s5),
        ('/feed', atom),
        ('/feed.atom', atom),
        ('/feed.rss', rss),
        ('/sitemap.xml', sitemap),

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

        ('/god/third/disqus_moderate', disqus_moderate),
        ('/god/third/douban/request', douban_request_auth),
        ('/god/third/douban/auth', douban_access_token),
        ('/god/third/douban/miniblog', douban_miniblog),

        ('/god/console/memcache', console_memcache),

        ('/(.*)/', redirect),
        ('.*', error404),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
