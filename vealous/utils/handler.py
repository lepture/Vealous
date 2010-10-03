#!/usr/bin/env python
#
# Copyright 2010 by Marvour
#
# Under the BSD License

"""
A simple handler with cookie and session supporting.

Here is a simple example:

    from handler import WebHandler
    class MainPage(WebHandler):
        def get(self):
            self.cookies['cookie1'] = 'webhandler'
            self.cookies.set_cookie('cookie2','webhandler')
            self.session['session1'] = 'session'
            self.session.set_session('session1', 'session')
"""

__AUTHOR__ = 'marvour <marvour@gmail.com>'
__VERSION__ = '1.0'

import os
import logging
import time
import datetime
try:
    import hashlib
    sha1 = hashlib.sha1
except ImportError:
    import sha
    sha1 = sha.new
from Cookie import BaseCookie
from google.appengine.ext import webapp
from google.appengine.api import memcache

SECRET = 'secret'
SESSION_NAME = 'sessionid'
SESSION_EXPIRE = 7200


class WebHandler(webapp.RequestHandler):
    def initialize(self, request, response):
        self.request = request
        self.response = response
        self.cookie = Cookie(request, response)
        self.session = Session(request, response)

class Cookie(object):
    def __init__(self, request, response, **policy):
        self.cookies = request.cookies

        self.request = request
        self.response = response
        self.policy = policy

    def __getitem__(self, key):
        if key in self.cookies:
            return self.cookies[key]

    def __setitem__(self, key, item):
        self.set_cookie(key, item, **self.policy)

    def __delitem__(self, key):
        self.delete_cookie(key, **self.policy)

    def __contains__(self, key):
        return key in self.cookies

    def keys(self):
        return self.cookies.key()

    def set_cookie(self, key, value='', max_age=None,
                   path='/', domain=None, secure=None, 
                   httponly=False, version=None, comment=None):
        """
        Set (add) a cookie for the response
        """
        if self.request.environ.get('HTTPS', '').lower() in ['on', 'true']:
            secure = True
        cookies = BaseCookie()
        cookies[key] = value
        for var_name, var_value in [
            ('max-age', max_age),
            ('path', path),
            ('domain', domain),
            ('secure', secure),
            ('HttpOnly', httponly),
            ('version', version),
            ('comment', comment),
            ]:
            if var_value is not None and var_value is not False:
                cookies[key][var_name] = str(var_value)
            if max_age is not None:
                cookies[key]['expires'] = max_age
        header_value = cookies[key].output(header='').lstrip()
        self.response.headers._headers.append(('Set-Cookie', header_value))

    def delete_cookie(self, key, path='/', domain=None):
        self.set_cookie(key, '', path=path, domain=domain, max_age=0)


class Session(object):
    def __init__(self, request, response):
        sessionid = request.cookies.get(SESSION_NAME, None)
        session = None
        if sessionid:
            session = memcache.get(sessionid)
        if session is None:
            logging.info("Invalidating session " + str(sessionid))
            sessionid = self._generate_sessionid()
            session = dict()
            memcache.add(sessionid, session, SESSION_EXPIRE)
            cookie = Cookie(request, response)
            cookie.set_cookie(SESSION_NAME, sessionid, max_age=SESSION_EXPIRE)
        self.sessionid = sessionid
        self.session = session

    def _update_cache(self):
        memcache.replace(self.sessionid, self.session, SESSION_EXPIRE)

    def _generate_sessionid(self):
        rand1 = os.urandom(8)
        rand2 = os.urandom(16)
        now = time.time()
        secret_key = SECRET
        sessionid = sha1('%s%s%s%s' % (rand1, now, secret_key, rand2)).hexdigest()
        return sessionid

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
