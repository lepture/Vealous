
import urlparse
import base64
import logging
from wsgiref.util import is_hop_by_hop

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run
from google.appengine.api import urlfetch

from cgi import parse_qs,parse_qsl
from hashlib import sha1
from hmac import new as hmac
from random import getrandbits
from time import time
from urllib import urlencode,quote as urlquote,unquote as urlunquote

import dbs
from config import twitter_key, twitter_secret, SECRET, DEBUG
class OAuthException(Exception):
    pass

class OAuthClient():

    def __init__(self, service_name, consumer_key, consumer_secret, request_url,
               access_url, callback_url=None):
        """ Constructor."""

        self.service_name = service_name
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.request_url = request_url
        self.access_url = access_url
        self.callback_url = callback_url

    def prepare_request(self, url, token="", secret="", additional_params=None,
                      method=urlfetch.GET):
        """Prepare Request.

        Prepares an authenticated request to any OAuth protected resource.

        Returns the payload of the request.
        """

        def encode(text):
          return urlquote(str(text), "")

        params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time())),
            "oauth_nonce": str(getrandbits(64)),
            "oauth_version": "1.0"
        }

        if token:
            params["oauth_token"] = token
        elif self.callback_url:
            params["oauth_callback"] = self.callback_url

        if additional_params:
            params.update(additional_params)

        for k,v in params.items():
            if isinstance(v, unicode):
                params[k] = v.encode('utf8')
            if type(v) is str:
                params[k] = params[k].replace("~","~~~")
            
        # Join all of the params together.
        params_str = "&".join(["%s=%s" % (encode(k), encode(params[k]))
                               for k in sorted(params)])

        # Join the entire message together per the OAuth specification.
        message = "&".join(["GET" if method == urlfetch.GET else "POST",
                            encode(url), encode(params_str)])

        # Create a HMAC-SHA1 signature of the message.
        key = "%s&%s" % (self.consumer_secret, secret) # Note compulsory "&".
        message = message.replace('%257E%257E%257E', '~')
        signature = hmac(key, message, sha1)
        digest_base64 = signature.digest().encode("base64").strip()
        params["oauth_signature"] = digest_base64

        # Construct the request payload and return it
        return urlencode(params).replace('%7E%7E%7E', '~')
    
    
    def make_async_request(self, url, token="", secret="", additional_params=None,
                   protected=False, method=urlfetch.GET):
        """Make Request.

        Make an authenticated request to any OAuth protected resource.

        If protected is equal to True, the Authorization: OAuth header will be set.

        A urlfetch response object is returned.
        """
        
        (scm, netloc, path, params, query, _) = urlparse.urlparse(url)
        url = None
        query_params = None
        if query:
            query_params = dict([(k,v) for k,v in parse_qsl(query)])
            additional_params.update(query_params)
        url = urlparse.urlunparse(('https', netloc, path, params, '', ''))
        
        payload = self.prepare_request(url, token, secret, additional_params, method)

        if method == urlfetch.GET:
            url = "%s?%s" % (url, payload)
            payload = None
        headers = {"Authorization": "OAuth"} if protected else {}

        rpc = urlfetch.create_rpc(deadline=10.0)
        urlfetch.make_fetch_call(rpc, url, method=method, headers=headers, payload=payload)
        return rpc

    def make_request(self, url, token="", secret="", additional_params=None,
                                      protected=False, method=urlfetch.GET):
        data = self.make_async_request(url, token, secret, additional_params, protected, method).get_result()
        
        if data.status_code != 200:
            logging.debug(data.status_code)
            logging.debug(url)
            logging.debug(token)
            logging.debug(secret)
            logging.debug(additional_params)
            logging.debug(data.content)
        return data

    
class TwitterClient(OAuthClient):

    def __init__(self, consumer_key, consumer_secret, callback_url):
        """Constructor."""

        OAuthClient.__init__(self,
                "twitter",
                consumer_key,
                consumer_secret,
                "https://api.twitter.com/oauth/request_token",
                "https://api.twitter.com/oauth/access_token",
                callback_url)


def convertUrl(orig_url):
    (scm, netloc, path, params, query, _) = urlparse.urlparse(orig_url)
    
    path = path.replace('/gtap','').replace('//','/')
    path_parts = path.split('/')
    if 'api' == path_parts[1] or 'search' == path_parts[1]:
        sub_head = path_parts[1]
        path_parts = path_parts[2:]
        path_parts.insert(0,'')
        new_path = '/'.join(path_parts).replace('//', '/')
        new_netloc = sub_head + '.twitter.com'
    elif path_parts[1].startswith('search'):
        new_path = path
        new_netloc = 'search.twitter.com'
    else:
        new_path = path
        new_netloc = 'twitter.com'
    new_path = new_path.replace('//','/')
    new_url = urlparse.urlunparse(('https',new_netloc, new_path, params, query, ''))
    return new_url, new_path

def parseAuthHeader(headers):
    username = None
    password = None
    if 'Authorization' in headers:
        auth_header = headers['Authorization']
        auth_parts = auth_header.split(' ')
        user_parts = base64.b64decode(auth_parts[1]).split(':')
        username = user_parts[0]
        password = user_parts[1]
    return username, password

class Gtap(webapp.RequestHandler):
    def do_proxy(self, method):
        orig_url = self.request.url
        orig_body = self.request.body

        new_url, new_path = convertUrl(orig_url)
        #logging.info('new url: %s | new path: %s' % (new_url, new_path))
        if "/" == new_path or "" == new_path:
            logging.debug('GFW is broken')
            return self.response.out.write("GFW is broken")
        username, password = parseAuthHeader(self.request.headers)
        if username is None:
            logging.debug('Need a username')
            return self.response.out.write("Need a username")
        if username != dbs.Vigo.get('twitter'):
            logging.debug('Wrong username')
            return self.response.out.write("Wrong username")
        password = sha1(password + SECRET).hexdigest()
        if password != dbs.Vigo.get('password'):
            logging.debug('Wrong password')
            return self.response.out.write("Wrong Password")
        qs = dbs.Vigo.get('oauth_twitter')
        if not qs:
            logging.debug('Not Authed')
            return self.response.out.write("Not Authed")
        qs = dict(parse_qsl(qs))
        user_access_token = qs['oauth_token']
        user_access_secret = qs['oauth_token_secret']
        additional_params = dict([(k,v) for k, v in parse_qsl(orig_body)])
        use_method = urlfetch.GET if method=="GET" else urlfetch.POST
        client = TwitterClient(twitter_key, twitter_secret, None)
        try:
            data = client.make_request(
                url=new_url, token=user_access_token,
                secret=user_access_secret, method=use_method,
                protected=True, additional_params = additional_params)
        except Exception, e:
            logging.debug(e)
            return self.response.out.write(e)
        for res_name, res_value in data.headers.items():
            if is_hop_by_hop(res_name) is False and res_name != 'status':
                self.response.headers.add_header(res_name, res_value)
        #logging.debug(data.content)
        return self.response.out.write(data.content)

    def post(self):
        self.do_proxy("POST")

    def get(self):
        self.do_proxy("GET")

apps = webapp.WSGIApplication(
    [
        ('/gtap/.*', Gtap),
    ],
    debug = DEBUG,
)

if '__main__' == __name__:
    run(apps)
