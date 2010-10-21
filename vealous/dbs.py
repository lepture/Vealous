#-*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.api import memcache
import time
import markdown
import logging

week = 604800
day = 86400

class Note(db.Model):
    slug = db.StringProperty(required=False)
    text = db.TextProperty(indexed=False)
    created = db.DateTimeProperty(auto_now_add=True)

    @property
    def title(self):
        return 'Note-%s' % self.slug
    
    @property
    def the_url(self):
        return '/t/%s' % self.slug

    @classmethod
    def getten(cls):
        data = memcache.get('t$ten')
        if data is not None:
            return data
        q = cls.gql("ORDER BY created DESC")
        data = q.fetch(10)
        memcache.set('t$ten', data, day)
        return data

    @classmethod
    def get(cls, slug):
        key = 't/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        q = cls.gql("WHERE slug= :1", slug)
        data = q.fetch(1)
        if data:
            memcache.set(key, data[0])
            logging.info('Get Note from DB by slug :' + slug)
            return data[0]
        return None

    @classmethod
    def add(cls, text):
        slug = str(int(time.time()))
        key = 't/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        data = Note(slug=slug, text=text)
        data.put()
        memcache.set(key, data)
        memcache.delete('t$ten')
        return data

    @classmethod
    def delete(cls, data):
        keys = ['t/' + data.slug, 't$ten']
        memcache.delete_multi(keys)
        db.delete(data)
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
        data = cls(
            title=title, slug=slug, text=text, draft=draft,
            keyword=keyword, html=markdown.markdown(text),
        )
        data.put()
        memcache.set(key, data)
        keys = ['a$ten', 'a$archive', 'a$keyword/'+data.keyword, 'xml$atom', 'xml$rss', 'xml$sitemap']
        memcache.delete_multi(keys)
        return data

    @classmethod
    def update(cls, data, title, slug, text, draft, keyword='nokeyword'):
        data.title = title
        data.slug = slug
        data.text = text
        data.draft = draft
        data.keyword = keyword
        data.html = markdown.markdown(text)
        data.put()

        keys = ['a/'+data.slug, 'a$ten', 'a$archive', 'a$keyword/'+data.keyword, 'xml$atom', 'xml$rss', 'xml$sitemap']
        memcache.delete_multi(keys)
        return data

    @classmethod
    def sw_status(cls, data, draft=True):
        data.draft = draft
        data.put()
        keys = ['a/'+data.slug, 'a$ten', 'a$archive', 'a$keyword/'+data.keyword, 'xml$atom', 'xml$rss', 'xml$sitemap']
        memcache.delete_multi(keys)
        return data

    @classmethod
    def get(cls, slug):
        key = 'a/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        q = cls.gql("WHERE slug= :1 and draft = :2", slug, False)
        data = q.fetch(1)
        if data:
            memcache.set(key, data[0])
            logging.info('Get Article from DB by slug :' + slug)
            return data[0]
        return None

    @classmethod
    def delete(cls, data):
        keys = ['a/'+data.slug, 'a$ten', 'a$archive', 'a$keyword/'+data.keyword, 'xml$atom', 'xml$rss', 'xml$sitemap']
        memcache.delete_multi(keys)
        db.delete(data)
        return data

    @classmethod
    def getten(cls):
        data = memcache.get('a$ten')
        if data is not None:
            return data
        q = cls.gql("WHERE draft = :1 ORDER BY created DESC", False)
        data = q.fetch(10)
        logging.info('Get Ten Article from DB')
        memcache.set('a$ten', data)
        return data

    @classmethod
    def get_archive(cls):
        data = memcache.get('a$archive')
        if data is not None:
            return data
        q = cls.gql("WHERE draft = :1 ORDER BY created DESC", False)
        data = q.fetch(1000)
        memcache.set('a$archive', data)
        logging.info('Get Archive from DB')
        return data

    @classmethod
    def get_kw_articles(cls, keyword):
        key = 'a$keyword/' + keyword
        data = memcache.get(key)
        if data is not None:
            return data
        q = cls.gql("WHERE keyword = :1 and draft = :2 ORDER BY created DESC", keyword, False)
        data = q.fetch(1000)
        memcache.set(key, data)
        logging.info('Get Articles from DB by keyword : ' + keyword)
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
        q = cls.gql("WHERE name = :1", name)
        data = q.fetch(1)
        if not data:
            return ''
        value = data[0].substance
        memcache.set(key, value, week)
        logging.info('Get Vigo from DB : ' + name)
        return value

    @classmethod
    def set(cls, name, value):
        key = 'vigo/' + name
        q = cls.gql("WHERE name = :1", name)
        data = q.fetch(1)
        if data:
            data = data[0]
        else:
            data = Vigo()
            data.name = name
        data.substance = value
        data.put()
        memcache.set(key, value, week)
        return value

class Melody(db.Model):
    title = db.StringProperty(required=True, indexed=True)
    url = db.StringProperty(required=False, indexed=False) # link, nav, s5 source url
    label = db.StringProperty(required=True, indexed=True) #link, nav, s5, page
    ext = db.StringProperty(required=False, indexed=True) # link rel, s5 slug
    text = db.TextProperty(required=False, indexed=False) # intro, s5 content
    prior = db.IntegerProperty(indexed=True, default=0)

    @classmethod
    def get_s5(cls, slug):
        key = 'melody$s5/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        q = cls.gql("WHERE ext = :1 and label = :2", slug, 's5')
        data = q.fetch(1)
        if not data:
            return None
        data = data[0]
        if data.text:
            logging.info('Get S5 from DB by slug : ' + slug)
            memcache.set(key, data, week)
            return data
        return None

    @classmethod
    def get_page(cls, slug):
        key = 'melody$page/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        q = cls.gql("WHERE ext = :1 and label = :2", slug, 'page')
        data = q.fetch(1)
        if not data:
            return None
        data = data[0]
        if data.text:
            logging.info('Get Page from DB by slug : ' + slug)
            memcache.set(key, data, week)
            return data
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
        q = cls.gql('WHERE label = :1 ORDER BY prior DESC', label)
        data = q.fetch(100)
        memcache.set('melody/%s' % label, data, week)
        return data

    @classmethod
    def delete(cls, data):
        key = 'melody/' + data.label
        memcache.delete(key)
        db.delete(data)
        return data


class DictBook(db.Model):
    word = db.StringProperty(required=True, indexed=True)
    pron = db.StringProperty(required=False)
    define = db.TextProperty(required=False, indexed=False)
    rating = db.IntegerProperty(default=0, indexed=True)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def add(cls, word, pron, define):
        data = cls.get(word)
        if data is not None:
            return data
        data = cls(word=word, pron=pron, define=define)
        data.put()
        memcache.set('dict/' + word, data)
        keys = ['dict$rating/0', 'dict$all']
        memcache.delete_multi(keys)
        return data
    @classmethod
    def get(cls, word):
        key = 'dict/' + word
        data = memcache.get(key)
        if data is not None:
            return data
        q = cls.gql('WHERE word = :1', word)
        data = q.fetch(1)
        if data:
            memcache.set(key, data[0])
            return data[0]
        return None
    @classmethod
    def delete(cls, word):
        data = cls.get(word)
        if data:
            db.delete(data)
            keys = ['dict/'+data.word, 'dict$all', 'dict$rating/'+str(data.rating)]
            memcache.delete_multi(keys)
            return data
        return None
    @classmethod
    def get_log(cls, start=0, end=10):
        data = cls.get_rating(0, start, end)
        return data[start:end]
    @classmethod
    def mark(cls, word):
        data = cls.get(word)
        if data.rating < 5:
            data.rating += 1
        data.put()
        keys = ['dict$rating/'+str(data.rating), 'dict$rating/'+str(data.rating-1), 'dict/'+data.word, 'dict$all']
        memcache.delete_multi(keys)
        return data
    @classmethod
    def get_rating(cls, rating=1, start=0, end=10):
        try: rating = int(rating)
        except: rating = 1
        try: start = int(start)
        except: start = 0
        try: end = int(end)
        except: end = 10
        if rating > 5:
            rating = 5
        elif rating < 0:
            rating = 0
        data = memcache.get('dict$rating/' + str(rating))
        if data is not None:
            return data
        q = cls.gql('WHERE rating=:1 ORDER BY created DESC', rating)
        data = q.fetch(1000)
        return data[start:end]
    @classmethod
    def get_all(cls):
        data = memcache.get('dict$all')
        if data is not None:
            return data
        q = cls.gql('ORDER BY created DESC')
        data = q.fetch(1000)
        memcache.set('dict$all', data)
        return data
