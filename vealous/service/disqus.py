#-*- coding: utf-8 -*-

from google.appengine.api import urlfetch
from django.utils.simplejson import loads as parse_json
import urllib
import logging

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
