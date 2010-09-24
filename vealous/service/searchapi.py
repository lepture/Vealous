# -*- coding: utf-8 -*-

import logging
from google.appengine.api import urlfetch
from urllib2 import quote
from django.utils.simplejson import loads as parse_json

API_URL = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=filtered_cse&cx=%(cx)s&q=%(q)s&start=%(start)s'

def gsearch(cx, q, start):
    try:
        q = quote(q.encode('utf-8'))
    except:
        q = quote(q)
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
    gres = parse_json(res.content)
    if 200 != gres['responseStatus']:
        logging.error('Search responseStatus Error: ' + str(gres['responseDetails']))
        raise Exception('Search responseStatus Error: ' + str(gres['responseDetails']))
    return gres['responseData']
