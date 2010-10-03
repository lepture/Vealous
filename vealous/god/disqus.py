#-*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import memcache
from django.utils.simplejson import dumps
from django.utils.simplejson import loads as parse_json
from google.appengine.api import urlfetch
import urllib
import logging

from utils import be_god
from utils.handler import WebHandler
from config import DEBUG
import dbs

class Disqus(object):
    rpc = None

    def __init__(self, key):
        self._key = key

    def get_forum_posts_rpc(self, forumid):
        urlbase = 'http://disqus.com/api/%s/?user_api_key=%s&api_version=1.1'
        method = 'get_forum_posts'
        key = self._key
        url = urlbase % (method, key) + '&limit=10&exclude=killed&forum_id=' + str(forumid)
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, url)
        self.rpc = rpc
        return rpc

    def get_forum_posts_result(self):
        if not self.rpc:
            return None
        try:
            result = self.rpc.get_result()
            if 200 != result.status_code:
                logging.error('get forum posts result failed, status code: ' + str(result.status_code))
                return None
            data = result.content
            return data
        except urlfetch.DownloadError:
            logging.error('get forum posts result failed, urlfetch download error')
            return None
        return None
    
    def parse_data(self, data):
        if not data:
            return None
        json = parse_json(data)
        try:
            code = json['code']
            messages = json['message']
        except:
            return None
        if 'ok' != code:
            logging.info('parse data failed')
            return None
        datalist = []
        for message in messages:
            avatar = 'http://www.gravatar.com/avatar/'
            username = 'anonymous'
            email = 'www@www.www'
            if message['is_anonymous']:
                avatar += message['anonymous_author']['email_hash']
                avatar += '?size=48'
                username = message['anonymous_author']['name']
                email = message['anonymous_author']['email']
            else:
                if message['author']['has_avatar']:
                    avatar = message['author']['avatar']['medium']
                else:
                    avatar += message['author']['email_hash']
                    avatar += '?size=48'
                username = message['author']['display_name'] or message['author']['username']
                email = message['author']['email']
            rdic = {}
            rdic['avatar'] = avatar
            rdic['username'] = username
            rdic['email'] = email
            rdic['ip'] = message['ip_address']
            rdic['comment_id'] = message['id']
            rdic['content'] = message['message']
            rdic['status'] = message['status']
            rdic['created'] = message['created_at']
            rdic['moderated'] = message['has_been_moderated']
            rdic['thread'] = message['thread']
            datalist.append(rdic)
        return datalist

    def moderate_post(self, forum_key, post_id, action):
        url = 'http://disqus.com/api/moderate_post/'
        key = self._key
        payload = {'forum_api_key':forum_key,
                   'user_api_key':key,
                   'post_id':post_id,
                   'action':action} 
        payload = urllib.urlencode(payload)
        result = urlfetch.fetch(url, payload=payload, method='POST').content
        json = parse_json(result)
        if 'ok' != json['code']:
            logging.info('moderate post failed')
            return {'succeeded': False}
        return json

class DisqusModerate(WebHandler):
    @be_god
    def get(self):
        action = self.request.get('action',None)
        post_id = self.request.get('post_id',None)
        forum_key = dbs.Vigo.get('forum_key')
        disqus_key = dbs.Vigo.get('disqus_key')
        self.response.headers['Content-Type'] = 'application/json'
        if action and post_id and forum_key and disqus_key:
            d = Disqus(disqus_key)
            data = d.moderate_post(forum_key,post_id,action)
            if data['succeeded']:
                memcache.delete('disqus$comments')
            return self.response.out.write(dumps(data))
        data = {'succeeded': False}
        return self.response.out.write(dumps(data))



apps = webapp.WSGIApplication(
    [
        ('/god/disqus/moderate', DisqusModerate),
    ],
    debug = DEBUG,
)

if '__main__' == __name__:
    run(apps)
