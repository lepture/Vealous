#-*- coding: utf-8 -*-

import os
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from django.utils import simplejson

from libs import pydouban
from decorators import be_god
from utils.render import render
from utils.sessions import Session
import config
import dbs

day = 86400

register = template.create_template_register()
template.register_template_library('god.douban')

@register.filter
def avatar(links, arg='icon'):
    avatar = {}
    avatar['icon'] = None
    for link in links:
        if 'icon' == link.rel:
            avatar['icon'] = link.href
        elif 'alternate' == link.rel:
            avatar['alternate'] = link.href
    if not avatar['icon']:
        avatar['icon'] = 'http://img3.douban.com/icon/user_normal.jpg'
    return avatar[arg]
@register.filter
def pk(link):
    return link.split('/')[-1]

def get_path(ua, name):
    path = os.path.join(config.ROOT, 'god', 'tpl', name)
    return path

class Dashboard(webapp.RequestHandler):
    @be_god
    def get(self):
        ua = self.request.headers.get('User-Agent', 'bot')
        path = get_path(ua, 'douban_dashboard.html')
        rdic = {}
        source = self.request.get('from', None)
        message = ''
        if source:
            session = Session(self)
            message = session.get('message','')
            session.delete('message')
        rdic['message'] = message
        qs = dbs.Vigo.get('oauth_douban')
        if not qs:
            return self.redirect('/god/douban/login')
        api = pydouban.Api()
        api.set_qs_oauth(config.douban_key, config.douban_secret, qs)
        profile = memcache.get('douban/profile')
        if profile is None:
            profile = api.get_profile()
            memcache.set('douban/profile', profile, day)
        rdic['profile'] = profile
        miniblogs = memcache.get('douban/miniblogs')
        if miniblogs is None:
            miniblogs = api.get_contacts_miniblog()
            memcache.set('douban/miniblogs', miniblogs, 240)
        rdic['miniblogs'] = miniblogs
        return self.response.out.write(render(path, rdic))

class Login(webapp.RequestHandler):
    @be_god
    def get(self):
        auth = pydouban.Auth(config.douban_key, config.douban_secret)
        callback = config.SITE_URL + '/god/douban/auth'
        dic = auth.login(callback)
        session = Session(self)
        session['douban_dic'] = dic
        return self.redirect(dic['url'])

class Auth(webapp.RequestHandler):
    @be_god
    def get(self):
        session = Session(self)
        oauth_douban = dbs.Vigo.get('oauth_douban')
        if oauth_douban:
            session['message'] = 'Douban Authed Already'
            return self.redirect('/god/douban?from=douban')
        auth = pydouban.Auth(config.douban_key, config.douban_secret)
        dic = session.get('douban_dic',{})
        if not dic:
            session['message'] = 'Request Douban access token failed'
            return self.redirect('/god?from=douban')
        qs = auth.get_acs_token(dic['oauth_token'],dic['oauth_token_secret'])
        dbs.Vigo.set('oauth_douban', qs)
        session['message'] = 'Douban Auth Success'
        return self.redirect('/god/douban?from=douban')

class Miniblog(webapp.RequestHandler):
    @be_god
    def post(self):
        content = self.request.get('text', None)
        if not content:
            raise
        qs = dbs.Vigo.get('oauth_douban')
        api = pydouban.Api()
        api.set_qs_oauth(config.douban_key, config.douban_secret, qs)
        try:
            api.post_miniblog(content)
            data = {'text':'Post To Douban Success'}
        except:
            data = {'text':'Post To Douban Failed'}
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(data))

apps = webapp.WSGIApplication(
    [
        ('/god/douban', Dashboard),
        ('/god/douban/login', Login),
        ('/god/douban/auth', Auth),
        ('/god/douban/miniblog', Miniblog),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
