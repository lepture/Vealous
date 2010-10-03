#-*- coding: utf-8 -*-

import re
import logging

def is_mobile(request):
    ua = request.headers.get('User-Agent', 'bot')
    if re.search('ipod|mobile|opera mini|blackberry|webos|ucweb|midp', ua.lower()):
        logging.info('mobile device visited this site : ' + ua)
        return True
    return False
