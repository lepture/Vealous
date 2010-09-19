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
from UserDict import UserDict
from google.appengine.ext import webapp
from google.appengine.api import memcache

SECRET = 'secret'
SESSION_NAME = 'sessionid'
SESSION_EXPIRE = 7200


class WebHandler(webapp.RequestHandler):
    @property
    def cookies(self):
        cookies = self.request.cookies
        cookies.__setitem__ = self._set_cookie
        cookies.__delitem__ = self._del_cookie
        cookies.set_cookie = self._set_cookie
        cookies.del_cookie = self._del_cookie
        return cookies

    @property
    def session(self):
        session = self.__session()
        session.__getitem__ = self._get_session
        session.__setitem__ = self._set_session
        session.__delitem__ = self._del_session
        session.set_session = self._set_session
        session.del_session = self._del_session
        return session

    def _set_cookie(self, key, value='', max_age=None,
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

    def _del_cookie(self, key, path='/', domain=None):
        self._set_cookie(key, '', path=path, domain=domain, max_age=0)

    def __session(self):
        sessionid = self.request.cookies.get(SESSION_NAME, None)
        session = None
        if sessionid:
            session = memcache.get(sessionid)
        if session is None:
            logging.info("Invalidating session " + str(sessionid))
            sessionid = self._generate_sessionid()
            session = UserDict()
            memcache.add(sessionid, session, SESSION_EXPIRE)
            self._set_cookie(SESSION_NAME,sessionid)
        return session

    def _get_session(self, key):
        session = self.__session()
        if key in session:
            return session[key]
        logging.error('Session Key Error, key not existed: ' + str(key))
        return None

    def _set_session(self, key, value):
        session = self.__session()
        session[key] = value
        self._update_cache(session)

    def _del_session(self, key):
        session = self.__session()
        if key in session:
            del session[key]
            self._update_cache(session)
            return True
        return False

    def _update_cache(self, session):
        sessionid = self.request.cookies.get(SESSION_NAME, None)
        memcache.replace(sessionid, session, SESSION_EXPIRE)

    def _generate_sessionid(self):
        rand1 = os.urandom(8)
        rand2 = os.urandom(16)
        now = time.time()
        secret_key = SECRET
        sessionid = sha1('%s%s%s%s' % (rand1, now, secret_key, rand2)).hexdigest()
        return sessionid
