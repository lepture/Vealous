#-*- coding: utf-8 -*-

import os
import logging
from urllib2 import quote, unquote
from django.utils.simplejson import loads as parse_json
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import memcache
from google.appengine.api import urlfetch

from utils.render import render
from utils import Paginator
from utils import is_mobile
from markdown import markdown
import dbs

import config

def get_path(request, name):
    if is_mobile(request):
        path = os.path.join(config.ROOT, 'tpl','mobile' , name)
        return path
    path = os.path.join(config.ROOT, 'tpl', config.THEME, name)
    return path

def getslug(slug):
    try:
        return unquote(slug).decode('utf-8')
    except:
        return slug

class Index(webapp.RequestHandler):
    def head(self):
        pass

    def get(self):
        if is_mobile(self.request):
            mkey = 'html/mobile'
        else:
            mkey = 'html/index'
        html = memcache.get(mkey)
        if html is not None:
            return self.response.out.write(html)
        rdic = {}
        rdic['articles'] = dbs.Article.getten()
        rdic['navs'] = dbs.Melody.get_all('nav')
        rdic['links'] = dbs.Melody.get_all('link')
        path = get_path(self.request, 'index.html')
        html = render(path, rdic)
        memcache.set(mkey, html, 300)
        self.response.out.write(html)

class Article(webapp.RequestHandler):
    def head(self, url):
        pass

    def get(self, slug):
        slug = getslug(slug)
        rdic = {}
        data = dbs.Article.get(slug)
        if not data:
            logging.info('404 , visite article ' + slug)
            path = get_path(self.request, '404.html')
            self.response.set_status(404)
            html = render(path, rdic)
            return self.response.out.write(html)
        mode = self.request.get('mode','mark')
        if 'plaintext' == mode:
            self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
            html = data.text
            return self.response.out.write(html)
        rdic['navs'] = dbs.Melody.get_all('nav')
        rdic['data'] = data
        path = get_path(self.request, 'article.html')
        html = render(path, rdic)
        self.response.out.write(html)

class Archive(webapp.RequestHandler):
    def head(self):
        pass

    def get(self):
        rdic = {}
        rdic['navs'] = dbs.Melody.get_all('nav')
        p = self.request.get('p',1)
        data = dbs.Article.get_archive()
        rdic['mvdata'] = Paginator(data, 10, p)
        path = get_path(self.request, 'archive.html')
        self.response.out.write(render(path,rdic))

class Keyword(webapp.RequestHandler):
    def head(self, keyword):
        pass
    def get(self, keyword):
        keyword = getslug(keyword)
        rdic = {}
        data = dbs.Article.get_kw_articles(keyword)
        if not data:
            logging.info('404 , visite keyword ' + keyword)
            path = get_path(self.request, '404.html')
            html = render(path, rdic)
            self.response.set_status(404)
        else:
            p = self.request.get('p',1)
            rdic['mvdata'] = Paginator(data, 10, p)
            rdic['navs'] = dbs.Melody.get_all('nav')
            rdic['links'] = dbs.Melody.get_all('link')
            rdic['keyword'] = keyword
            path = get_path(self.request, 'keyword.html')
            html = render(path, rdic)
        self.response.out.write(html)

class Page(webapp.RequestHandler):
    def get(self, slug):
        slug = getslug(slug)
        data = None
        #data = dbs.Melody.get_page(slug)
        rdic = {}
        rdic['navs'] = dbs.Melody.get_all('nav')
        rdic['links'] = dbs.Melody.get_all('link')
        if not data:
            logging.info('404 , visite page ' + slug)
            path = get_path(self.request, '404.html')
            self.response.set_status(404)
            html = render(path, rdic)
            return self.response.out.write(html)
        data.text = markdown(data.text)
        rdic['data'] = data
        path = get_path(self.request, 'page.html')
        html = render(path, rdic)
        self.response.out.write(html)


class Search(webapp.RequestHandler):
    def get(self):
        rdic = {}
        cx = config.gcse
        rdic['q'] = q = self.request.get('q','Vealous')
        rdic['start'] = start = self.request.get('start', '0')
        try:
            rdic['gres'] = gsearch(q, start, cx)
        except:
            rdic['error'] = 'Oops! An Error occured!'
        rdic['navs'] = dbs.Melody.get_all('nav')
        path = get_path(self.request, 'search.html')
        self.response.out.write(render(path,rdic))

class Atom(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        html = memcache.get('xml$atom')
        if html is None:
            rdic = {}
            rdic['datas'] = dbs.Article.getten()
            path = os.path.join(config.ROOT, 'tpl', 'atom.xml')
            html = render(path, rdic)
            memcache.set('xml$atom', html)
        self.response.out.write(html)

class Rss(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        html = memcache.get('xml$rss')
        if html is None:
            rdic = {}
            rdic['datas'] = dbs.Article.getten()
            path = os.path.join(config.ROOT, 'tpl', 'rss.xml')
            html = render(path, rdic)
            memcache.set('xml$rss', html)
        self.response.out.write(html)

class Sitemap (webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        html = memcache.get('xml$sitemap')
        if html is None:
            rdic = {}
            urlset = []
            def addurl(loc, lastmod=None, changefreq=None, priority=None):
                url = {
                    'location': loc,
                    'lastmod': lastmod,
                    'changefreq': changefreq,
                    'priority': priority,
                }
                urlset.append(url)
            articles = dbs.Article.get_archive()
            for art in articles:
                addurl(art.the_url, art.modified,'weekly',0.5)
            rdic['urlset'] = urlset
            path = os.path.join(config.ROOT, 'tpl', 'sitemap.xml')
            html = render(path, rdic)
            memcache.set('xml$sitemap', html)
        self.response.out.write(html)

class Redirect(webapp.RequestHandler):
    def get(self, path):
        logging.info('redirect from path ' + path)
        self.redirect('/' + path)

class Error404(webapp.RequestHandler):
    def get(self):
        logging.info('404')
        rdic = {}
        path = get_path(self.request, '404.html')
        self.response.set_status(404)
        self.response.out.write(render(path,rdic))


def gsearch(q, start, cx=''):
    GSEARCH_URL = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=filtered_cse&cx=%(cx)s&q=%(q)s&start=%(start)s'
    if not cx:
        GSEARCH_URL = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=filtered_cse&q=%(q)s&start=%(start)s'
    try:
        q = quote(q.encode('utf-8'))
    except:
        q = quote(q)
    gdic = dict(cx=cx,q=q,start=start)
    url = GSEARCH_URL % gdic
    try:
        res = urlfetch.fetch(url)
    except urlfetch.DownloadError, e:
        logging.error('Search Download Error: ' + str(e))
        raise urlfetch.DownloadError
    if 200 != res.status_code:
        logging.error('Search Status Error: ' + str(res.status_code))
        raise Exception('Search Status Error: ' + str(res.status_code))
    gres = parse_json(res.content)
    if 200 != gres['responseStatus']:
        logging.error('Search responseStatus Error: ' + str(gres['responseDetails']))
        raise Exception('Search responseStatus Error: ' + str(gres['responseDetails']))
    return gres['responseData']

apps = webapp.WSGIApplication(
    [
        ('/', Index),
        ('/search', Search),
        ('/archive', Archive),
        ('/a/(.*)', Article),
        ('/k/(.*)', Keyword),
        ('/p/(.*)', Page),
        ('/feed', Atom),
        ('/feed.atom', Atom),
        ('/feed.rss', Rss),
        ('/sitemap.xml', Sitemap),

        ('/(.*)/', Redirect),
        ('.*', Error404),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
