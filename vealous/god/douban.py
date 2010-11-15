#-*- coding: utf-8 -*-

import os
import datetime
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from django.utils import simplejson

from libs import pydouban
from utils import be_god
from utils.handler import WebHandler
from utils.render import render
from god import get_path
import config
import dbs

day = 86400

register = template.create_template_register()
template.register_template_library('god.douban')

@register.filter
def selectlink(links, arg='icon'):
    if not isinstance(links, list):
        return ''
    for link in links:
        if arg == link.rel:
            return link.href
    return ''
@register.filter
def pk(link):
    return link.split('/')[-1]


class Dashboard(WebHandler):
    @be_god
    def get(self):
        path = get_path(self.request, 'douban_dashboard.html')
        rdic = {}
        source = self.request.get('from', None)
        message = ''
        if source:
            message = self.session.get('message','')
            self.session.delete('message')
        rdic['message'] = message
        qs = dbs.Vigo.get('oauth_douban')
        if not qs:
            return self.redirect('/god/douban/login')
        api = pydouban.Api(max_results=30)
        api.set_qs_oauth(config.douban_key, config.douban_secret, qs)
        profile = memcache.get('douban/profile')
        if profile is None:
            profile = api.get_profile()
            memcache.set('douban/profile', profile, day)
        rdic['profile'] = profile
        miniblogs = memcache.get('douban/miniblogs')
        if miniblogs is None:
            miniblogs = api.get_contacts_miniblog()
            for i in range(len(miniblogs.entry)):
                miniblogs.entry[i].published.t = datetime.datetime.strptime(
                    miniblogs.entry[i].published.t, '%Y-%m-%dT%H:%M:%S+08:00')
                miniblogs.entry[i].published.t -= datetime.timedelta(hours=8)
            memcache.set('douban/miniblogs', miniblogs, 240)
        rdic['miniblogs'] = miniblogs
        return self.response.out.write(render(path, rdic))

class Login(WebHandler):
    @be_god
    def get(self):
        auth = pydouban.Auth(config.douban_key, config.douban_secret)
        callback = config.SITE_URL + '/god/douban/auth'
        dic = auth.login(callback)
        self.session['douban_dic'] = dic
        return self.redirect(dic['url'])

class Auth(WebHandler):
    @be_god
    def get(self):
        oauth_douban = dbs.Vigo.get('oauth_douban')
        if oauth_douban:
            self.session['message'] = 'Douban Authed Already'
            return self.redirect('/god/douban?from=douban')
        auth = pydouban.Auth(config.douban_key, config.douban_secret)
        dic = self.session.get('douban_dic',{})
        if not dic:
            self.session['message'] = 'Request Douban access token failed'
            return self.redirect('/god?from=douban')
        qs = auth.get_acs_token(dic['oauth_token'],dic['oauth_token_secret'])
        dbs.Vigo.set('oauth_douban', qs)
        self.session['message'] = 'Douban Auth Success'
        return self.redirect('/god/douban?from=douban')

class Miniblog(WebHandler):
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

if 'zh' == config.LANGUAGE:
    apps = webapp.WSGIApplication(
        [
            ('/god/douban', Dashboard),
            ('/god/douban/login', Login),
            ('/god/douban/auth', Auth),
            ('/god/douban/miniblog', Miniblog),
        ],
        debug = config.DEBUG,
    )
else:
    apps = webapp.WSGIApplication([], debug = config.DEBUG)

if '__main__' == __name__:
    run(apps)
