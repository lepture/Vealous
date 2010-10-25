#-*- coding: utf-8 -*-

from google.appengine.ext.webapp import template
import datetime
import re
try:
    import hashlib
    md5 = hashlib.md5
except ImportError:
    import md5
    md5 = md5.new

from config import TIMEZONE

register = template.create_template_register()

@register.filter
def prettytime(value):
    if isinstance(value, datetime.datetime):
        value += datetime.timedelta(hours=TIMEZONE) # fix 
        return value.strftime("%H:%M %b %d, %Y")
    return value

@register.filter
def feedtime(value):
    if isinstance(value, datetime.datetime):
        return value.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return value

@register.filter
def split(value,arg,num=0):
    num = int(num)
    return value.split(arg)[num]

@register.filter
def gravatar(value, arg='normal'):
    if 'large' == arg:
        size = 73
    elif 'mini' == arg:
        size = 24
    else:
        size = 48
    url = 'http://www.gravatar.com/avatar/'
    url += md5(value).hexdigest() + '?s=' + str(size)
    return url

@register.filter
def gtitle(value):
    value = value.split('|')[0]
    return value

@register.filter
def more(value):
    value = re.sub(r'\r\n|\r|\n', '\n', value)
    paras = re.split('\n', value)
    if not paras:
        return value
    content = '\n'.join(paras[:2])
    return content

@register.filter
def embed(value):
    #gist
    value = re.sub(r'(http://gist.github.com/[\d]+)',r'<small><a rel="nofollow" href="\1">\1</a></small><script src="\1.js"></script>', value) 
    #youku
    value = re.sub(r'http://v.youku.com/v_show/id_([a-zA-Z0-9\=]+).html', r'<small><a rel="nofollow" href="http://v.youku.com/v_show/id_\1.html">Youku Source</a></small><br /><embed src="http://player.youku.com/player.php/sid/\1/v.swf" quality="high" width="480" height="400" allowScriptAccess="sameDomain" type="application/x-shockwave-flash" />', value)
    #tudou
    value = re.sub(r'http://www.tudou.com/programs/view/([a-zA-z0-9\-\=]+)/',r'<small><a rel="nofollow" href="http://www.tudou.com/programs/view/\1/">Tudou Source</a></small><br /><embed src="http://www.tudou.com/v/\1/v.swf" width="480" height="400" allowScriptAccess="sameDomain" wmode="opaque" type="application/x-shockwave-flash" />', value)
    return value

@register.filter
def embed_feed(value):
    #gist
    value = re.sub(r'(http://gist.github.com/[\d]+)',r'snippet code at <a rel="nofollow" href="\1">\1</a>', value) 
    #youku
    value = re.sub(r'http://v.youku.com/v_show/id_([a-zA-Z0-9\=]+).html', r'Feed subscribers who cannot see the video click at: <small><a rel="nofollow" href="http://v.youku.com/v_show/id_\1.html">Youku Source</a></small><br /><embed src="http://player.youku.com/player.php/sid/\1/v.swf" quality="high" width="480" height="400" allowScriptAccess="sameDomain" type="application/x-shockwave-flash" />', value)
    #tudou
    value = re.sub(r'http://www.tudou.com/programs/view/([a-zA-z0-9\-\=]+)/',r'Feed subscribers who cannot see the video click at: <small><a rel="nofollow" href="http://www.tudou.com/programs/view/\1/">Tudou Source</a></small><br /><embed src="http://www.tudou.com/v/\1/v.swf" width="480" height="400" allowScriptAccess="sameDomain" wmode="opaque" type="application/x-shockwave-flash" />', value)
    return value

@register.filter
def star(num):
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

@register.filter
def at(value):
    value = re.sub(r'@([a-zA-Z0-9\_]+)',r'@<a href="/utils/twitter/\1">\1</a>', value) 
    return value
