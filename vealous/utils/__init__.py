#-*- coding: utf-8 -*-

import re
import logging
from urllib2 import quote, unquote
from google.appengine.api import users

from config import LOGIN_URL

def is_mobile(request):
    ua = request.headers.get('User-Agent', 'bot')
    if re.search('ipod|mobile|opera mini|blackberry|webos|ucweb|midp', ua.lower()):
        logging.info('mobile device visited this site : ' + ua)
        return True
    return False

def is_spider(request):
    ua = request.headers.get('User-Agent', 'bot')
    _reg = 'bot|crawl|spider|slurp|search|lycos|robozilla'
    if re.search(_reg, ua.lower()):
        return True
    return False


def be_god(func):
    def decorator(handler, *args, **kwargs):
        auth = handler.session.get('auth',0)
        gauth = 0
        if users.is_current_user_admin():
            gauth = 1
        if 0 == auth and 0 == gauth:
            return handler.redirect('%s?to=%s' % (LOGIN_URL, quote(handler.request.url)))
        return func(handler, *args, **kwargs)
    return decorator

def safeunquote(slug):
    try:
        slug = unquote(slug)
        if isinstance(slug, str):
            return slug.decode('utf-8')
        assert isinstance(slug, unicode)
        return slug
    except:
        return slug

class Paginator(object):
    def __init__(self, data, count=10, page=1):
        self.data = data
        self.count = count
        self.page = self._make_int(page)
        self.item_num = self.item_num()
        self.page_num = self.page_num()

    def item_num(self):
        try:
            num = self.data.count()
        except (AttributeError, TypeError):
            num = len(self.data)
        return num
    
    def page_num(self):
        item_num = self.item_num
        count = self.count
        if item_num % count:
            return item_num / count + 1
        return item_num / count
    
    @property
    def has_next(self):
        return self.page < self.page_num

    @property
    def next_num(self):
        return int(self.page + 1)
    
    @property
    def has_previous(self):
        return self.page > 1
    
    @property
    def previous_num(self):
        return int(self.page - 1)
    
    def page_range(self):
        p = self.page
        pn = self.page_num
        return [i for i in range(p-4, p+5) if i in range(1, pn+1)]

    @property
    def show_first(self):
        return self.page > 5

    @property
    def show_first_dash(self):
        return self.page > 5 and self.page != 6

    @property
    def show_last(self):
        return self.page_num - self.page > 5

    @property
    def show_last_dash(self):
        n = self.page_num - self.page
        return n > 5 and n != 6

    def get_items(self):
        limit = self.count
        offset = (self.page - 1)*limit
        try:
            objects = self.data.fetch(limit, offset)
        except (AttributeError, TypeError), e:
            objects = self.data[offset:limit*self.page]
        return objects
    object_list = property(get_items)

    def _make_int(self, num):
        try:
            num = int(num)
        except:
            return 1
        if num <= 1:
            return 1
        return num
