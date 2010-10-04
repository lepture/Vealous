#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import xmpp

from utils.mardict import DictCN, GoogleDict
from libs import pydouban
from libs import twitter
import dbs
import config

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
        if not self._content:
            return 'You asked nothing'
        if '2' in self._cmd:
            return self._trans2()
        if 'd' == self._cmd or 'dict' == self._cmd:
            return self._dict()
        if 'g' == self._cmd or 'google' == self._cmd:
            return self._google()
        if 'n' == self._cmd or 'note' == self._cmd:
            reply = self._note() + '\n'
            reply += self._twitter() + '\n'
            reply += self._douban()
            return reply
        if 'db' == self._cmd or 'douban' == self._cmd:
            return self._douban()
        if 't' == self._cmd or 'twitter' == self._cmd:
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
        d = DictCN(self._content)
        data = d.reply()
        if data:
            return data['reply']
        return 'Not Found'
    def _google(self):
        g = GoogleDict(self._content)
        lan = g.detect()
        if lan in ('zh-CN' or 'zh-TW'):
            g = GoogleDict(self._content, lan, 'en')
        g = GoogleDict(self._content, lan, 'zh')
        data = g.reply()
        if data:
            return data['reply']
        return 'Not Found'
    def _note(self):
        note = dbs.Note.add(self._content)
        return 'Note Saved'
    def _douban(self):
        qs = dbs.Vigo.get('oauth_douban')
        api = pydouban.Api()
        api.set_qs_oauth(config.douban_key, config.douban_secret, qs)
        try:
            api.post_miniblog(self._content)
        except:
            return 'Post to Douban Failed'
        return 'Post to Douban Success'
    def _twitter(self):
        content = self._content
        if len(self._content) > 140:
            content = content[:133] + '...'
        try: content = content.encode('utf-8')
        except UnicodeDecodeError: pass
        qs = dbs.Vigo.get('oauth_twitter')
        token = twitter.oauth.Token.from_string(qs)
        api = twitter.Api(config.twitter_key, config.twitter_secret,
                          token.key, token.secret)
        try:
            api.PostUpdate(content)
        except:
            return 'Post to Twitter Failed'
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
