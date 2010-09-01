#-*- coding: utf-8 -*-

import os
import logging
from google.appengine.ext import webapp
from google.appengine.api import memcache

from decorators import be_god
from utils.render import render
import config

def get_path(name):
    path = os.path.join(config.ROOT, 'god', 'tpl', name)
    return path

class console_memcache(webapp.RequestHandler):
    @be_god
    def get(self):
        action = self.request.get('action','none')
        key = self.request.get('key',None)
        if 'flush' == action:
            memcache.flush_all()
            logging.info('flash all memcache')
            return self.redirect('/god/console/memcache')
        if 'delete' == action and key:
            memcache.delete(key)
            logging.info('delete memcache key: ' + str(key))
            return self.redirect('/god/console/memcache')
        elif 'display' == action and key:
            result = memcache.get(key)
        else:
            result = ''
        rdic = {}
        memstat = memcache.get_stats()
        rdic['memstat'] = memstat
        rdic['result'] = result
        path = get_path('memcache.html')
        return self.response.out.write(render(path,rdic))
