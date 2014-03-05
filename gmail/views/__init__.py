from __future__ import absolute_import
from django.views.generic import TemplateView
from django.http import HttpResponse
from bson import BSON

from .email import *
from .user import *
from .api import *

class Index(TemplateView):
    template_name = 'index.html'

def not_implemented(req):
    return HttpResponse('NotImplemented yet')

def debug(req):
    print (BSON.encode({'hello': 'world'}))
    return HttpResponse(BSON.encode({'hello': 'world'}))
