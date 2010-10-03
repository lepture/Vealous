#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import xmpp

from utils.mardict import DictCN, GoogleDict
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
        return self._google()

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
