#-*- coding: utf-8 -*-

import os
import re
import logging
import datetime
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.ext import webapp
from google.appengine.api import memcache, urlfetch
from django.utils import simplejson

from libs import twitter
from utils import be_god
from utils.handler import WebHandler
from utils.render import render
from god import get_tpl
import config
import dbs

week = 604800

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
            logging.warn('Twitter: ' + str(e))
        return res.content
    def set_qs_api(self, qs, input_encoding=None):
        self.token = twitter.oauth.Token.from_string(qs)
        api = twitter.Api(
            self.consumer.key, self.consumer.secret,
            self.token.key, self.token.secret, input_encoding
        )
        return api


class Dashboard(WebHandler):
    @be_god
    def get(self):
        path = get_tpl('twitter_user.html')
        rdic = {}
        source = self.request.get('from', None)
        message = ''
        if source:
            message = self.session.get('message','')
            self.session.delete('message')
        rdic['message'] = message
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.redirect('/god/twitter/login')
        api = Twitter().set_qs_api(qs)
        statuses = memcache.get('twitter$home')
        if statuses is None:
            try:
                statuses = api.GetFriendsTimeline(count=30, retweets=True)
            except twitter.TwitterError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            except urlfetch.DownloadError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            for status in statuses:
                status.datetime = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            memcache.set('twitter$home', statuses, 240)
        rdic['statuses'] = statuses
        username = dbs.Vigo.get('twitter')
        profile = memcache.get('twitter$profile$' + username)
        if profile is None:
            profile = api.GetUser(username)
            memcache.set('twitter$profile$'+username, profile, 86400)
        rdic['profile'] = profile
        rdic['username'] = username
        return self.response.out.write(render(path, rdic))

class UserStatus(WebHandler):
    @be_god
    def get(self, username):
        path = get_tpl('twitter_user.html')
        rdic = {}
        rdic['username'] = username
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.redirect('/god/twitter/login')
        api = Twitter().set_qs_api(qs)
        statuses = memcache.get('twitter$status$' + username)
        if statuses is None:
            try:
                statuses = api.GetUserTimeline(count=30, screen_name=username)
            except twitter.TwitterError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            except urlfetch.DownloadError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            for status in statuses:
                status.datetime = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            memcache.set('twitter$status$' + username, statuses, 240)
        rdic['statuses'] = statuses
        profile = memcache.get('twitter$profile$' + username)
        if profile is None:
            profile = api.GetUser(username)
            memcache.set('twitter$profile$'+username, profile, 86400)
        rdic['profile'] = profile
        return self.response.out.write(render(path, rdic))

class Mentions(WebHandler):
    @be_god
    def get(self):
        path = get_tpl('twitter_user.html')
        rdic = {}
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.redirect('/god/twitter/login')
        api = Twitter().set_qs_api(qs)
        statuses = memcache.get('twitter$mentions')
        if statuses is None:
            try:
                statuses = api.GetReplies()
            except twitter.TwitterError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            except urlfetch.DownloadError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            for status in statuses:
                status.datetime = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            memcache.set('twitter$mentions', statuses, 240)
        rdic['statuses'] = statuses
        username = dbs.Vigo.get('twitter')
        profile = memcache.get('twitter$profile$' + username)
        if profile is None:
            profile = api.GetUser(username)
            memcache.set('twitter$profile$'+username, profile, 86400)
        rdic['profile'] = profile
        rdic['username'] = username
        return self.response.out.write(render(path, rdic))

class Directs(WebHandler):
    @be_god
    def get(self):
        path = get_tpl('twitter_directs.html')
        rdic = {}
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.redirect('/god/twitter/login')
        api = Twitter().set_qs_api(qs)
        statuses = memcache.get('twitter$directs')
        if statuses is None:
            try:
                statuses = api.GetDirectMessages()
            except twitter.TwitterError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            except urlfetch.DownloadError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            for status in statuses:
                status.datetime = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            memcache.set('twitter$directs', statuses, 240)
        rdic['statuses'] = statuses
        return self.response.out.write(render(path, rdic))

class Favorites(WebHandler):
    @be_god
    def get(self):
        path = get_tpl('twitter_user.html')
        rdic = {}
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.redirect('/god/twitter/login')
        api = Twitter().set_qs_api(qs)
        username = dbs.Vigo.get('twitter')
        rdic['username'] = username
        statuses = memcache.get('twitter$favorites$' + username)
        if statuses is None:
            try:
                statuses = api.GetFavorites()
            except twitter.TwitterError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            except urlfetch.DownloadError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            for status in statuses:
                status.datetime = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            memcache.set('twitter$favorites$' + username, statuses, 240)
        rdic['statuses'] = statuses
        profile = memcache.get('twitter$profile$' + username)
        if profile is None:
            profile = api.GetUser(username)
            memcache.set('twitter$profile$'+username, profile, 86400)
        rdic['profile'] = profile
        return self.response.out.write(render(path, rdic))

class UserFavorites(WebHandler):
    @be_god
    def get(self, username):
        path = get_tpl('twitter_user.html')
        rdic = {}
        rdic['username'] = username
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.redirect('/god/twitter/login')
        api = Twitter().set_qs_api(qs)
        statuses = memcache.get('twitter$favorites$' + username)
        if statuses is None:
            try:
                statuses = api.GetFavorites(user=username)
            except twitter.TwitterError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            except urlfetch.DownloadError, e:
                logging.warn(str(e))
                return self.redirect('/god/twitter')
            for status in statuses:
                status.datetime = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            memcache.set('twitter$favorites$' + username, statuses, 240)
        rdic['statuses'] = statuses
        profile = memcache.get('twitter$profile$' + username)
        if profile is None:
            profile = api.GetUser(username)
            memcache.set('twitter$profile$'+username, profile, 86400)
        rdic['profile'] = profile
        return self.response.out.write(render(path, rdic))

class Public(WebHandler):
    @be_god
    def get(self):
        path = get_tpl('twitter_user.html')
        rdic = {}
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.redirect('/god/twitter/login')
        api = Twitter().set_qs_api(qs)
        statuses = memcache.get('twitter$public')
        if statuses is None:
            statuses = api.GetPublicTimeline()
            for status in statuses:
                status.datetime = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            memcache.set('twitter$public', statuses, 120)
        rdic['statuses'] = statuses
        username = dbs.Vigo.get('twitter')
        profile = memcache.get('twitter$profile$' + username)
        if profile is None:
            profile = api.GetUser(username)
            memcache.set('twitter$profile$'+username, profile, 86400)
        rdic['profile'] = profile
        rdic['username'] = username
        return self.response.out.write(render(path, rdic))

class Login(WebHandler):
    @be_god
    def get(self):
        auth = Twitter()
        url = auth.get_url(twitter.REQUEST_TOKEN_URL)
        qs = auth.fetch(url)
        self.session['twitter_qs'] = qs
        auth.set_qs_token(qs)
        to = auth.get_url(twitter.AUTHORIZATION_URL)
        return self.redirect(to)

class Auth(WebHandler):
    @be_god
    def get(self):
        qs = dbs.Vigo.get('oauth_twitter')
        if qs:
            return self.response.out.write('authed')
        qs = self.session.get('twitter_qs','')
        if not qs:
            self.session['message'] = 'Request Twitter access token failed'
            return self.redirect('/god?from=twitter')
        auth = Twitter()
        auth.set_qs_token(qs)
        url = auth.get_url(twitter.ACCESS_TOKEN_URL)
        qs = auth.fetch(url)
        dbs.Vigo.set('oauth_twitter', qs)
        self.session['message'] = 'Twitter Auth Success'
        return self.redirect('/god/twitter?from=auth')

class PostStatus(WebHandler):
    @be_god
    def post(self):
        qs = dbs.Vigo.get('oauth_twitter')
        self.response.headers['Content-Type'] = 'application/json'
        if not qs:
            return self.response.out.write('{"text":"Twitter Not Authed"}')
        content = self.request.get('text', '')
        if len(content) > 140:
            content = content[:133] + '...'
        api = Twitter().set_qs_api(qs, 'utf-8')
        try:
            api.PostUpdate(content)
            data = {'text':'Post To Twitter Success'}
        except twitter.TwitterError, e:
            data = {'text':str(e)}
        except urlfetch.DownloadError, e:
            data = {'text':str(e)}
        memcache.delete('twitter$home')
        self.response.out.write(simplejson.dumps(data))

class AddFav(WebHandler):
    @be_god
    def get(self, status_id):
        self.response.headers['Content-Type'] = 'application/json'
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.response.out.write('{"text":"Twitter Not Authed"}')
        api = Twitter().set_qs_api(qs)
        status = twitter.Status(id=status_id)
        try:
            api.CreateFavorite(status)
        except twitter.TwitterError, e:
            data = {'text':str(e)}
            return self.response.out.write(simplejson.dumps(data))
        except urlfetch.DownloadError, e:
            data = {'text':str(e)}
            return self.response.out.write(simplejson.dumps(data))
        return self.response.out.write('{"text":"Twitter Add Favorite Success"}')

class DelFav(WebHandler):
    @be_god
    def get(self, status_id):
        self.response.headers['Content-Type'] = 'application/json'
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return self.response.out.write('{"text":"Twitter Not Authed"}')
        api = Twitter().set_qs_api(qs)
        status = twitter.Status(id=status_id)
        try:
            api.DestroyFavorite(status)
        except twitter.TwitterError, e:
            data = {'text':str(e)}
            return self.response.out.write(simplejson.dumps(data))
        except urlfetch.DownloadError, e:
            data = {'text':str(e)}
            return self.response.out.write(simplejson.dumps(data))
        return self.response.out.write('{"text":"Twitter Delete Favorite Success"}')


apps = webapp.WSGIApplication(
    [
        ('/god/twitter', Dashboard),
        ('/god/twitter/login', Login),
        ('/god/twitter/auth', Auth),
        ('/god/twitter/mentions', Mentions),
        ('/god/twitter/directs', Directs),
        ('/god/twitter/public', Public),
        ('/god/twitter/status', PostStatus),
        ('/god/twitter/user/(.*)', UserStatus),
        ('/god/twitter/favorites', Favorites),
        ('/god/twitter/favorites/(.*)', UserFavorites),
        ('/god/twitter/addfav/(\d{10,20})', AddFav),
        ('/god/twitter/delfav/(\d{10,20})', DelFav),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
