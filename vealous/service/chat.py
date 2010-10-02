#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import xmpp
import config

class Chat(webapp.RequestHandler):
    def post(self):
        message = xmpp.Message(self.request.POST)
        if message.sender != config.EMAIL:
            return message.reply('If only you are a god!')
        return message.reply('You are God')

apps = webapp.WSGIApplication(
    [
        ('/_ah/xmpp/message/chat/', Chat),
    ],
    debug = config.DEBUG,
)

if '__main__' == __name__:
    run(apps)
