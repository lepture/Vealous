# -*- coding: utf-8 -*-

import logging
from google.appengine.api import urlfetch
from django.utils.simplejson import loads as parse_json

API_URL = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=8&cx=%(cx)s&q=%(q)s&start=%(start)s'

def gsearch(cx, q, start):
    gdic = dict(cx=cx,q=q,start=start)
    url = API_URL % gdic
    try:
        res = urlfetch.fetch(url)
    except urlfetch.DownloadError, e:
        logging.error('Search Download Error: ' + str(e))
        raise urlfetch.DownloadError
    if 200 != res.status_code:
        logging.error('Search Status Error: ' + str(res.status_code))
        raise Exception('Search Status Error: ' + str(res.status_code))
    content = res.content
    return content
