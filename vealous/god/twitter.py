#-*- coding: utf-8 -*-

import os
import logging
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.ext import webapp
from google.appengine.api import memcache, urlfetch
from google.appengine.ext.webapp import template
from django.utils import simplejson

from libs import twitter
from decorators import be_god
from utils.render import render
from utils.sessions import Session
import config
import dbs

week = 604800

#register = template.create_template_register()
#template.register_template_library('god.twitter')

class Twitter(object):
    def __init__(self, token=None):
        self.consumer = twitter.oauth.Consumer(config.twitter_key, config.twitter_secret)
        self.token = token
        self.method = twitter.oauth.SignatureMethod_HMAC_SHA1()

    def set_qs_token(self, qs):
        self.token = twitter.oauth.Token.from_string(qs)

    def get_url(self, url, method='GET', param={}):
        req = twitter.oauth.Request.from_consumer_and_token(
            self.consumer, token=self.token, http_method=method,
            http_url = url, parameters=param)
        req.sign_request(self.method, self.consumer, self.token)
        return req.to_url()
    def fetch(self, url):
        try:
            res = urlfetch.fetch(url)
        except urlfetch.DownloadError, e:
            logging.error('Twitter: ' + str(e))
            raise Exception('Twitter: ' + str(e))
        return res.content
    def set_qs_api(self, qs):
        self.token = twitter.oauth.Token.from_string(qs)
        api = twitter.Api(self.consumer.key, self.consumer.secret,
                          self.token.key, self.token.secret)
        return api

def get_path(ua, name):
    path = os.path.join(config.ROOT, 'god', 'tpl', name)
    return path

class Dashboard(webapp.RequestHandler):
    @be_god
    def get(self):
        ua = self.request.headers.get('User-Agent', 'bot')
        path = get_path(ua, 'twitter_dashboard.html')
        rdic = {}
        source = self.request.get('from', None)
        message = ''
        if source:
            session = Session(self)
            message = session.get('message','')
            session.delete('message')
        rdic['message'] = message
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.redirect('/god/twitter/login')
        api = Twitter().set_qs_api(qs)
        return self.response.out.write(render(path, rdic))

class Login(webapp.RequestHandler):
    @be_god
    def get(self):
        auth = Twitter()
        url = auth.get_url(twitter.REQUEST_TOKEN_URL)
        qs = auth.fetch(url)
        session = Session(self)
        session['twitter_qs'] = qs
        auth.set_qs_token(qs)
        to = auth.get_url(twitter.AUTHORIZATION_URL)
        return self.redirect(to)

class Auth(webapp.RequestHandler):
    @be_god
    def get(self):
        qs = dbs.Vigo.get('oauth_twitter')
        if qs:
            return self.response.out.write('authed')
        session = Session(self)
        qs = session.get('twitter_qs','')
        if not qs:
            session['message'] = 'Request Twitter access token failed'
            return self.redirect('/god?from=twitter')
        auth = Twitter()
        auth.set_qs_token(qs)
        url = auth.get_url(twitter.ACCESS_TOKEN_URL)
        dbs.Vigo.set('oauth_twitter', qs)
        session['message'] = 'Twitter Auth Success'
        return self.redirect('/god/twitter?from=auth')

class Status(webapp.RequestHandler):
    @be_god
    def post(self):
        content = self.request.get('text', '')
        if len(content) > 140:
            content = content[:133] + '...'
        try: content = content.encode('utf-8')
        except UnicodeDecodeError: pass
        qs = dbs.Vigo.get('oauth_twitter')
        api = Twitter().set_qs_api(qs)
        try:
            api.PostUpdate(content)
            data = {'text':'Post To Twitter Success'}
        except:
            data = {'text':'Post To Twitter Failed'}
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(data))

apps = webapp.WSGIApplication(
    [
        ('/god/twitter', Dashboard),
        ('/god/twitter/login', Login),
        ('/god/twitter/auth', Auth),
        ('/god/twitter/status', Status),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
