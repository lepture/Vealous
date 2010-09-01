#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple OAuth

Request Params in Header
Signature Method: HMAC-SHA1
"""

__author__ = 'Marvour <marvour@gmail.com>'
__version__ = 1.0

import hmac
import time
import urllib
import urlparse
import base64
import httplib
from hashlib import sha1
from random import getrandbits

class OauthClient(object):
    def __init__(self, key, secret, token='', token_secret='', callback=''):
        self._key = key
        self._secret = secret
        self._token = token
        self._token_secret = token_secret
        self._callback = callback

    def _quote(self, s):
        return urllib.quote(str(s), '~')

    def to_dict(self, s):
        d = {}
        for item in s.split('&'):
            (key, value) = item.split('=')
            d[key] = value
        return d

    def get_oauth_params(self, url, params={}, method='GET'):
        oauth_params = {
            'oauth_consumer_key': self._key,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': int(time.time()),
            'oauth_nonce': getrandbits(64),
        }

        params.update(oauth_params)

        # generate signature {{{
        s = ''
        for k in sorted(params):
            s += self._quote(k) + '=' + self._quote(params[k]) + '&'
        msg = method + '&' + self._quote(url) + '&' + self._quote(s[:-1])
        key = self._secret + '&' + self._token_secret
        signature = base64.b64encode(hmac.new(key, msg, sha1).digest())
        # }}}

        params['oauth_signature'] = signature
        return params
    
    def to_header(self, params, realm=''):
        header = 'OAuth realm="%s"' % realm
        for k, v in params.iteritems():
            header += ',%s="%s"' % (k, v)
        return {'Authorization': header }


    def exchange_token(self, url, params={}, method='GET'):
        params = self.get_oauth_params(url, params, method)
        oauth_header = self.to_header(params)
        http_url = urlparse.urlparse(url)
        connection = httplib.HTTPConnection("%s" % http_url.hostname)
        connection.request(method, http_url.path, headers = oauth_header)

        res = connection.getresponse()
        content = res.read()
        if 200 != res.status:
            raise Exception('OAuth Request Token Error: ' + content)
        res.close()
        dic = self.to_dict(content)
        return dic

    def request_token(self, rq_url, method='GET'):
        dic = self.exchange_token(rq_url)
        self._token = dic['oauth_token']
        self._token_secret = dic['oauth_token_secret']
        return dic

    def request_auth(self, auth_url):
        if self._token:
            url = auth_url + '?' + 'oauth_token=' + self._token
        else:
            raise Exception('OAuth Request Token Not Finished')
        if self._callback:
            url += '&oauth_callback=' + self._quote(self._callback)
        return url

    def access_token(self, acs_url, method='GET'):
        if not self._token:
            raise Exception('OAuth Request Token Not Finished')
        params = {'oauth_token': self._token}
        dic = self.exchange_token(acs_url, params, method)
        self._token = dic['oauth_token']
        self._token_secret = dic['oauth_token_secret']
        return dic
    
if '__main__' == __name__:
    douban_key = ''
    douban_secret = ''
    rq_url = 'http://www.douban.com/service/auth/request_token'
    auth_url = 'http://www.douban.com/service/auth/authorize'
    client = OauthClient(douban_key, douban_secret)
    dic = client.request_token(rq_url)
    print client.request_auth(auth_url)
    s = raw_input('after agreed, enter ok>>  ')
    if 'ok' == s:
        acs_url = 'http://www.douban.com/service/auth/access_token'
        data = client.access_token(acs_url)
        print data
