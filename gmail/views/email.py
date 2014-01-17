#coding: utf-8
from __future__ import absolute_import
import ipdb
import logging
from json import dumps
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.generic import ListView, View, edit
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from gmail.models import Email
from gmail.forms import EmailQueryForm
from mongoengine import GridFSProxy
from mongoengine.django.shortcuts import get_document_or_404
from bson.objectid import ObjectId

from gmail.utils import LoginRequiredMixin

logger = logging.getLogger(__name__)

class EmailList(LoginRequiredMixin, ListView):
    template_name = 'email_list.html'
    context_object_name = 'emails'
    paginate_by = 20

    def get_queryset(self):
        # The order doesn't matter, since we have user indexed,
        # it will be used first
        return Email.find(self.request.GET.dict()).owned_by(u).under(path)

    def get_context_data(self, **kwargs):
        context = super(EmailList, self).get_context_data(**kwargs)
        context['folders'] = set(self.request.user.folders)
        return context

    def post(self, request, path=None):
        # META is standard python dict
        # and content-length will be inside definitely
        if 'HTTP_X_PATH' not in request.META:
            logger.warn('Recved a email without path', extra=request.__dict__)
            return HttpResponse(status=400)
        # 2014/1/8 CONTENT_LENGTH will be an int
        # when fired by django.test.client
        length = str(request.META['CONTENT_LENGTH'])
        # Max 50M, maybe should check it in nginx
        if length.isdigit() and int(length) > 50*1024*1024:
            logger.warn('Recved a request larger than 50M', extra=request.__dict__)
            return HttpResponse(status=413)

        email = Email.from_fp(request)
        email.user = self.request.user
        email.save()

        path = request.META['HTTP_X_PATH']
        folders = self.request.user.folders
        folders.setdefault(path, []).append(email.id)
        # NOTE thread-unsafe
        self.request.user.update(set__folders=folders)
        return HttpResponse('{"ok": true, "location": "%s"}' %
                # by http host
               request.build_absolute_uri(reverse('email_detail',
                   args=(email.id,))), status=201)

class EmailDetail(LoginRequiredMixin, View):
    template_name = 'email_detail.html'

    def get(self, request, eid):
        e = get_document_or_404(Email.objects.exclude(
            'resources', 'attach_txt'), id=eid)
        if not e.has_perm(request.user, 'read_email'):
            raise Http404()
        # Fuck you django DetailView, you bind too much with model
        return render_to_response(self.template_name, {'email': e}, 
                context_instance = RequestContext(request))

class Resource(LoginRequiredMixin, View):

    def get(self, request, rid):
        # Cao ni ma
        referer = request.META.get('HTTP_REFERER')
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

class Search(LoginRequiredMixin, edit.FormView):
    template_name = 'email_search.html'
    form_class = EmailQueryForm

class Delete(LoginRequiredMixin, View):

    def get(self, request, eid):
        # NOTE, need first() to call customized delete method
        e = Email.objects(id=eid).first()
        if not e.has_perm(request.user, 'delete_email'):
            raise Http404()
        if e:
            e.delete()
        return HttpResponseRedirect(reverse('email_list'))

class TimeLine(LoginRequiredMixin, ListView):
    template_name = 'email_timeline.html'
    context_object_name = 'emails'

    def get_queryset(self):
        return Email.objects.owned_by(self.request.user)
