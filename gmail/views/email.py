#coding: utf-8
from __future__ import absolute_import
import ipdb
import logging
from itertools import product
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.generic import ListView, DetailView, View, edit, TemplateView
from django.core.urlresolvers import reverse

from gmail.models import Email
from gmail.forms import EmailQueryForm
from mongoengine import GridFSProxy
from mongoengine.django.shortcuts import get_document_or_404
from bson.objectid import ObjectId

from .mixins import LoginRequiredMixin, JsonViewMixin

logger = logging.getLogger(__name__)

class EmailList(LoginRequiredMixin, ListView):
    template_name = 'email_list.html'
    context_object_name = 'emails'
    paginate_by = 20

    def get_queryset(self):
        u = self.request.user
        path = self.kwargs.get('path', None)
        if path and path not in u.folders:
            raise Http404('No path found')
        if not path:
            path = u.folders[0] if len(u.folders)>1 else None
        self.path = path
        # The order doesn't matter, since we have user & path indexed,
        # it will be used first
        return Email.find(self.request.GET.dict()).owned_by(u).under(path)

    def get_context_data(self, **kwargs):
        context = super(EmailList, self).get_context_data(**kwargs)
        context['folders'] = set(self.request.user.folders)
        context['current_path'] = self.path
        return context

    def post(self, request, path=None):
        # META is standard python dict
        # and content-length will be inside definitely
        if path is None:
            logger.warn('Recved a email without path', extra=request.__dict__)
            return HttpResponse(status=400)
        # 2014/1/8 CONTENT_LENGTH will be an int
        # when fired by django.test.client
        length = str(request.META['CONTENT_LENGTH'])
        # Max 50M, maybe should check it in nginx
        if length.isdigit() and int(length) > 50*1024*1024:
            logger.warn('Recved a request larger than 50M', extra=request.__dict__)
            return HttpResponse(status=413)

        email = Email.from_string(request.body)
        email.owner = request.user
        email.path = path
        email.save()
        request.user.update(add_to_set__folders=path) 
        # If you wanna use user later, reload it
        # request.user.reload()

        # by http host
        location = request.build_absolute_uri(reverse('email_detail',
                   args=(email.id,)))
        resp = HttpResponse('{"ok": true, "location": "%s"}' % location, status=201)
        resp['Location'] = location
        return resp

class EmailDetail(LoginRequiredMixin, DetailView):
    template_name = 'email_detail.html'
    context_object_name = 'email'

    def get_object(self):
        e = get_document_or_404(Email.objects.exclude(
            'resources', 'attach_txt'), id=self.kwargs['eid'])
        if not e.has_perm(self.request.user, 'read_email'):
            raise Http404()
        return e

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
        if not e:
            # TODO, test case to ensure it won't happen again
            raise Http404('Email not found')
        if not e.has_perm(request.user, 'delete_email'):
            raise Http404('Email not found')
        # Why need this folder if there is no email in it?
        if Email.objects.owned_by(request.user).under(e.path).count() == 1:
            request.user.update(pull__folders=e.path)
        e.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER')
                or reverse('email_list'))

class TimeLine(LoginRequiredMixin, TemplateView):
    template_name = 'email_timeline.html'

class TimeLineJson(LoginRequiredMixin, JsonViewMixin):

    def get(self, request):
        return [{'date': e.date, 'url': reverse('email_detail', args=(e.id,)),
                'subject': e.subject} for e in Email.objects.owned_by(request.user)]

class Relation(LoginRequiredMixin, TemplateView):
    template_name = 'email_relation.html'

class RelationJson(LoginRequiredMixin, JsonViewMixin):

    def get(self, request):
        emails = Email.objects.owned_by(self.request.user)
        nodes = []
        links = []
        for e in emails:
            from_= e.from_ if isinstance(e.from_, list) else [e.from_]
            to = e.to if isinstance(e.to, list) else [e.to]
            nodes.extend([{'id': f, 'text': f} for f in from_])
            nodes.extend([{'id': t, 'text': t} for t in to])
            links.extend([{'from': f, 'to': t} for f in from_ for t in to])
        return {'nodes': nodes, 'links': links}

