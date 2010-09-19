#-*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
import time
import markdown

month = 2592000
week = 604800
day = 86400

class Note(db.Model):
    slug = db.StringProperty(required=False)
    text = db.TextProperty(indexed=False)
    created = db.DateTimeProperty(auto_now_add=True)
    
    @classmethod
    def getten(cls):
        data = memcache.get('t$ten')
        if data is not None:
            return data
        q = Note.gql("ORDER BY created DESC")
        data = q.fetch(10)
        memcache.set('t$ten', data, day)
        return data

    @classmethod
    def add(cls, text):
        slug = str(int(time.time()))
        key = 't/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        data = Note(slug=slug, text=text)
        data.put()
        memcache.set(key, data, month)
        memcache.delete('t$ten')
        return data

    @classmethod
    def delete(cls, data):
        key = 't/' + data.slug
        memcache.delete(key)
        db.delete(data)
        memcache.delete('t$ten')
        return data

class Article(db.Model):
    title = db.StringProperty(required=True)
    slug = db.StringProperty(required=True)
    text = db.TextProperty(indexed=False)
    keyword = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    draft = db.BooleanProperty(required=True, default=False)
    # formated text
    html = db.TextProperty(indexed=False)

    @property
    def the_url(self):
        return '/a/%s' % self.slug
    
    @classmethod
    def add(cls, title, slug, text, draft, keyword='nokeyword'):
        key = 'a/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        data = Article(
            title=title, slug=slug, text=text, draft=draft,
            keyword=keyword, html=markdown.markdown(text),
        )
        data.put()
        memcache.set(key, data, month)
        memcache.delete('a$ten')
        key = 'a$keyword/' + data.keyword
        memcache.delete(key)
        return data

    @classmethod
    def update(cls, data, title, slug, text, draft, keyword='nokeyword'):
        key = 'a/' + data.slug
        data.title = title
        data.slug = slug
        data.text = text
        data.draft = draft
        data.keyword = keyword
        data.html = markdown.markdown(text)
        data.put()
        memcache.delete(key)
        memcache.delete('a$ten')
        key = 'a/keyword/' + data.keyword
        memcache.delete(key)
        return data

    @classmethod
    def get(cls, slug):
        key = 'a/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        q = Article.gql("WHERE slug= :1 and draft = :2", slug, False)
        data = q.fetch(1)
        if data:
            memcache.set(key, data[0], month)
            return data[0]
        return None

    @classmethod
    def delete(cls, data):
        key = 'a/' + data.slug
        memcache.delete(key)
        key = 'a$keyword/' + data.keyword
        memcache.delete(key)
        memcache.delete('a$ten')
        db.delete(data)
        return data

    @classmethod
    def getten(cls):
        data = memcache.get('a$ten')
        if data is not None:
            return data
        q = Article.gql("WHERE draft = :1 ORDER BY created DESC", False)
        data = q.fetch(10)
        memcache.set('a$ten', data, day)
        return data

    @classmethod
    def keyword_article(cls, keyword):
        key = 'a$keyword/' + keyword
        data = memcache.get(key)
        if data is not None:
            return data
        q = Article.gql("WHERE keyword = :1 and draft = :2 ORDER BY created DESC", keyword, False)
        data = q.fetch(10)
        memcache.set(key, data, week)
        return data

class Vigo(db.Model):
    # settings: key - value
    name = db.StringProperty(required=False, indexed=True)
    substance = db.TextProperty(required=False, indexed=False)
    
    @classmethod
    def get(cls, name):
        key = 'vigo/' + name
        value = memcache.get(key)
        if value is not None:
            return value
        q = Vigo.gql("WHERE name = :1", name)
        data = q.fetch(1)
        if not data:
            return ''
        value = data[0].substance
        memcache.set(key, value, month)
        return value

    @classmethod
    def set(cls, name, value):
        key = 'vigo/' + name
        q = Vigo.gql("WHERE name = :1", name)
        data = q.fetch(1)
        if data:
            data = data[0]
        else:
            data = Vigo()
            data.name = name
        data.substance = value
        data.put()
        memcache.set(key, value, month)
        return value

class Melody(db.Model):
    title = db.StringProperty(required=True, indexed=True)
    url = db.StringProperty(required=True, indexed=False) # link, nav, s5 source url
    label = db.StringProperty(required=True, indexed=True) #link, nav, s5
    ext = db.StringProperty(required=False, indexed=True) # link rel, s5 slug
    text = db.TextProperty(required=False, indexed=False) # intro, s5 content
    prior = db.IntegerProperty(indexed=True, default=0)

    @classmethod
    def get_s5(cls, slug):
        key = 'melody$s5/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        q = Melody.gql("WHERE ext = :1 and label = :2", slug, 's5')
        data = q.fetch(1)
        if not data:
            return None
        data = data[0]
        if data.text:
            memcache.set(key, data, week)
            return data
        try:
            result = urlfetch.fetch(data.url)
            if 200 != result.status_code:
                return None
            text = unicode(result.content, 'utf-8')
            data.text = text
            data.put()
            memcache.set(key, data, week)
            return data
        except urlfetch.DownloadError:
            return None
        return None

    @classmethod
    def add(cls, title, url, label, prior, ext=None, text=None):
        data = Melody(
            title=title, url=url, label=label,
            ext=ext, text=text, prior=prior,
        )
        data.put()
        memcache.delete('melody/%s' % label)
        return data

    @classmethod
    def update(cls, data, title, url, label, prior, ext=None, text=None):
        data.title = title
        data.url = url
        data.label = label
        data.prior = prior
        data.ext = ext
        data.text = text
        data.put()
        memcache.delete('melody/%s' % label)
        return data

    @classmethod
    def get_all(cls, label):
        data = memcache.get('melody/%s' % label)
        if data is not None:
            return data
        q = Melody.gql('WHERE label = :1 ORDER BY prior DESC', label)
        data = q.fetch(100)
        memcache.set('melody/%s' % label, data, week)
        return data

    @classmethod
    def delete(cls, data):
        key = 'melody/' + data.label
        memcache.delete(key)
        db.delete(data)
        return data
