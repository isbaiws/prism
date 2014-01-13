#coding: utf-8
from __future__ import absolute_import
import re
import ipdb
import logging
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.generic import ListView, View, edit
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from gmail.models import Email
from gmail.forms import EmailQueryForm
from mongoengine import GridFSProxy
from mongoengine.django.shortcuts import get_document_or_404
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

class EmailList(ListView):
    template_name = 'email_list.html'
    context_object_name = 'emails'
    header_fields = {'subject', 'from', 'to'}

    def get_queryset(self):
        cursor = Email.find(dict(self.request.GET.iterlists()))

        paginator = Paginator(cursor, 20) # Show 20 contacts per page
        page = self.request.GET.get('page')
        try:
            emails = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            emails = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            emails = paginator.page(paginator.num_pages)
        return emails

    def post(self, request):
        # META is standard python dict
        # and content-length will be inside definitely
        # 2014/1/8 CONTENT_LENGTH will be an int
        # when fired by django.test.client
        length = str(request.META['CONTENT_LENGTH'])
        # Max 50M, maybe should check it in nginx
        if length.isdigit() and int(length) > 50*1024*1024:
            logger.warn('Recved a request larger than 50M', extra=request.__dict__)
            return HttpResponse(status=413)
        if not self.is_authenticated(request):
            logger.warn('Unauthorized request', extra=request.__dict__)
            return HttpResponse(status=403)

        email = Email.from_fp(request)
        email.save()
        return HttpResponse('{ok: true, location: %s}' %
                # by http host
               request.build_absolute_uri(reverse('email_detail',
                   args=(email.id,))), status=201)

    def is_authenticated(self, request):
        return True

class EmailDetail(View):
    template_name = 'email_detail.html'

    def get(self, request, eid):
        e = get_document_or_404(Email.objects.exclude(
            'resources', 'attach_txt'), id=eid)
        # Fuck you django DetailView, you bind too much with model
        return render_to_response(self.template_name, {'email': e})

class Resource(View):

    def get(self, request, rid):
        resource = self.get_resource_or_404(rid)
        response = HttpResponse(resource.read())
        for hdr in ('content_type', 'content_disposition',):
            if hasattr(resource, hdr):
                response[hdr.replace('_', '-').title()] = getattr(resource, hdr)
        return response

    def get_resource_or_404(self, id_str):
        if not ObjectId.is_valid(id_str):
            raise Http404()
        resc = GridFSProxy().get(ObjectId(id_str))
        if not resc:
            raise Http404()
        return resc

class Search(edit.FormView):
    template_name = 'search.html'
    form_class = EmailQueryForm

class Delete(View):

    def get(self, request, eid):
        # NOTE, need first() to call customized delete method
        e = Email.objects(id=eid).first()
        if e:
            e.delete()
        return HttpResponseRedirect(reverse('email_list'))

