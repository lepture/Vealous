#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.api import memcache
from django.utils.simplejson import dumps
import urllib

from service.disqus import Disqus
from service.oauth import OauthClient
from utils.sessions import Session
from decorators import be_god
import dbs
from config import SITE_URL
from config import douban_key, douban_secret


class disqus_moderate(webapp.RequestHandler):
    @be_god
    def get(self):
        action = self.request.get('action',None)
        post_id = self.request.get('post_id',None)
        forum_key = dbs.Vigo.get('forum_key')
        disqus_key = dbs.Vigo.get('disqus_key')
        self.response.headers['Content-Type'] = 'application/json'
        if action and post_id and forum_key and disqus_key:
            d = Disqus(disqus_key)
            data = d.moderate_post(forum_key,post_id,action)
            if data['succeeded']:
                memcache.delete('god/comments')
            return self.response.out.write(dumps(data))
        data = {'succeeded': False}
        return self.response.out.write(dumps(data))


class douban_request_auth(webapp.RequestHandler):
    @be_god
    def get(self):
        rq_url = 'http://www.douban.com/service/auth/request_token'
        auth_url = 'http://www.douban.com/service/auth/authorize'
        callback = SITE_URL + '/god/third/douban/auth'
        client = OauthClient(douban_key, douban_secret, callback=callback)
        dic = client.request_token(rq_url)
        to = client.request_auth(auth_url)
        session = Session(self)
        session['douban'] = dic
        dbs.Vigo.set('xxxx', str(dic))
        return self.redirect(to)

class douban_access_token(webapp.RequestHandler):
    @be_god
    def get(self):
        oauth_douban = dbs.Vigo.get('oauth_douban')
        if oauth_douban:
            return self.response.out.write('authed')
        session = Session(self)
        douban = session.get('douban','')
        if not douban:
            session['message'] = 'Request Douban access token failed'
            return self.redirect('/god?from=douban')
        token = douban['oauth_token']
        token_secret = douban['oauth_token_secret']
        client = OauthClient(douban_key, douban_secret, token, token_secret)
        acs_url = 'http://www.douban.com/service/auth/access_token'
        dic = client.access_token(acs_url)
        # dic: 'oauth_token', 'oauth_token_secret', 'douban_user_id'
        dbs.Vigo.set('oauth_douban',urllib.urlencode(dic)) 
        session['message'] = 'Douban Auth Success'
        return self.redirect('/god?from=douban')
