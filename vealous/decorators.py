#-*- coding: utf-8 -*-

import urllib

from utils.sessions import Session
from config import LOGIN_URL

def be_god(func):
    def decorator(handler, *args, **kwargs):
        session = Session(handler)
        auth = session.get('auth',0)
        if 1 != auth:
            return handler.redirect('%s?to=%s' % (LOGIN_URL, urllib.quote(handler.request.url)))
        return func(handler, *args, **kwargs)
    return decorator
