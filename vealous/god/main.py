#-*- coding: utf-8 -*-

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
from google.appengine.api import memcache
from google.appengine.api import urlfetch, users
from google.appengine.api.labs import taskqueue
from django.utils.simplejson import loads

from utils import be_god
from utils.render import render
from utils.handler import WebHandler
from god.disqus import Disqus
from god import get_path, get_tpl
from libs import twitter
import dbs
import config

count = 10
day = 86400

class Login(WebHandler):
    def get(self):
        auth = self.session.get('auth',0)
        gauth = users.is_current_user_admin()
        if 1 == auth or gauth:
            self.redirect('/god')
        rdic = {}
        path = get_path(self.request, 'login.html')
        rdic['gurl'] = users.create_login_url(self.request.url)
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
        if users.is_current_user_admin():
            url = users.create_logout_url(self.request.url)
            return self.redirect(url)
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
        if comments is not None:
            rdic['comments'] = comments
            return self.response.out.write(render(path,rdic))
        disqus_key = config.disqus_userkey
        disqus_forumid = config.disqus_forumid
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
            logging.info(message)
            self.session.delete('message')
        rdic = {}
        action = self.request.get('action', 'none').lower()
        key = self.request.get('key', 'none')
        status = self.request.get('draft', '2')
        p = self.request.get('p',1)
        to = '/god/article?from=%s;p=%s' % (action, p)
        if 'draft' == action or 'post' == action:
            data = dbs.get_by_key(key)
            if data and 'draft' == action:
                data.sw_status(True)
            elif data and 'post' == action:
                data.sw_status(False)
            else:
                self.session['message'] = "Can't find the article"
            return self.redirect(to)
        if 'filter' == action:
            keys = self.get_filter(status)
        elif 'find' == action:
            data = self.get_find(key)
            if data:
                return self.redirect('/god/article/edit?key=%s;p=%s' % (data.key(), p))
            message = "Not find the article"
            keys = dbs.Article.all_keys()
        else:
            keys = dbs.Article.all_keys()
        rdic['message'] = message
        p = self.request.get('p',1)
        rdic['mvdata'] = dbs.Article.get_page(keys, p)
        rdic['p'] = p
        path = get_tpl('article.html')
        return self.response.out.write(render(path,rdic))

    def get_filter(self, status):
        if '0' == status:
            keys = dbs.Article.show_keys()
        elif '1' == status:
            allkeys = dbs.Article.all_keys()
            showkeys = dbs.Article.show_keys()
            keys = list(set(allkeys) - set(showkeys))
        else:
            keys = dbs.Article.all_keys()
        return keys 

    def get_find(self, key):
        q = dbs.Article.gql('WHERE slug =:1', key)
        data = q.fetch(1)
        if data:
            return data[0]
        return None

class EditArticle(WebHandler):
    @be_god
    def get(self):
        key = self.request.get('key', None)
        if not key:
            return self.redirect('/god/article')
        data = dbs.get_by_key(key)
        if not data:
            return self.redirect('/god/article')
        action = self.request.get('action', None)
        if 'delete' == action:
            data.delete()
            self.session['message'] = 'Article <strong>%s</strong> has been deleted' % data.title
            return self.redirect('/god/article?from=delete')
        rdic = {}
        rdic['data'] = data
        path = get_tpl('edit_article.html')
        return self.response.out.write(render(path,rdic))
    
    @be_god
    def post(self):
        rdic = {}
        key = self.request.get('key', None)
        p = self.request.get('p', 1)
        to = '/god/article?p=%s' % p
        if not key:
            return self.redirect(to)
        data = dbs.get_by_key(key)
        if not data:
            return self.redirect(to)
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
            data.update(title, slug, text, draft, keyword)
            self.session['message'] = 'Article <a href="/god/article/edit?key=%s">%s</a> has been modified' % (data.key(), data.title)
            if not draft:
                taskqueue.add(url='/god/task/ping', method="GET")
            return self.redirect(to + ';from=edit')
        rdic['data'] = data
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_tpl('edit_article.html')
        return self.response.out.write(render(path,rdic))

class AddArticle(WebHandler):
    @be_god
    def get(self):
        rdic = {}
        path = get_tpl('add_article.html')
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
            if not draft:
                self.tweet(data)
                taskqueue.add(url='/god/task/ping', method='GET')
            return self.redirect('/god/article?from=add')
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_tpl('add_article.html')
        return self.response.out.write(render(path,rdic))

    def tweet(self, data):
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return 'Twitter Not Authed'
        url = urllib.quote(config.SITE_URL + data.the_url)
        bitly = 'http://api.bit.ly/v3/shorten?login=%s&apiKey=%s&longUrl=%s&format=json' % (config.bitly_login, config.bitly_apikey, url)
        try:
            result = urlfetch.fetch(bitly)
            if 200 == result.status_code:
                url = loads(result.content)['data']['url']
            else:
                url = config.SITE_URL + data.the_url
        except:
            url = config.SITE_URL + data.the_url

        content = data.title + ' : ' + data.text[:100]
        if len(content) > 110:
            content = content[:100] + '... via ' + url
        else:
            content = content + '... via ' + url
        token = twitter.oauth.Token.from_string(qs)
        api = twitter.Api(
            config.twitter_key, config.twitter_secret,
            token.key, token.secret, 'utf-8')
        try:
            api.PostUpdate(content)
        except twitter.TwitterError, e:
            return str(e)
        return 'Post to Twitter Success'

class ViewPage(WebHandler):
    @be_god
    def get(self):
        action = self.request.get('action', 'none').lower()
        key = self.request.get('key', 'none')
        if 'find' == action:
            data = self.get_find(key)
            if data:
                return self.redirect('/god/page/edit?key=%s' % data.key())
        source = self.request.get('from', None)
        message = ''
        if source:
            message = self.session.get('message','')
            self.session.delete('message')
        rdic = {}
        rdic['message'] = message
        p = self.request.get('p',1)
        keys = dbs.Page.all_keys()
        rdic['mvdata'] = dbs.Page.get_page(keys, p)
        path = get_tpl('page.html')
        return self.response.out.write(render(path,rdic))

    def get_find(self, key):
        q = dbs.Article.gql('WHERE slug =:1', key)
        data = q.fetch(1)
        if data:
            return data[0]
        return None

class AddPage(WebHandler):
    @be_god
    def get(self):
        rdic = {}
        path = get_tpl('add_page.html')
        return self.response.out.write(render(path,rdic))
    
    @be_god
    def post(self):
        rdic = {}
        title = self.request.get('title', None)
        slug = self.request.get('slug', None)
        text = self.request.get('text', None)
        if title and slug:
            data = dbs.Page.add(title,slug,text)
            self.session['message'] = 'New page <a href="/god/page/edit?key=%s">%s</a> has been created' % (data.key(), data.title)
            return self.redirect('/god/page?from=add')
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_tpl('add_page.html')
        return self.response.out.write(render(path,rdic))

class EditPage(WebHandler):
    @be_god
    def get(self):
        key = self.request.get('key', None)
        if not key:
            return self.redirect('/god/page')
        data = dbs.get_by_key(key)
        if not data:
            return self.redirect('/god/page')
        action = self.request.get('action', None)
        if 'delete' == action:
            data.delete()
            self.session['message'] = 'Page <strong>%s</strong> has been deleted' % data.title
            return self.redirect('/god/page?from=delete')
        rdic = {}
        rdic['data'] = data
        path = get_tpl('edit_page.html')
        return self.response.out.write(render(path,rdic))
    
    @be_god
    def post(self):
        rdic = {}
        key = self.request.get('key', None)
        if not key:
            return self.redirect('/god/page')
        data = dbs.get_by_key(key)
        if not data:
            return self.redirect('/god/page')
        title = self.request.get('title', None)
        slug = self.request.get('slug', None)
        text = self.request.get('text', None)
        if title and slug:
            data.update(title, slug, text)
            self.session['message'] = 'Page <a href="/god/article/edit?key=%s">%s</a> has been modified' % (data.key(), data.title)
            return self.redirect('/god/page?from=edit')
        rdic['data'] = data
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_tpl('edit_page.html')
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
        keys = self.get_filter(status)
        p = self.request.get('p',1)
        rdic['mvdata'] = dbs.Melody.get_page(keys, p)
        path = get_tpl('melody.html')
        return self.response.out.write(render(path,rdic))

    def get_filter(self, status):
        if 'demo' != status and 'link' != status and 'nav' != status:
            return dbs.Melody.label_keys()
        return dbs.Melody.label_keys(status)

class AddMelody(WebHandler):
    @be_god
    def get(self):
        rdic = {}
        path = get_tpl('add_melody.html')
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
        if title and label:
            try: prior = int(prior)
            except: prior = 0
            data = dbs.Melody.add(title,url,label,prior,ext,text)
            self.session['message'] = 'New %s <a href="/god/melody/edit?key=%s">%s</a> has been created' % (data.label, data.key(), data.title)
            return self.redirect('/god/melody?from=add')
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_tpl('add_melody.html')
        return self.response.out.write(render(path,rdic))

class EditMelody(WebHandler):
    @be_god
    def get(self):
        key = self.request.get('key', None)
        if not key:
            return self.redirect('/god/melody')
        data = dbs.get_by_key(key)
        if not data:
            return self.redirect('/god/melody')
        action = self.request.get('action', None)
        if 'delete' == action:
            data.delete()
            self.session['message'] = '%s <strong>%s</strong> has been deleted' % (data.label.upper(), data.title)
            return self.redirect('/god/melody?from=delete')
        rdic = {}
        rdic['data'] = data
        path = get_tpl('edit_melody.html')
        return self.response.out.write(render(path,rdic))
    
    @be_god
    def post(self):
        rdic = {}
        key = self.request.get('key', None)
        if not key:
            return self.redirect('/god/melody')
        data = dbs.get_by_key(key)
        if not data:
            return self.redirect('/god/melody')
        label = self.request.get('label', None)
        title = self.request.get('title', None)
        url = self.request.get('url', None)
        prior = self.request.get('prior',0)
        text = self.request.get('text', None)
        ext = self.request.get('ext', None)
        if title and label:
            try: prior = int(prior)
            except: prior = 0
            data.update(title,url,label,prior,ext,text)
            self.session['message'] = '%s <a href="/god/melody/edit?key=%s">%s</a> has been modified' % (data.label.upper(), data.key(), data.title)
            return self.redirect('/god/melody?from=edit')
        rdic['data'] = data
        message = 'Please fill the required fields'
        rdic['message'] = message
        path = get_tpl('edit_melody.html')
        return self.response.out.write(render(path,rdic))

class VigoSetting(WebHandler):
    @be_god
    def get(self):
        rdic = {}
        path = get_path(self.request, 'vigo.html')
        return self.response.out.write(render(path,rdic))

    @be_god
    def post(self):
        rdic = {}
        sitename = self.request.get('sitename', 'Vealous')
        sitetag = self.request.get('sitetag', 'Pure Vealous')
        twitter = self.request.get('twitter', 'lepture')
        alterfeed = self.request.get('alterfeed','')
        meta = self.request.get('meta','')
        widget = self.request.get('widget','')

        dbs.Vigo.set('sitename', sitename)
        dbs.Vigo.set('sitetag', sitetag)
        dbs.Vigo.set('twitter', twitter)
        dbs.Vigo.set('alterfeed', alterfeed)
        dbs.Vigo.set('meta', meta)
        dbs.Vigo.set('widget', widget)
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
        if not origpasswd:
            rdic['message'] = 'Heavens! There is no God password ..'
            return self.response.out.write(render(path,rdic))
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
        path = get_tpl('memcache.html')
        return self.response.out.write(render(path,rdic))

class TaskPing(WebHandler):
    def get(self):
        gping = 'http://blogsearch.google.com/ping?name='
        gping += urllib.quote(dbs.Vigo.get('sitename'))
        gping += '&url=%s' % urllib.quote(config.SITE_URL)
        gping += '&changesURL=%s/sitemap.xml' % urllib.quote(config.SITE_URL)
        try:
            result = urlfetch.fetch(gping)
            if 200 == result.status_code:
                return self.response.out.write('Google Blog Ping: ' + gping)
            return self.response.out.write('Google Blog Ping Error: ' + str(result.status_code))
        except:
            return self.response.out.write('Google Blog Ping Failed')

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
        ('/god/page', ViewPage),
        ('/god/page/add', AddPage),
        ('/god/page/edit', EditPage),
        ('/god/melody', ViewMelody),
        ('/god/melody/add', AddMelody),
        ('/god/melody/edit', EditMelody),
        ('/god/console/memcache', ConsoleMemcache),
        ('/god/task/ping', TaskPing),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
