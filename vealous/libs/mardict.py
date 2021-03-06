#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mardict - Marvour Dict Bot
Copyright (c) 2010 Hsiaoming Young

Orignally Publish at http://mardict.appspot.com
"""

__author__ = 'Hsiaoming Young<i@shiao.org>'
__version__ = '1.0'
__license__ = 'BSD LICENSE'

import re
import urllib2
from django.utils.simplejson import loads as parse_json
#from simplejson import loads as parse_json

class DictCN(object):
    def __init__(self, word='hello'):
        try: word = word.encode('utf-8')
        except UnicodeDecodeError: pass
        self._url = 'http://dict.cn/ws.php?utf8=true&q=%s' % urllib2.quote(word)

    def _get_source(self):
        url = self._url
        try:
            page = urllib2.urlopen(url)
            source = unicode(page.read(), 'utf-8')
            page.close()
        except:
            return None

        regex = r'<key>(.*?)</key>.*?<lang>(.*?)</lang>.*?<pron>(.*?)</pron>.*?<def>(.*?)</def>'
        match = re.findall(regex, source, re.U|re.S)
        if match:
            return match[0]
        return None

    def reply(self):
        info = self._get_source()
        if not info:
            return None

        key = info[0]
        lang = info[1]
        pron = info[2]
        define = info[3].replace('\n',', ')
        define = define.replace('&lt;','<').replace('&gt;','>')
        define = define.replace('&amp;','&')
        # fix pron
        regex = r'&#(\d{3});'
        match = re.findall(regex, pron, re.U)
        for num in match:
            fix = '&#%s;' % num
            pron = pron.replace(fix,unichr(int(num)))

        reply = 'from: dict.cn\n%s [%s]\n%s' % (key, pron, define)
        data = {'from': 'dictcn','word': key, 'lang': lang,
                'pron': pron, 'define': define, 'reply': reply}
        return data

class GoogleDict(object):
    base = 'http://ajax.googleapis.com/ajax/services/language/'

    def __init__(self, word='hello',lan1='en',lan2='zh-CN'):
        self._from = lan1
        self._to = lan2
        try:
            self._word = word.encode('utf-8')
        except:
            self._word = word

    def _get_source(self, url):
        try:
            page = urllib2.urlopen(url)
            source = parse_json(page.read())
            page.close()
        except:
            return None
        return source['responseData']

    def detect(self):
        url = self.base + ('detect?v=1.0&q=%s' % urllib2.quote(self._word))
        source = self._get_source(url)
        if source:
            return source['language']
        return 'en'

    def reply(self):
        lan1 = self._from
        lan2 = self._to
        word = urllib2.quote(self._word)
        url = self.base + ('translate?v=1.0&langpair=%s|%s&q=%s' % \
                           (lan1,lan2,word))
        source = self._get_source(url)
        if not source:
            return None
        try:
            key = unicode(self._word, 'utf-8')
        except:
            key = self._word
        define = source['translatedText']
        pron = 'none'
        reply = 'from: google(%s->%s)\n%s\n%s' % (lan1, lan2, key, define)
        data = {'from':'google','word':key, 'pron':pron,
                'define': define, 'reply': reply }
        return data


class QQDict(object):
    def __init__(self, word='hello'):
        try: word = word.encode('utf-8')
        except UnicodeDecodeError: pass
        self._url = 'http://dict.qq.com/dict?q=%s' % urllib2.quote(word)

    def _get_source(self):
        url = self._url
        try:
            page = urllib2.urlopen(url)
            source = parse_json(page.read())
            page.close()
        except:
            return None
        return source

    def _fix_phos(self, phos):
        pron = []
        for pho in phos:
            match = re.findall(r'&#(\d{3});', pho, re.U)
            for num in match:
                fix = '&#%s;' % num
                pho = pho.replace(fix, unichr(int(num)))
            pron.append(pho)
        return ','.join(pron)

    def _fix_des(self, des):
        define = []
        for de in des:
            define.append('%s %s' % (de['p'], de['d']))
        return ', '.join(define)

    def reply(self):
        info = self._get_source()
        if not info:
            return None
        if not info.has_key('lang'):
            return None
        lang = info['lang']
        if not info.has_key('local'):
            return None
        if not info['local']:
            return None
        local = info['local']
        key = local[0]['word']
        pron = []
        define = []
        for data in local:
            pron.append(self._fix_phos(data['pho']))
            if 'ch' == lang:
                define.append(','.join(data['des']))
            else:
                define.append(self._fix_des(data['des']))
        pron = ','.join(pron)
        define = ';'.join(define)
        reply = 'from: dict.qq.com\n%s [%s]\n%s' % (key, pron, define)
        data = {'from': 'QQdict', 'word': key, 'lang': lang,
                'pron': pron, 'define':define, 'reply': reply}
        return data

if "__main__" == __name__:
    q = raw_input('enter: ')
    d = QQDict(q)
    print d.reply()['reply']
