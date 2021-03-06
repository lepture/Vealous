#-*- coding: utf-8 -*-

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django','1.1')
import os.path
import logging
from urllib2 import quote
from django.utils.simplejson import loads as parse_json
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import memcache
from google.appengine.api import urlfetch

from utils.render import render
from utils.handler import BaseHandler
import dbs

import config

def get_path(condition, name):
    if condition:
        path = os.path.join(config.ROOT, 'tpl','mobile' , name)
        return path
    path = os.path.join(config.ROOT, 'tpl', config.THEME, name)
    return path

def get_navs():
    dic = {}
    navs = dbs.Melody.get_all('nav')
    dic['normal'] = filter(lambda nav: 'normal'==nav.ext, navs)
    dic['more'] = filter(lambda nav: 'more'==nav.ext, navs)
    return dic

class Index(BaseHandler):
    def get(self):
        rdic = {}
        keys = dbs.Article.show_keys()[:10]
        articles = dbs.Article.get_data_by_keys(keys)
        if articles:
            rdic['hi'] = articles[0]
            rdic['articles'] = articles[1:6]
        else:
            rdic['articles'] = articles
        rdic['links'] = dbs.Melody.get_all('link')
        rdic['navs'] = get_navs()
        path = get_path(self.is_mobile, 'index.html')
        html = render(path, rdic)
        self.response.out.write(html)

class Article(BaseHandler):
    def head(self, slug):
        pass

    def get(self, slug):
        slug = self.unquote(slug)
        rdic = {}
        data = dbs.Article.get_by_slug(slug)
        if not data:
            logging.info('404 , visite article ' + slug)
            path = get_path(self.is_mobile, '404.html')
            self.response.set_status(404)
            html = render(path, rdic)
            return self.response.out.write(html)
        mode = self.request.get('mode','mark')
        if 'plaintext' == mode:
            if self.is_spider:
                return self.error(404)
            self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
            html = data.text
            return self.response.out.write(html)
        rdic['navs'] = get_navs()
        rdic['data'] = data
        path = get_path(self.is_mobile, 'article.html')
        html = render(path, rdic)
        self.response.out.write(html)

class Archive(BaseHandler):
    def get(self):
        rdic = {}
        rdic['navs'] = get_navs()
        p = self.request.get('p',1)
        keys = dbs.Article.show_keys()
        mvdata = dbs.Article.get_page(keys, p)
        if mvdata['page'] > mvdata['page_num']:
            path = get_path(self.is_mobile, '404.html')
            self.response.set_status(404)
            html = render(path, rdic)
            return self.response.out.write(html)
        rdic['mvdata'] = mvdata
        path = get_path(self.is_mobile, 'archive.html')
        self.response.out.write(render(path,rdic))

class Keyword(BaseHandler):
    def head(self, keyword):
        pass
    def get(self, keyword):
        keyword = self.unquote(keyword)
        rdic = {}
        keys = dbs.Article.kw_keys(keyword)
        if not keys:
            logging.info('404 , visite keyword ' + keyword)
            path = get_path(self.is_mobile, '404.html')
            html = render(path, rdic)
            self.response.set_status(404)
            return self.response.out.write(html)
        p = self.request.get('p',1)
        rdic['mvdata'] = dbs.Article.get_page(keys, p)
        rdic['navs'] = get_navs()
        rdic['links'] = dbs.Melody.get_all('link')
        rdic['keyword'] = keyword
        path = get_path(self.is_mobile, 'keyword.html')
        html = render(path, rdic)
        self.response.out.write(html)

class Page(BaseHandler):
    def get(self, slug):
        slug = self.unquote(slug)
        data = dbs.Page.get_by_slug(slug)
        rdic = {}
        rdic['navs'] = get_navs()
        rdic['links'] = dbs.Melody.get_all('link')
        if not data:
            logging.info('404 , visite page ' + slug)
            path = get_path(self.is_mobile, '404.html')
            self.response.set_status(404)
            html = render(path, rdic)
            return self.response.out.write(html)
        rdic['data'] = data
        path = get_path(self.is_mobile, 'page.html')
        html = render(path, rdic)
        self.response.out.write(html)

class DEMO(BaseHandler):
    def get(self, slug):
        slug = self.unquote(slug)
        data = dbs.Melody.get_demo(slug)
        rdic = {}
        rdic['navs'] = get_navs()
        rdic['links'] = dbs.Melody.get_all('link')
        if not data:
            logging.info('404 , visite demo ' + slug)
            path = get_path(self.is_mobile, '404.html')
            self.response.set_status(404)
            html = render(path, rdic)
            return self.response.out.write(html)
        self.response.headers['Content-Type'] = data.ext or 'text/html'
        self.response.out.write(data.text)


class Search(BaseHandler):
    def get(self):
        rdic = {}
        cx = config.gcse
        rdic['q'] = q = self.request.get('q','Vealous')
        rdic['start'] = start = self.request.get('start', '0')
        try:
            rdic['gres'] = gsearch(q, start, cx)
        except:
            rdic['error'] = 'Oops! An Error occured!'
        rdic['navs'] = get_navs()
        path = get_path(self.is_mobile, 'search.html')
        self.response.out.write(render(path,rdic))

class Atom(BaseHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        html = memcache.get('a_atom')
        if html is not None:
            return self.response.out.write(html)
        rdic = {}
        keys = dbs.Article.show_keys()[:10]
        rdic['datas'] = dbs.Article.get_data_by_keys(keys)
        path = os.path.join(config.ROOT, 'tpl', 'atom.xml')
        html = render(path, rdic)
        memcache.set('a_atom', html)
        self.response.out.write(html)

class Rss(BaseHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        html = memcache.get('a_rss')
        if html is not None:
            return self.response.out.write(html)
        rdic = {}
        keys = dbs.Article.show_keys()[:10]
        rdic['datas'] = dbs.Article.get_data_by_keys(keys)
        path = os.path.join(config.ROOT, 'tpl', 'rss.xml')
        html = render(path, rdic)
        memcache.set('a_rss', html)
        self.response.out.write(html)

class Sitemap (BaseHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        html = memcache.get('a_sitemap')
        if html is not None:
            return self.response.out.write(html)
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
        keys = dbs.Article.show_keys()
        articles = dbs.Article.get_data_by_keys(keys)
        for art in articles:
            addurl(art.the_url, art.modified,'weekly',0.5)
        rdic['urlset'] = urlset
        path = os.path.join(config.ROOT, 'tpl', 'sitemap.xml')
        html = render(path, rdic)
        memcache.set('a_sitemap', html)
        self.response.out.write(html)

class Redirect(BaseHandler):
    def get(self, path):
        logging.info('redirect from path ' + path)
        self.redirect('/' + path)

class Error404(BaseHandler):
    def get(self):
        logging.info('404')
        rdic = {}
        path = get_path(self.is_mobile, '404.html')
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
        ('/d/(.*)', DEMO),
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
