#-*- coding: utf-8 -*-
import os
import re
import time
import datetime
import logging
try:
    import hashlib
    sha1 = hashlib.sha1
except ImportError:
    import sha
    sha1 = sha.new

import config
SECRET = config.SECRET
SESSION_NAME = config.SESSION_NAME
SESSION_EXPIRE = config.SESSION_EXPIRE
from google.appengine.api import memcache

from cookies import Cookies

class Session(object):
    def __init__(self, handler, expire=None):
        self.handler = handler
        self.expire = SESSION_EXPIRE
        if expire:
            self.expire = expire

        self.sessionid = handler.request.cookies.get(SESSION_NAME, None)
        self.session = None
        if self.sessionid:
            self.session = memcache.get(self.sessionid)
        if self.session is None:
            logging.info("Invalidating session " + str(self.sessionid))
            self.sessionid = self._generate_sessionid()
            self.session = dict()
            memcache.add(self.sessionid, self.session, SESSION_EXPIRE)
            cookies = Cookies(handler)
            cookies[SESSION_NAME] = self.sessionid

    def _generate_sessionid(self):
        rand1 = os.urandom(8)
        rand2 = os.urandom(16)
        now = time.time()
        secret_key = SECRET
        sessionid = sha1('%s%s%s%s' % (rand1, now, secret_key, rand2)).hexdigest()
        return sessionid

    def _valid_seesionid(self, sessionid):
        rx = re.compile('^[0-9a-fA-F]+$')
        judge = rx.match(sessionid)
        if judge:
            return True
        return False

    def _update_cache(self):
        memcache.replace(self.sessionid, self.session, SESSION_EXPIRE)

    def get(self, key, value=None):
        if key in self.session:
            return self.session[key]
        return value

    def delete(self, key):
        if key in self.session:
            del self.session[key]
            self._update_cache()
            return True
        return False

    def __getitem__(self, key):
        if key in self.session:
            return self.session[key]
        raise KeyError(str(keyname))

    def __delitem__(self, key):
        if key in self.session:
            del self.session[key]
            logging.info("Delete from session: " + str(self.session[key]))
            self._update_cache()
            return
        raise KeyError(str(key))

    def __setitem__(self, key, value):
        self.session[key] = value
        self._update_cache()
        pass

    def __contains__(self, key):
        if key in self.session:
            return True
        return False
    
    def __repr__(self):
        return '<Session ' + self.sessionid + '>'
