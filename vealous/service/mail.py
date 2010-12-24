#-*- coding: utf-8 -*-

import logging
import re
import urllib2
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

import dbs
import config

def is_god(sender):
    """
    sender:
        user@example.com
        User <user@example.com>
    """
    regex1 = r'^%s$' % config.EMAIL
    regex2 = r'<%s>$' % config.EMAIL
    if re.search(regex1, sender) or re.search(regex2, sender):
        return True
    return False

class Article(InboundMailHandler):
    def receive(self, message):
        if not is_god(message.sender):
            logging.info('Not Admin: %s' % message.sender)
            return
        data = self.format(message)
        if not data:
            return
        title, slug, keyword, text = data
        dbs.Article.add(title, slug, text, False, keyword)
        return

    def format(self, message):
        if not hasattr(message, 'subject'):
            return False
        if not hasattr(message, 'body'):
            return False
        subjects = message.subject.split(',')
        text = message.body.decode()
        if 3 <= len(subjects):
            title, slug, keyword = subjects
            return title, slug, keyword, text
        elif 1 == len(subjects):
            return subjects[0], subjects[0], '', text
        elif 2 == len(subjects):
            return subjects[0], subjects[1], '', text
        return False

class Page(InboundMailHandler):
    def receive(self, message):
        if not is_god(message.sender):
            logging.info('Not Admin: %s' % message.sender)
            return
        data = self.format(message)
        if not data:
            return
        title, slug, text = data
        dbs.Page.add(title, slug, text)
        return

    def format(self, message):
        if not hasattr(message, 'subject'):
            return False
        if not hasattr(message, 'body'):
            return False
        subjects = message.subject.split(',')
        text = message.body.decode()
        if 1 == len(subjects):
            return subjects[0], subjects[0], text
        else:
            return subjects[0], subjects[1], text
        return False


_article_url = '/_ah/mail/article-%s' % urllib2.quote(config.BLOG_EMAIL)
_page_url = '/_ah/mail/page-%s' % urllib2.quote(config.BLOG_EMAIL)
apps = webapp.WSGIApplication(
    [
        (_article_url, Article),
        (_page_url, Page),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
