#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import memcache
from django.utils.simplejson import dumps
#import urllib2

from service import doubanapi, twitterapi
from service.disqus import Disqus
from utils.sessions import Session
from decorators import be_god
import dbs
from config import SITE_URL, DEBUG
from config import douban_key, douban_secret, twitter_key, twitter_secret


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
        consumer = doubanapi.set_consumer(douban_key, douban_secret)
        qs = doubanapi.request_token(consumer)
        token = doubanapi.set_qs_token(qs)

        session = Session(self)
        session['douban_qs'] = qs

        callback = SITE_URL + '/god/third/douban/auth'
        to = doubanapi.authorize(consumer, token, callback)
        return self.redirect(to)

class douban_access_token(webapp.RequestHandler):
    @be_god
    def get(self):
        oauth_douban = dbs.Vigo.get('oauth_douban')
        if oauth_douban:
            return self.response.out.write('authed')
        session = Session(self)
        qs = session.get('douban_qs','')
        if not qs:
            session['message'] = 'Request Douban access token failed'
            return self.redirect('/god?from=douban')
        consumer = doubanapi.set_consumer(douban_key, douban_secret)
        token = doubanapi.set_qs_token(qs)
        oauth_douban = doubanapi.access_token(consumer, token)

        dbs.Vigo.set('oauth_douban', oauth_douban)
        session['message'] = 'Douban Auth Success'
        return self.redirect('/god?from=douban')

class douban_miniblog_saying(webapp.RequestHandler):
    @be_god
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        content = self.request.get('text', None)
        if not content:
            data = {'succeeded': False}
            return self.response.out.write(dumps(data))
        consumer = doubanapi.set_consumer(douban_key, douban_secret)
        qs = dbs.Vigo.get('oauth_douban')
        if not qs:
            data = {'succeeded': False}
            return self.response.out.write(dumps(data))
        token = doubanapi.set_qs_token(qs)
        try:
            doubanapi.miniblog_saying(consumer, token, content)
            data = {'succeeded': True}
        except:
            data = {'succeeded': False}
        return self.response.out.write(dumps(data))

class twitter_request_auth(webapp.RequestHandler):
    @be_god
    def get(self):
        consumer = twitterapi.set_consumer(twitter_key, twitter_secret)
        qs = twitterapi.request_token(consumer)
        token = twitterapi.set_qs_token(qs)

        session = Session(self)
        session['twitter_qs'] = qs

        callback = SITE_URL + '/god/third/twitter/auth'
        to = twitterapi.authorize(consumer, token, callback)
        return self.redirect(to)

class twitter_access_token(webapp.RequestHandler):
    @be_god
    def get(self):
        oauth_twitter = dbs.Vigo.get('oauth_twitter')
        if oauth_twitter:
            return self.response.out.write('authed')
        session = Session(self)
        qs = session.get('twitter_qs','')
        if not qs:
            session['message'] = 'Request Twitter access token failed'
            return self.redirect('/god?from=twitter')
        consumer = twitterapi.set_consumer(twitter_key, twitter_secret)
        token = twitterapi.set_qs_token(qs)
        oauth_twitter = twitterapi.access_token(consumer, token)

        dbs.Vigo.set('oauth_twitter', oauth_twitter)
        session['message'] = 'Twitter Auth Success'
        return self.redirect('/god?from=twitter')

class twitter_update_status(webapp.RequestHandler):
    @be_god
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        content = self.request.get('text', None)
        if not content:
            data = {'succeeded': False}
            return self.response.out.write(dumps(data))
        consumer = twitterapi.set_consumer(twitter_key, twitter_secret)
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            data = {'succeeded': False}
            return self.response.out.write(dumps(data))
        token = twitterapi.set_qs_token(qs)
        data = twitterapi.update_status(consumer, token, content)
        try:
            twitterapi.update_status(consumer, token, content)
            data = {'succeeded': True}
        except:
            data = {'succeeded': False}
        return self.response.out.write(dumps(data))



apps = webapp.WSGIApplication(
    [
        ('/god/third/disqus_moderate', disqus_moderate),
        ('/god/third/douban/request', douban_request_auth),
        ('/god/third/douban/auth', douban_access_token),
        ('/god/third/douban/miniblog_saying', douban_miniblog_saying),
        ('/god/third/twitter/request', twitter_request_auth),
        ('/god/third/twitter/auth', twitter_access_token),
        ('/god/third/twitter/update_status', twitter_update_status),
    ],
    debug = DEBUG,
)

if '__main__' == __name__:
    run(apps)
