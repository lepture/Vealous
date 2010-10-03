#-*- coding: utf-8 -*-

import os
import logging
import urllib
try:
    import hashlib
    sha1 = hashlib.sha1
except ImportError:
    import sha
    sha1 = sha.new

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from django.utils.simplejson import dumps

from utils import is_mobile, be_god
from utils.render import render
from utils import Paginator
from utils.handler import WebHandler
from god.disqus import Disqus
import dbs
import config

count = 10
day = 86400

def get_path(request , name):
    if is_mobile(request):
        path = os.path.join(config.ROOT, 'god','mobile' , name)
        return path
    path = os.path.join(config.ROOT, 'god', 'tpl', name)
    return path

class Login(WebHandler):
    def get(self):
        auth = self.session.get('auth',0)
        if 1 == auth:
            self.redirect('/god')
        rdic = {}
        path = get_path(self.request, 'login.html')
        return self.response.out.write(render(path,rdic))
    def post(self):
        password = dbs.Vigo.get('password')
        if not password:
            password = sha1(config.PASSWORD + config.SECRET).hexdigest()
            dbs.Vigo.set('password', password)
        passwd = self.request.get('passwd') # input password
        passwd = sha1(passwd + config.SECRET).hexdigest()
        to = self.request.get('to')
        if passwd == password:
            self.session['auth'] = 1
            return self.redirect(urllib.unquote(to))
        rdic = {}
        message = 'Are you really a God?'
        rdic['message'] = message
        path = get_path(self.request, 'login.html')
        return self.response.out.write(render(path,rdic))

class Logout(WebHandler):
    def get(self):
        self.session['auth'] = 0
        return self.redirect('/god/login')

class Dashboard(WebHandler):
    @be_god
    def get(self):
        rdic = {}
        source = self.request.get('from', None)
        message = ''
        if source:
            message = self.session.get('message','')
            self.session.delete('message')
        rdic['message'] = message
        comments = memcache.get('disqus$comments')
        path = get_path(self.request, 'dashboard.html')
        rdic['notes'] = dbs.Note.getten()
        if comments is not None:
            rdic['comments'] = comments
            return self.response.out.write(render(path,rdic))
        disqus_key = dbs.Vigo.get('disqus_key')
        disqus_forumid = dbs.Vigo.get('disqus_forumid')
        mydisqus = Disqus(disqus_key)
        mydisqus.get_forum_posts_rpc(disqus_forumid)
        result = mydisqus.get_forum_posts_result()
        comments = mydisqus.parse_data(result)
        memcache.set('disqus$comments', comments, 10800) # 3 hours
        rdic['comments'] = comments
        return self.response.out.write(render(path,rdic))

class ViewArticle(WebHandler):
    @be_god
    def get(self):
        source = self.request.get('from', None)
        message = ''
        if source:
            message = self.session.get('message','')
            self.session.delete('message')
        rdic = {}
        action = self.request.get('action', 'none').lower()
        key = self.request.get('key', 'none')
        status = self.request.get('draft', '2')
        if 'draft' == action or 'post' == action:
            data = db.get(key)
            if data and 'draft' == action:
                data.sw_status(data)
            elif data and 'post' == action:
                data.sw_status(data, False)
            else:
                self.session['message'] = "Can't find the article"
            return self.redirect('/god/article?from='+action)
        if 'filter' == action:
            data = self.get_filter(status)
        elif 'find' == action:
            data = self.get_find(key)
        else:
            data = dbs.Article.gql('ORDER BY created DESC')
        rdic['message'] = message
        p = self.request.get('p',1)
        rdic['mvdata'] = Paginator(data, count, p)
        path = get_path(self.request, 'article.html')
        return self.response.out.write(render(path,rdic))

    def get_filter(self, status):
        if '0' == status:
            data = dbs.Article.gql('WHERE draft = :1 ORDER BY created DESC', False)
        elif '1' == status:
            data = dbs.Article.gql('WHERE draft = :1 ORDER BY created DESC', True)
        else:
            data = dbs.Article.gql('ORDER BY created DESC')
        return data

    def get_find(self, key):
        data = dbs.Article.gql('WHERE slug =:1', key)
        return data

class EditArticle(WebHandler):
    @be_god
    def get(self):
        key = self.request.get('key', None)
        if not key:
            return self.redirect('/god/article')
        data = db.get(key)
        if not data:
            return self.redirect('/god/article')
        action = self.request.get('action', None)
        if 'delete' == action:
            dbs.Article.delete(data)
            self.session['message'] = 'Article <strong>%s</strong> has been deleted' % data.title
            return self.redirect('/god/article?from=delete')
        rdic = {}
        rdic['data'] = data
        path = get_path(self.request, 'edit_article.html')
        return self.response.out.write(render(path,rdic))
    
    @be_god
    def post(self):
        rdic = {}
        key = self.request.get('key', None)
        if not key:
            return self.redirect('/god/article')
        data = db.get(key)
        if not data:
            return self.redirect('/god/article')
        title = self.request.get('title', None)
        slug = self.request.get('slug', None)
        text = self.request.get('text', None)
        draft = self.request.get('draft', None)
        keyword = self.request.get('keyword', None)
        if draft:
            draft = True
        else:
            draft = False
        if title and slug:
            dbs.Article.update(data, title, slug, text, draft, keyword)
            self.session['message'] = 'Article <a href="/god/article/edit?key=%s">%s</a> has been modified' % (data.key(), data.title)
            gping = 'http://blogsearch.google.com/ping?url=%s/feed.atom' % config.SITE_URL
            urlfetch.fetch(gping)
            return self.redirect('/god/article?from=edit')
        rdic['data'] = data
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_path(self.request, 'edit_article.html')
        return self.response.out.write(render(path,rdic))

class AddArticle(WebHandler):
    @be_god
    def get(self):
        rdic = {}
        path = get_path(self.request, 'add_article.html')
        return self.response.out.write(render(path,rdic))
    
    @be_god
    def post(self):
        rdic = {}
        title = self.request.get('title', None)
        slug = self.request.get('slug', None)
        text = self.request.get('text', None)
        keyword = self.request.get('keyword', None)
        draft = self.request.get('draft', None)
        if draft:
            draft = True
        else:
            draft = False
        if title and slug:
            data = dbs.Article.add(title,slug,text,draft,keyword)
            self.session['message'] = 'New article <a href="/god/article/edit?key=%s">%s</a> has been created' % (data.key(), data.title)
            gping = 'http://blogsearch.google.com/ping?url=%s/feed.atom' % config.SITE_URL
            urlfetch.fetch(gping)
            return self.redirect('/god/article?from=add')
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_path(self.request, 'add_article.html')
        return self.response.out.write(render(path,rdic))

class ViewMelody(WebHandler):
    @be_god
    def get(self):
        source = self.request.get('from', None)
        message = ''
        if source:
            message = self.session.get('message','')
            self.session.delete('message')
        status = self.request.get('filter', 'none')
        rdic = {}
        rdic['message'] = message
        data = self.get_filter(status)
        p = self.request.get('p',1)
        rdic['mvdata'] = Paginator(data, count, p)
        path = get_path(self.request, 'melody.html')
        return self.response.out.write(render(path,rdic))

    def get_filter(self, status):
        if 's5' != status and 'link' != status and 'nav' != status:
            data = dbs.Melody.all().order('-prior')
            return data
        data = dbs.Melody.gql('WHERE label = :1 ORDER BY prior DESC',status)
        return data

class AddMelody(WebHandler):
    @be_god
    def get(self):
        rdic = {}
        path = get_path(self.request, 'add_melody.html')
        return self.response.out.write(render(path,rdic))

    @be_god
    def post(self):
        rdic = {}
        label = self.request.get('label', None)
        title = self.request.get('title', None)
        url = self.request.get('url', None)
        prior = self.request.get('prior',0)
        text = self.request.get('text', None)
        ext = self.request.get('ext', None)
        if title and url and label:
            try: prior = int(prior)
            except: prior = 0
            data = dbs.Melody.add(title,url,label,prior,ext,text)
            self.session['message'] = 'New %s <a href="/god/melody/edit?key=%s">%s</a> has been created' % (data.label, data.key(), data.title)
            return self.redirect('/god/melody?from=add')
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_path(self.request, 'add_melody.html')
        return self.response.out.write(render(path,rdic))

class EditMelody(WebHandler):
    @be_god
    def get(self):
        key = self.request.get('key', None)
        if not key:
            return self.redirect('/god/melody')
        data = db.get(key)
        if not data:
            return self.redirect('/god/melody')
        action = self.request.get('action', None)
        if 'delete' == action:
            dbs.Melody.delete(data)
            self.session['message'] = '%s <strong>%s</strong> has been deleted' % (data.label.upper(), data.title)
            return self.redirect('/god/melody?from=delete')
        rdic = {}
        rdic['data'] = data
        path = get_path(self.request, 'edit_melody.html')
        return self.response.out.write(render(path,rdic))
    
    @be_god
    def post(self):
        rdic = {}
        key = self.request.get('key', None)
        if not key:
            return self.redirect('/god/melody')
        data = db.get(key)
        if not data:
            return self.redirect('/god/melody')
        label = self.request.get('label', None)
        title = self.request.get('title', None)
        url = self.request.get('url', None)
        prior = self.request.get('prior',0)
        text = self.request.get('text', None)
        ext = self.request.get('ext', None)
        if title and url and label:
            try: prior = int(prior)
            except: prior = 0
            dbs.Melody.update(data, title,url,label,prior,ext,text)
            self.session['message'] = '%s <a href="/god/melody/edit?key=%s">%s</a> has been modified' % (data.label.upper(), data.key(), data.title)
            return self.redirect('/god/melody?from=edit')
        rdic['data'] = data
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_path(self.request, 'edit_melody.html')
        return self.response.out.write(render(path,rdic))

class ViewNote(WebHandler):
    @be_god
    def get(self):
        self.redirect('/god')

class AddNote(WebHandler):
    @be_god
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        content = self.request.get('text', None)
        if not content:
            data = {'succeeded': False, 'text':'You Said Nothing'}
            return self.response.out.write(dumps(data))
        note = dbs.Note.add(content)
        html = '<div class="cell"><p>%s</p><p>Created at <span class="time">Just now</span></p></div>' % content
        data = {'succeeded': True, 'text':'Note Saved', 'html':html}
        return self.response.out.write(dumps(data))

class DeleteNote(WebHandler):
    @be_god
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        key = self.request.get('key', None)
        if not key:
            data = {'succeeded': False, 'text':'No key found'}
            return self.response.out.write(dumps(data))
        data = db.get(key)
        if not data:
            data = {'succeeded': False, 'text':'No such note'}
            return self.response.out.write(dumps(data))
        dbs.Note.delete(data)
        data = {'succeeded': True, 'text':'Delete Note'}
        return self.response.out.write(dumps(data))

class VigoSetting(WebHandler):
    @be_god
    def get(self):
        rdic = {}
        rdic['disqus_key'] = dbs.Vigo.get('disqus_key')
        rdic['forum_key'] = dbs.Vigo.get('forum_key')
        rdic['disqus_forumid'] = dbs.Vigo.get('disqus_forumid')
        path = get_path(self.request, 'vigo.html')
        return self.response.out.write(render(path,rdic))

    @be_god
    def post(self):
        rdic = {}
        sitename = self.request.get('sitename', 'Vealous')
        sitetag = self.request.get('sitetag', 'Pure Vealous')
        twitter = self.request.get('twitter', 'lepture')
        ga = self.request.get('ga','')
        gcse = self.request.get('gcse','')
        disqus = self.request.get('disqus','')
        disqus_key = self.request.get('disqus_key','')
        forum_key = self.request.get('forum_key','')
        disqus_forumid = self.request.get('disqus_forumid','')
        alterfeed = self.request.get('alterfeed','')

        rdic['sitename'] = dbs.Vigo.set('sitename', sitename)
        rdic['sitetag'] = dbs.Vigo.set('sitetag', sitetag)
        rdic['twitter'] = dbs.Vigo.set('twitter', twitter)
        rdic['ga'] = dbs.Vigo.set('ga', ga)
        rdic['gcse'] = dbs.Vigo.set('gcse', gcse)
        rdic['disqus'] = dbs.Vigo.set('disqus', disqus)
        rdic['disqus_key'] = dbs.Vigo.set('disqus_key', disqus_key)
        rdic['forum_key'] = dbs.Vigo.set('forum_key', forum_key)
        rdic['disqus_forumid'] = dbs.Vigo.set('disqus_forumid', disqus_forumid)
        rdic['alterfeed'] = dbs.Vigo.set('alterfeed', alterfeed)
        memcache.delete('vigo')
        rdic['message'] = 'Your setting has been saved'
        path = get_path(self.request, 'vigo.html')
        return self.response.out.write(render(path,rdic))

class Chpasswd(WebHandler):
    @be_god
    def get(self):
        rdic = {}
        path = get_path(self.request, 'chpasswd.html')
        return self.response.out.write(render(path,rdic))
    @be_god
    def post(self):
        rdic = {}
        origpasswd = dbs.Vigo.get('password')
        old = self.request.get('oldpasswd','')
        path = get_path(self.request, 'chpasswd.html')
        if origpasswd != sha1(old + config.SECRET).hexdigest():
            rdic['message'] = 'Heavens! God forgot his password ..'
            return self.response.out.write(render(path,rdic))
        passwd1 = self.request.get('passwd1', '')
        passwd2 = self.request.get('passwd2', '')
        if passwd1 and passwd2:
            if passwd1 != passwd2:
                rdic['message'] = "It's really terrible, two passwords didn't match"
                return self.response.out.write(render(path,rdic))
            newpasswd = sha1(passwd1 + config.SECRET).hexdigest()
            dbs.Vigo.set('password', newpasswd)
            rdic['message'] = "Password has been changed"
            return self.response.out.write(render(path,rdic))
        rdic['message'] = "Please fill all required fields"
        return self.response.out.write(render(path,rdic))

class ConsoleMemcache(WebHandler):
    @be_god
    def get(self):
        action = self.request.get('action','none')
        key = self.request.get('key',None)
        if 'flush' == action:
            memcache.flush_all()
            logging.info('flash all memcache')
            return self.redirect('/god/console/memcache')
        if 'delete' == action and key:
            memcache.delete(key)
            logging.info('delete memcache key: ' + str(key))
            return self.redirect('/god/console/memcache')
        elif 'display' == action and key:
            result = memcache.get(key)
        else:
            result = ''
        rdic = {}
        memstat = memcache.get_stats()
        rdic['key'] = key
        rdic['memstat'] = memstat
        rdic['result'] = result
        self.request.headers['User-Agent'] = 'bot'
        path = get_path(self.request,'memcache.html')
        return self.response.out.write(render(path,rdic))


apps = webapp.WSGIApplication(
    [
        ('/god/?', Dashboard),
        ('/god/login', Login),
        ('/god/logout', Logout),
        ('/god/chpasswd', Chpasswd),
        ('/god/setting', VigoSetting),
        ('/god/article', ViewArticle),
        ('/god/article/add', AddArticle),
        ('/god/article/edit', EditArticle),
        ('/god/melody', ViewMelody),
        ('/god/melody/add', AddMelody),
        ('/god/melody/edit', EditMelody),
        ('/god/note', ViewNote),
        ('/god/note/add', AddNote),
        ('/god/note/delete', DeleteNote),
        ('/god/console/memcache', ConsoleMemcache),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
