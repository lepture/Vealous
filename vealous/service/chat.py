#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import xmpp, memcache

from libs.mardict import DictCN, GoogleDict
from libs import pydouban
from libs import twitter
import dbs
import config

def star_rate(num):
    ''' 0 <= num <= 5'''
    num = str(num)
    d = {
        '0':u'☆☆☆☆☆',
        '1':u'★☆☆☆☆',
        '2':u'★★☆☆☆',
        '3':u'★★★☆☆',
        '4':u'★★★★☆',
        '5':u'★★★★★',
    }
    return d[num]

help_text = """
Command is leading with '-' or ':'

log -- recent dict log.
rating -- words with exact rating.
mark -- add rate for exact word.
del -- delete exact word.
lan2lan -- eg: zh2en, ja2zh
twitter -- send tweet.
douban -- send douban miniblog.
"""

class CMD(object):
    def __init__(self, content):
        self._content = content
        self.has_cmd = False
    def parse_cmd(self):
        sp = self._content.split()
        cmd = sp[0]
        if cmd[0] not in (':' , '-'):
            return self._google()
        self.has_cmd = True
        self._cmd = cmd[1:]
        self._content = ' '.join(sp[1:])
        if 'help' == self._cmd:
            return help_text
        if 'log' == self._cmd:
            return self._log()
        if 'rating' == self._cmd:
            return self._rating()
        if 'mark' == self._cmd:
            return self._mark()
        if 'del' == self._cmd:
            return self._delete()

        if not self._content:
            return 'You asked nothing'

        if '2' in self._cmd:
            return self._trans2()
        if self._cmd in ('d', 'dict'):
            return self._dict()
        if self._cmd in ('g', 'google'):
            return self._google()
        if self._cmd in ('dt', 'td'):
            reply = self._twitter() + '\n'
            reply += self._douban()
            return reply
        if self._cmd in ('db', 'douban'):
            return self._douban()
        if self._cmd in ('t', 'twitter'):
            return self._twitter()
        return 'Unknown Command'

    def _trans2(self):
        lan = self._cmd.split('2')
        g = GoogleDict(self._content, lan[0], lan[1])
        data = g.reply()
        if data:
            return data['reply']
        return 'Not Found'
    def _dict(self):
        if 'zh' != config.LANGUAGE:
            return 'disabled for international user'
        d = DictCN(self._content)
        data = d.reply()
        if not data:
            return 'Not Found'
        if 'ec' == data['lang']:
            dbs.DictBook.add(data['word'], data['pron'], data['define'])
            memcache.set('dict$last', data)
        return data['reply']
    def _google(self):
        g = GoogleDict(self._content)
        lan = g.detect()
        condition = lan == config.LANGUAGE
        if 'zh' == config.LANGUAGE:
            condition = lan in ('zh-CN', 'zh-TW')
        if condition:
            g = GoogleDict(self._content, lan, 'en')
        else:
            g = GoogleDict(self._content, lan, config.LANGUAGE)
        data = g.reply()
        if data:
            return data['reply']
        return 'Not Found'
    def _log(self):
        if 'zh' != config.LANGUAGE:
            return 'disabled for international user'
        sp = self._content.split()
        if len(sp) == 0:
            start = 0
            end = 10
        elif len(sp) == 1:
            start = 0
            end = sp[0]
        elif len(sp) == 2:
            start = sp[0]
            end = sp[1]
        else:
            start = 0
            end = 10
        logs = dbs.DictBook.get_log(start=start, end=end)
        reply = ''
        for data in logs:
            reply += '%s [%s]\n%s\n' % (data.word, data.pron, data.define)
        if not reply:
            return 'Not Found'
        return reply
    def _rating(self):
        if 'zh' != config.LANGUAGE:
            return 'disabled for international user'
        sp = self._content.split()
        if len(sp) == 0:
            rating = 1
            start = 0
            end = 10
        elif len(sp) == 1:
            rating = sp[0]
            start = 0
            end = 10
        elif len(sp) == 2:
            rating = sp[0]
            start = 0
            end = sp[1]
        elif len(sp) == 3:
            rating = sp[0]
            start = sp[1]
            end = sp[2]
        logs = dbs.DictBook.get_rating(rating = rating, start=start, end=end)
        reply = ''
        for data in logs:
            reply += '%s [%s]\n%s\n' % (data.word, data.pron, data.define)
        if not reply:
            return 'Not Found'
        return reply
    def _mark(self):
        if 'zh' != config.LANGUAGE:
            return 'disabled for international user'
        if self._content:
            data = dbs.DictBook.mark(self._content)
            reply = u'\n%s [%s]\n%s\n' % (data.word, data.pron, data.define)
            reply += u'Has been marked %s' % star_rate(data.rating)
            return reply
        data = memcache.get('dict$last')
        if data is None:
            return 'Mark word Failed'
        data = dbs.DictBook.mark(data['word'])
        reply = '%s [%s]\n%s\n' % (data.word, data.pron, data.define)
        reply += u'Has been marked %s' % star_rate(data.rating)
        return reply
    def _delete(self):
        if 'zh' != config.LANGUAGE:
            return 'disabled for international user'
        if self._content:
            word = self._content
        else:
            data = memcache.get('dict$last')
            if not data:
                return 'Word Not Found'
            word = data.word
        if not word:
            return 'Word Not Found'
        data = dbs.DictBook.delete(word)
        if data:
            return '[%s] has been deleted' % word
        return '[%s] not in Dict book' %  word

    def _douban(self):
        if 'zh' != config.LANGUAGE:
            return 'disabled for international user'
        qs = dbs.Vigo.get('oauth_douban')
        if not qs:
            return 'Douban Not Authed'
        api = pydouban.Api()
        api.set_qs_oauth(config.douban_key, config.douban_secret, qs)
        try:
            api.post_miniblog(self._content)
        except:
            return 'Post to Douban Failed'
        return 'Post to Douban Success'
    def _twitter(self):
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            return 'Twitter Not Authed'
        content = self._content
        if len(self._content) > 140:
            content = content[:133] + '...'
        token = twitter.oauth.Token.from_string(qs)
        api = twitter.Api(config.twitter_key, config.twitter_secret,
                          token.key, token.secret, 'utf-8')
        try:
            api.PostUpdate(content)
        except twitter.TwitterError, e:
            return str(e)
        return 'Post to Twitter Success'

class Chat(webapp.RequestHandler):
    def post(self):
        message = xmpp.Message(self.request.POST)
        sender = message.sender.split('/')[0].lower()
        if sender != config.EMAIL.lower():
            return message.reply('If only you are a god!')
        reply = CMD(message.body).parse_cmd()
        return message.reply(reply)

apps = webapp.WSGIApplication(
    [
        ('/_ah/xmpp/message/chat/', Chat),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
