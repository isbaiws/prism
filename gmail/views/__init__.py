from __future__ import absolute_import
from django.views.generic import TemplateView
from django.http import HttpResponse
from .email import *
from .user import *

class Index(TemplateView):
    template_name = 'index.html'

def not_implemented(req):
    return HttpResponse('NotImplemented yet')
