#!/usr/bin/env python

from google.appengine.ext import webapp
from Cookie import BaseCookie

class WebHandler(webapp.RequestHandler):
    @property
    def cookies(self):
        cookies = self.request.cookies
        cookies.__setitem__ = self._set_cookie
        cookies.set_cookie = self._set_cookie
        cookies.__delitem__ = self._del_cookie
        cookies.del_cookie = self._del_cookie
        return cookies

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


class test(WebHandler):
    def get(self):
        cookie = self.cookies.get('key', None)
        if not cookie:
            self.cookies['key'] = 'hello'
        del self.cookies['key']
        self.cookies.set_cookie('key','test', secure=True)
        self.response.out.write(cookie)

apps = webapp.WSGIApplication(
    [
        ('/test', test),
    ],
    debug = True,
)

if '__main__' == __name__:
    from google.appengine.ext.webapp.util import run_wsgi_app as run
    run(apps)
