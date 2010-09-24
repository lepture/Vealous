#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
AppEngine-OAuth

OAuth utility for applications on Google App Engine

See: http://0-oo.net/sbox/python-box/appengine-oauth
License: http://0-oo.net/pryn/MIT_license.txt (The MIT license)
'''

__author__ = 'dgbadmin@gmail.com'
__version__ = '0.1.0'


import hmac
import urllib
from google.appengine.api import urlfetch
from hashlib import sha1
from random import getrandbits
from time import time
from django.utils import simplejson


class AppEngineOAuth(object):
    def __init__(self, key, secret, acs_token='', acs_token_secret=''):
        self._key = key
        self._secret = secret
        self._token = acs_token
        self._token_secret = acs_token_secret

        # Be understandable which type token is (request or access)
        if acs_token == '':
            self._token_type = None
        else:
            self._token_type = 'access'


    def prepare_login(self, req_token_url):
        '''
        Return request_token, request_token_secret and params of authorize url.
        '''
        # Get request token
        params = self.get_oauth_params(req_token_url, {})
        res = urlfetch.fetch(url=req_token_url + '?' + urllib.urlencode(params),method='GET')
        self.last_response = res
        if res.status_code != 200:
            raise Exception('OAuth Request Token Error: ' + res.content)
        # Response content is request_token
        dic = self._qs2dict(res.content)
        self._token = dic['oauth_token']
        self._token_secret = dic['oauth_token_secret']
        self._token_type = 'request'

        # Get params with signature
        sig_params = {'oauth_signature': params['oauth_signature']}
        dic['params'] = urllib.urlencode(self.get_oauth_params(req_token_url,sig_params))
        return dic

    def exchange_tokens(self, acs_token_url, req_token, req_token_secret):
        self._token = req_token
        self._token_secret = req_token_secret
        self._token_type = 'request'

        params = urllib.urlencode(self.get_oauth_params(acs_token_url, {}))
        res = urlfetch.fetch(url=acs_token_url, payload=params, method='POST')
        self.last_response = res
        if res.status_code != 200:
            raise Exception('OAuth Access Token Error: ' + res.content)
        # Response content is access_token
        dic = self._qs2dict(res.content)
        self._token = dic['oauth_token']
        self._token_secret = dic['oauth_token_secret']
        self._token_type = 'access'

        return dic


    def get_oauth_params(self, url, params, method='GET'):
        oauth_params = {
            'oauth_consumer_key': self._key,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': int(time()),
            'oauth_nonce': getrandbits(64),
            'oauth_version': '1.0'}
        if self._token_type != None:
            oauth_params['oauth_token'] = self._token

        # Add other params
        params.update(oauth_params)

        # Sort and concat
        s = ''
        for k in sorted(params):
            s += self._quote(k) + '=' + self._quote(params[k]) + '&'
            msg = method + '&' + self._quote(url) + '&' + self._quote(s[:-1])
        # Maybe token_secret is empty
        key = self._secret + '&' + self._token_secret

        digest = hmac.new(key, msg, sha1).digest()
        params['oauth_signature'] = digest.encode('base64')[:-1]

        return params

    def _quote(self, s):
        return urllib.quote(str(s), '~')

    def _qs2dict(self, s):
        dic = {}  
        for param in s.split('&'):
            (key, value) = param.split('=')
            dic[key] = value
        return dic

    def _dict2qs(self, dic):
        return '&'.join(['%s="%s"' % (key, value) for key, value in dic.iteritems()]) 

    def dict2header(self, dic):
        s = ', '.join(['%s="%s"' % (k, self._quote(v)) for k, v in dic.iteritems() if k.startswith('oauth_')]) 
        auth_header = 'OAuth realm="", %s' % s
        return {'Authorization': auth_header}

class Twitter(object):
    def __init__(self):
        self._api_url = 'https://twitter.com'
        self._oauth = None

    def update(self, msg):
        path = '/statuses/update.json'
        res = self._post(path, {'status': msg})
        print res.content
        if 201 != res.status_code:
            raise Exception('Twitter Update Status Error : ' + str(res.status_code))
        return res

    def set_oauth(self, key, secret, acs_token='', acs_token_secret=''):
        self._oauth = AppEngineOAuth(key, secret, acs_token, acs_token_secret)
    def prepare_oauth_login(self):
        dic = self._oauth.prepare_login(self._api_url + '/oauth/request_token/')
        dic['url'] = self._api_url + '/oauth/authorize?' + dic['params']
        return dic

    def exchange_oauth_tokens(self, req_token, req_token_secret):
        dic = self._oauth.exchange_tokens(
            self._api_url + '/oauth/accsess_token/',
            req_token, req_token_secret)
        return dic

    def _post(self, path, params):
        url = self._api_url + path
        if not self._oauth:
            raise Exception('Twitter Not Authed')
        dic = self._oauth.get_oauth_params(url, params, 'POST')
        print dic
        headers = self._oauth.dict2header(dic)
        print headers
        try:
            res = urlfetch.fetch(url=url, payload=urllib.urlencode(dic),method='POST', headers=headers)
        except urlfetch.DownloadError, e:
            raise Exception('Twitter Post DownloadError : ' + str(e))
        return res

    def _get(self, path, params):
        url = self._api_url + path
        if not self._oauth:
            raise Exception('Twitter Not Authed')
        params = self._oauth.get_oauth_params(url, params, 'GET')
        url += '?' + urllib.urlencode(params)
        try:
            res = urlfetch.fetch(url=url,method='GET')
        except urlfetch.DownloadError, e:
            raise Exception('Twitter GET DownloadError : ' + str(e))
        return res
