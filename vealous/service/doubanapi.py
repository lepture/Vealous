from google.appengine.api import urlfetch
import oauth2 as oauth
import logging

try:
    from urlparse import parse_qs, parse_qsl
except ImportError:
    from cgi import parse_qs, parse_qsl

AUTH_URL = 'http://www.douban.com/service/auth/'
API_URL = 'http://api.douban.com/'

class DoubanClient(object):
    def __init__(self, consumer, token=None):

        if consumer is not None and not isinstance(consumer, oauth.Consumer):
            raise ValueError("Invalid consumer.")

        if token is not None and not isinstance(token, oauth.Token):
            raise ValueError("Invalid token.")

        self.consumer = consumer
        self.token = token
        self.method = oauth.SignatureMethod_HMAC_SHA1()

    def set_signature_method(self, method):
        if not isinstance(method, oauth.SignatureMethod):
            raise ValueError("Invalid signature method.")
        self.method = method

    def set_header(self, method, uri, param):
        headers = {}
        req = oauth.Request.from_consumer_and_token(self.consumer, 
            token=self.token, http_method=method, http_url=uri, 
            parameters=param)
        req.sign_request(self.method, self.consumer, self.token)
        headers.update(req.to_header())
        DEFAULT_CONTENT_TYPE = 'application/x-www-form-urlencoded'
        if method in ('POST', 'PUT'):
            headers['Content-Type'] = 'application/atom+xml; charset=utf-8'
        else:
            headers['Content-Type'] = DEFAULT_CONTENT_TYPE
        return headers

    def get_url(self, uri, method="GET", param={}):
        req = oauth.Request.from_consumer_and_token(self.consumer, 
            token=self.token, http_method=method, http_url=uri, 
            parameters=param)
        req.sign_request(self.method, self.consumer, self.token)
        uri = req.to_url()
        return uri

    def request(self, uri):
        try:
            res = urlfetch.fetch(uri)
        except urlfetch.DownloadError, e:
            logging.error('OAuth Request Token Error: ' + str(e))
            raise urlfetch.DownloadError
        if 200 != res.status_code:
            logging.error('OAuth Request Token Error: ' + str(res.status_code))
            raise Exception('OAuth Request Token Error: ' + str(res.status_code))
        content = res.content
        return content

    def post_data(self, uri, body=None, param=None):
        method = 'POST'
        headers = self.set_header(method, uri, param)

        try:
            res = urlfetch.fetch(uri, method=method, payload=body, headers=headers)
        except urlfetch.DownloadError, e:
            logging.error('OAuth Post Data Error: ' + str(e))
            raise urlfetch.DownloadError
        if 201 != res.status_code:
            logging.error('OAuth Request Token Error: ' + str(res.status_code))
            raise Exception('OAuth Request Token Error: ' + str(res.status_code))
        return True

def to_atom(content):
    atom = '<?xml version="1.0" encoding="UTF-8"?>'
    atom += '<entry xmlns:ns0="http://www.w3.org/2005/Atom" xmlns:db="http://www.douban.com/xmlns/">'
    atom += '<content>'
    atom += content.encode('utf-8')
    atom += '</content></entry>'
    return atom

def set_consumer(key, secret):
    consumer = oauth.Consumer(key, secret)
    return consumer

def set_token(key, secret):
    token = oauth.Token(key, secret)
    return token

def set_qs_token(qs):
    token = oauth.Token.from_string(qs)
    return token

def request_token(consumer):
    rq_url = AUTH_URL + 'request_token'
    client = DoubanClient(consumer)
    uri = client.get_url(rq_url)
    qs = client.request(uri)
    return qs

def authorize(consumer, token, callback):
    auth_url = AUTH_URL + 'authorize'
    client = DoubanClient(consumer, token)
    uri = client.get_url(auth_url) + '&oauth_callback=' + callback
    return uri

def access_token(consumer, token):
    acs_url = AUTH_URL + 'access_token'
    client = DoubanClient(consumer, token)
    uri = client.get_url(acs_url)
    qs = client.request(uri)
    return qs

def miniblog_saying(consumer, token, content):
    res_url = API_URL + 'miniblog/saying'
    client = DoubanClient(consumer, token)
    body = to_atom(content)
    return client.post_data(res_url, body)

