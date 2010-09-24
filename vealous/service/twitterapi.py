# -*- coding: utf-8 -*-
import logging
from google.appengine.api import urlfetch
from libs.appoauth import AppEngineOAuth
import urllib

API_URL = 'https://twitter.com/'

class Twitter(object):
    def __init__(self, key, secret):
        self._key = key
        self._secret = secret
        self._oauth = None

    def set_oauth(self, acs_token='', acs_token_secret=''):
        self._oauth = AppEngineOAuth(self._key, self._secret, acs_token, acs_token_secret)
    
    def set_oauth_qs(self, qs = ''):
        self._oauth = AppEngineOAuth(self._key, self._secret)
        dic = self._oauth._qs2dict(qs)
        acs_token = dic['oauth_token']
        acs_token_secret = dic['oauth_token_secret']
        self._oauth = AppEngineOAuth(self._key, self._secret, acs_token, acs_token_secret)

    def prepare_oauth_login(self):
        if not self._oauth:
            raise Exception('Twitter Not Set Oauth')
        dic = self._oauth.prepare_login(API_URL + 'oauth/request_token')
        dic['url'] = API_URL + 'oauth/authorize?' + dic['params']
        return dic

    def exchange_oauth_tokens(self, req_token, req_token_secret):
        if not self._oauth:
            raise Exception('Twitter Not Set Oauth')
        acs_url = API_URL + 'oauth/access_token'
        dic = self._oauth.exchange_tokens(acs_url, req_token, req_token_secret)
        return self._oauth._dict2qs(dic)

    def update(self, msg):
        res_url = API_URL + 'statuses/update.json'
        params = {'status': msg}
        res = self._post(res_url, params)
        if 200 != res.status_code:
            raise Exception('Twitter Update Status Error : ' + str(res.status_code))
        return res.content

    def _post(self, res_url, params ):
        dic = self._oauth.get_oauth_params(res_url, {}, 'POST')
        headers = self._oauth.dict2header(dic)
        headers['Content-Type'] = 'application/json; charset=utf-8'
        res = urlfetch.fetch(
            url=res_url, 
            payload=urllib.urlencode(params), 
            method='POST',
            headers=headers)
        return res
