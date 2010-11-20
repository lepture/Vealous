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

        if count <= 1:
            self.count = 1
        else:
            self.count = int(count)

        try:
            page = int(page)
        except:
            page = 1
        if page <=1:
            self.page = 1
        else:
            self.page = page

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
        p1 = self.page
        p2 = self.page_num
        if p1 < p2:
            return True
        return False

    @property
    def next_num(self):
        return int(self.page + 1)
    
    @property
    def has_previous(self):
        p1 = self.page
        if p1 > 1:
            return True
        return False
    
    @property
    def previous_num(self):
        return int(self.page - 1)
    
    def page_range(self, num=4):
        current = self.page
        xlist = range(current-num, current+num+1)
        plist = range(1, self.page_num + 1)
        data = []
        for p in xlist:
            if p in plist:
                data.append(p)
        return data

    @property
    def show_first(self):
        if self.page > 5:
            return True
        return False

    @property
    def show_first_dash(self):
        p = self.page
        if p > 5 and p != 6:
            return True
        return False

    @property
    def show_last(self):
        n = self.page_num - self.page
        if n > 5:
            return True
        return False

    @property
    def show_last_dash(self):
        n = self.page_num - self.page
        if n > 5 and n != 6:
            return True
        return False

    def get_items(self):
        limit = self.count
        offset = (self.page - 1)*limit
        try:
            mvdata = self.data.fetch(limit, offset)
        except (AttributeError, TypeError), e:
            mvdata = self.data[offset:limit*self.page]
        return mvdata
    object_list = property(get_items)
