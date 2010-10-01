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
