# -*- coding: utf-8 -*-
import logging
from google.appengine.api import urlfetch
from libs.appoauth import AppEngineOAuth

AUTH_URL = 'http://www.douban.com/service/auth/'
API_URL = 'http://api.douban.com/'

def _atom(content):
    atom = '<?xml version="1.0" encoding="UTF-8"?>'
    atom += '<entry xmlns:ns0="http://www.w3.org/2005/Atom" xmlns:db="http://www.douban.com/xmlns/">'
    atom += '<content>'
    atom += content.encode('utf-8') + ' via Vealous'
    atom += '</content></entry>'
    return atom

class Douban(object):
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
            raise Exception('Douban Not Set Oauth')
        dic = self._oauth.prepare_login(AUTH_URL + 'request_token')
        dic['url'] = AUTH_URL + 'authorize?' + dic['params']
        return dic

    def exchange_oauth_tokens(self, req_token, req_token_secret):
        if not self._oauth:
            raise Exception('Douban Not Set Oauth')
        acs_url = AUTH_URL + 'access_token'
        dic = self._oauth.exchange_tokens(acs_url, req_token, req_token_secret)
        return self._oauth._dict2qs(dic)

    def update(self, msg):
        res_url = API_URL + 'miniblog/saying'
        body = _atom(msg)
        res = self._post(res_url, body)
        if 201 != res.status_code:
            raise Exception('Douban Miniblog Status Error : ' + str(res.status_code))
        return res.content

    def _post(self, res_url, body):
        dic = self._oauth.get_oauth_params(res_url, {}, 'POST')
        headers = self._oauth.dict2header(dic)
        headers['Content-Type'] = 'application/atom+xml; charset=utf-8'
        res = urlfetch.fetch(url=res_url, payload=body, method='POST', headers=headers)
        return res

