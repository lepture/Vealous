#-*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.api import memcache
from libs import markdown
import logging

week = 604800

def make_int(num):
    try:
        return int(num)
    except:
        return 0

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
    def add(cls, title, slug, text, draft, keyword=''):
        key = 'a_slug_' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        data = cls(
            title=title, slug=slug, text=text, draft=draft,
            keyword=keyword, html=markdown.markdown(text),
        )
        data.put()
        memcache.set(key, data)

        keys = ['a_atom', 'a_rss', 'a_sitemap', 'a_all', 'a_show']
        keys.append('a_kw_%s' % keyword)
        memcache.delete_multi(keys)
        return data

    def update(self, title, slug, text, draft, keyword=''):
        keys = ['a_atom', 'a_rss', 'a_sitemap', 'a_all', 'a_show']
        if self.keyword != keyword:
            keys.append('a_kw_%s' % keyword)
            keys.append('a_kw_%s' % self.keyword)
        keys.append(str(self.key()))
        memcache.delete_multi(keys)

        self.title = title
        self.slug = slug
        self.text = text
        self.draft = draft
        self.keyword = keyword
        self.html = markdown.markdown(text)
        self.put()

        key = 'a_slug_' + slug
        memcache.set(key, self)
        return self

    def sw_status(self, draft=True):
        keys = ['a_atom', 'a_rss', 'a_sitemap', 'a_show']
        keys.append('a_kw_%s' % self.keyword)
        keys.append(str(self.key()))
        if self.draft and not draft:
            self.draft = draft
            self.put()
        elif not self.draft and draft:
            self.draft = draft
            self.put()
        memcache.delete_multi(keys)
        key = 'a_slug_' + self.slug
        memcache.set(key, self)
        return self 

    def delete(self):
        keys = ['a_atom', 'a_rss', 'a_sitemap', 'a_show']
        keys.append('a_kw_%s' % self.keyword)
        keys.append('a_slug_%s' % self.slug)
        memcache.delete_multi(keys)
        db.delete(self)
        return self

    @classmethod
    def get_by_slug(cls, slug):
        key = 'a_' + slug
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
    def get_by_key(cls, key):
        data = memcache.get(key)
        if data is not None:
            return data
        data = db.get(key)
        if not data:
            return None
        memcache.set(key, data)
        return data

    @classmethod
    def show_keys(cls):
        data = memcache.get('a_show')
        if data is not None:
            return data
        q = db.GqlQuery('SELECT __key__ from Article WHERE draft = :1 ORDER BY created DESC', False)
        data = [str(key) for key in q]
        memcache.set('a_show', data)
        return data

    @classmethod
    def all_keys(cls):
        data = memcache.get('a_all')
        if data is not None:
            return data
        q = db.GqlQuery('SELECT __key__ from Article ORDER BY created DESC')
        data = [str(key) for key in q]
        memcache.set('a_all', data)
        return data

    @classmethod
    def kw_keys(cls, keyword):
        key = 'a_kw_%s' % keyword
        data = memcache.get(key)
        if data is not None:
            return data
        q = db.GqlQuery('SELECT __key__ from Article WHERE keyword = :1 AND draft = :2 ORDER BY created DESC', keyword, False)
        data = [str(k) for k in q]
        memcache.set(key, data)
        return data

    @classmethod
    def get_articles_by_keys(cls, keys):
        data = memcache.get_multi(keys)
        miss = list(set(keys) - set(data.keys()))
        if miss:
            logging.info('Missing keys: ' + str(miss))
        for key in miss:
            data.update({key: cls.get_by_key(key)})
        articles = sorted(data.itervalues(), key = lambda x:x.created, reverse=True)
        return articles

    @classmethod
    def get_page(cls, keys, p=1):
        try:
            p = int(p)
        except:
            p = 1
        item_num = len(keys)
        if item_num % 10:
            page_num = item_num / 10 + 1
        else:
            page_num = item_num / 10 
        has_previous = p > 1
        previous_num = p - 1
        has_next = p < page_num
        next_num = p + 1
        show_first = p > 5
        show_first_dash = show_first and p != 6
        show_last = (page_num - p) > 5
        show_last_dash = show_last and (page_num - p) != 6
        page_range = [i for i in range(p-4, p+5) if i in range(1, page_num+1)]
        _start = (p-1)*10
        _end = p*10
        object_list = cls.get_articles_by_keys(keys[_start:_end])
        rdic = {
            'p':p, 'item_num':item_num, 'page_num':page_num,
            'has_previous':has_previous, 'previous_num':previous_num,
            'has_next':has_next,'next_num':next_num,
            'show_first':show_first, 'show_first_dash':show_first_dash,
            'show_last':show_last, 'show_last_dash':show_last_dash,
            'page_range':page_range, 'object_list':object_list
        }
        return rdic

class Page(db.Model):
    title = db.StringProperty(required=True)
    slug = db.StringProperty(required=True)
    text = db.TextProperty(indexed=False)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    # formated text
    html = db.TextProperty(indexed=False)

    @property
    def the_url(self):
        return '/p/%s' % self.slug
    
    @classmethod
    def add(cls, title, slug, text):
        key = 'p/' + slug
        data = memcache.get(key)
        if data is not None:
            return data
        data = cls(title=title, slug=slug, text=text, html=markdown.markdown(text))
        data.put()
        memcache.set(key, data)
        keys = ['p$all']
        memcache.delete_multi(keys)
        return data

    def update(self, title, slug, text):
        self.title = title
        self.slug = slug
        self.text = text
        self.html = markdown.markdown(text)
        self.put()
        keys = ['p/'+self.slug, 'p$all']
        memcache.delete_multi(keys)
        return self

    def delete(self):
        keys = ['p_slug_%s' % self.slug, 'p$all']
        memcache.delete_multi(keys)
        db.delete(self)
        return self

    @classmethod
    def get_by_slug(cls, slug):
        key = 'p_slug_%s' % slug
        data = memcache.get(key)
        if data is not None:
            return data
        q = cls.gql("WHERE slug= :1", slug)
        data = q.fetch(1)
        if data:
            memcache.set(key, data[0])
            logging.info('Get Page from DB by slug :' + slug)
            return data[0]
        return None

    @classmethod
    def get_all(cls):
        data = memcache.get('p$all')
        if data is not None:
            return data
        q = cls.gql("ORDER BY created DESC")
        data = q.fetch(1000)
        memcache.set('p$all', data)
        logging.info('Get All Page from DB')
        return data

class Vigo(db.Model):
    # settings: key - value
    name = db.StringProperty(required=False, indexed=True)
    substance = db.TextProperty(required=False, indexed=False)
    
    @classmethod
    def get(cls, name):
        key = 'vigo_' + name
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
        key = 'vigo_' + name
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
    """
    Nav, Link, DEMO
    """
    title = db.StringProperty(required=True, indexed=True)
    url = db.StringProperty(required=False, indexed=True)
    label = db.StringProperty(required=True, indexed=True)
    ext = db.StringProperty(required=False, indexed=True)
    text = db.TextProperty(required=False, indexed=False)
    prior = db.IntegerProperty(indexed=True, default=0)

    @classmethod
    def get_demo(cls, url):
        key = 'melody$demo/' + url
        data = memcache.get(key)
        if data is not None:
            return data
        q = cls.gql('WHERE label = :1 AND url = :2', 'demo', url)
        data = q.fetch(1)
        if data:
            memcache.set(key, data[0])
            logging.info('Get DEMO from DB by url:' + url)
            return data[0]
        return None


    @classmethod
    def add(cls, title, url, label, prior, ext=None, text=None):
        data = Melody(
            title=title, url=url, label=label,
            ext=ext, text=text, prior=prior,
        )
        data.put()
        memcache.delete('melody$%s' % label)
        return data

    def update(self, title, url, label, prior, ext=None, text=None):
        self.title = title
        self.url = url
        self.label = label
        self.prior = prior
        self.ext = ext
        self.text = text
        self.put()
        memcache.delete('melody$'+label)
        if 'demo' == label:
            memcache.delete('melody$demo/'+ext)
        return self

    @classmethod
    def get_all(cls, label):
        data = memcache.get('melody$%s' % label)
        if data is not None:
            return data
        q = cls.gql('WHERE label = :1 ORDER BY prior DESC', label)
        data = q.fetch(100)
        memcache.set('melody$%s' % label, data)
        logging.info('Get Melody from DB by label: ' + label)
        return data

    @classmethod
    def delete(cls, data):
        key = 'melody$' + data.label
        memcache.delete(key)
        db.delete(data)
        return data

class DictBook(db.Model):
    word = db.StringProperty(indexed=True)
    pron = db.StringProperty()
    define = db.TextProperty()

    rating = db.IntegerProperty(default=0, indexed=True)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def add(cls, word, pron, define):
        data = cls.get(word)
        if data is not None:
            return data
        key = 'dict/' + word
        data = cls(key_name=key, word=word, pron=pron, define=define)
        data.put()
        memcache.set(key, data)
        keys = ['dict$rating/0', 'dict$all']
        memcache.delete_multi(keys)
        return data
    @classmethod
    def get(cls, word):
        key = 'dict/' + word
        data = memcache.get(key)
        if data is not None:
            return data
        data = cls.get_by_key_name(key)
        if data:
            memcache.set(key, data)
            return data
        return None
    @classmethod
    def delete(cls, word):
        data = cls.get(word)
        if not data:
            return None
        db.delete(data)
        key = 'dict/' + word
        keys = [key, 'dict$all', 'dict$rating/'+str(data.rating)]
        memcache.delete_multi(keys)
        return data
    @classmethod
    def mark(cls, word):
        data = cls.get(word)
        if not data:
            return None
        if data.rating >= 5:
            return data
        data.rating += 1
        data.put()
        keys = ['dict$rating/'+str(data.rating), 'dict$rating/'+str(data.rating-1), 'dict/'+data.word, 'dict$all']
        memcache.delete_multi(keys)
        return data
    @classmethod
    def rating_data(cls, rating=1):
        try: rating = int(rating)
        except: rating = 1
        if rating > 5:
            rating = 5
        elif rating < 0:
            rating = 0
        data = memcache.get('dict$rating/' + str(rating))
        if data is not None:
            return data
        q = cls.gql('WHERE rating=:1 ORDER BY created DESC', rating)
        data = q.fetch(1000)
        return data
    @classmethod
    def get_rating(cls, rating=1, start=0, end=10):
        try: start = int(start)
        except: start = 0
        try: end = int(end)
        except: end = 10
        data = cls.rating_data(rating)
        return data[start:end]
    @classmethod
    def get_log(cls, start=0, end=10):
        data = cls.get_rating(0, start, end)
        return data
    @classmethod
    def get_all(cls):
        data = memcache.get('dict$all')
        if data is not None:
            return data
        q = cls.gql('ORDER BY created DESC')
        data = q.fetch(1000)
        memcache.set('dict$all', data)
        return data

