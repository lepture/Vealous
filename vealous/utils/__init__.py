#-*- coding: utf-8 -*-

import re
import logging
from urllib2 import quote

from config import LOGIN_URL

def is_mobile(request):
    ua = request.headers.get('User-Agent', 'bot')
    if re.search('ipod|mobile|opera mini|blackberry|webos|ucweb|midp', ua.lower()):
        logging.info('mobile device visited this site : ' + ua)
        return True
    return False

def be_god(func):
    def decorator(handler, *args, **kwargs):
        auth = handler.session.get('auth',0)
        if 1 != auth:
            return handler.redirect('%s?to=%s' % (LOGIN_URL, quote(handler.request.url)))
        return func(handler, *args, **kwargs)
    return decorator
