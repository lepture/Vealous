#-*- coding: utf-8 -*-

import os
from utils import is_mobile
from config import ROOT

def get_path(request , name):
    if is_mobile(request):
        path = os.path.join(ROOT, 'god','mobile' , name)
        return path
    path = os.path.join(ROOT, 'god', 'tpl', name)
    return path

def get_tpl(name):
    path = os.path.join(ROOT, 'god', 'tpl', name)
    return path
