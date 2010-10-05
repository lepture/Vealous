#-*- coding: utf-8 -*-

import os
import logging
from urllib2 import quote
from django.utils.simplejson import loads as parse_json
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import memcache
from google.appengine.api import urlfetch

from utils.render import render
from utils import Paginator
from libs import twitter
from utils import is_mobile
import dbs

import config

def get_path(request, name):
    if is_mobile(request):
        path = os.path.join(config.ROOT, 'tpl','mobile' , name)
        return path
    path = os.path.join(config.ROOT, 'tpl', config.THEME, name)
    return path

class UtilsDict(webapp.RequestHandler):
    def get(self):
        rdic = {}
        p = self.request.get('p',1)
        rdic['navs'] = dbs.Melody.get_all('nav')
        rdic['links'] = dbs.Melody.get_all('link')
        data = dbs.DictBook.get_all()
        rdic['mvdata'] = Paginator(data, 30, p)
        path = get_path(self.request, 'utils_dict.html')
        self.response.out.write(render(path,rdic))

class UtilsTwitter(webapp.RequestHandler):
    def get(self):
        rdic = {}
        rdic['navs'] = dbs.Melody.get_all('nav')
        rdic['links'] = dbs.Melody.get_all('link')
        rdic['tweets'] = self.tweets()
        path = get_path(self.request, 'utils_twitter.html')
        self.response.out.write(render(path,rdic))

    def tweets(self):
        username = dbs.Vigo.get('twitter')
        if not username:
            return []
        data = memcache.get('twitter$status$' + username)
        if data is not None:
            return data
        api = twitter.Api()
        data = api.GetUserTimeline(screen_name=username, count=30)
        memcache.set('twitter$status$' + username, data, 240)
        return data

apps = webapp.WSGIApplication(
    [
        ('/utils/dict', UtilsDict),
        ('/utils/twitter', UtilsTwitter),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
