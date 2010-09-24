#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import memcache
from django.utils.simplejson import dumps
#import urllib2

from service import doubanapi
from service.disqus import Disqus
from utils.sessions import Session
from decorators import be_god
import dbs
from config import SITE_URL, DEBUG
from config import douban_key, douban_secret
import logging


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
        douban = doubanapi.Douban(douban_key, douban_secret)
        douban.set_oauth()
        dic = douban.prepare_oauth_login()
        logging.info(dic)

        session = Session(self)
        session['douban_dic'] = dic

        #callback = SITE_URL + '/god/third/douban/auth'
        callback = 'http://localhost:8080/god/third/douban/auth'
        to = dic['url'] + '&oauth_callback=' + callback
        return self.redirect(to)

class douban_access_token(webapp.RequestHandler):
    @be_god
    def get(self):
        oauth_douban = dbs.Vigo.get('oauth_douban')
        if oauth_douban:
            return self.response.out.write('authed')
        session = Session(self)
        dic = session.get('douban_dic',{})
        if not dic:
            session['message'] = 'Request Douban access token failed'
            return self.redirect('/god?from=douban')
        douban = doubanapi.Douban(douban_key, douban_secret)
        douban.set_oauth()
        qs = douban.exchange_oauth_tokens(dic['oauth_token'], dic['oauth_token_secret'])

        dbs.Vigo.set('oauth_douban', qs)
        session['message'] = 'Douban Auth Success'
        return self.redirect('/god?from=douban')

class douban_update(webapp.RequestHandler):
    @be_god
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        content = self.request.get('text', None)
        if not content:
            data = {'succeeded': False, 'text':'You Said Nothing'}
            return self.response.out.write(dumps(data))
        douban = doubanapi.Douban(douban_key, douban_secret)
        qs = dbs.Vigo.get('oauth_douban')
        if not qs:
            data = {'succeeded': False, 'text':'Not Connect to Douban Yet, <a href="/god/third/douban/request">Click Here</a>'}
            return self.response.out.write(dumps(data))
        douban.set_oauth_qs(qs)
        try:
            douban.update(content)
            data = {'succeeded': True, 'text':'Post to Douban Success'}
        except:
            data = {'succeeded': False, 'text':'Post to Douban Error'}
        return self.response.out.write(dumps(data))


apps = webapp.WSGIApplication(
    [
        ('/god/third/disqus_moderate', disqus_moderate),
        ('/god/third/douban/request', douban_request_auth),
        ('/god/third/douban/auth', douban_access_token),
        ('/god/third/douban/update.json', douban_update),
    ],
    debug = DEBUG,
)

if '__main__' == __name__:
    run(apps)
