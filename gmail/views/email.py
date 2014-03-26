#coding: utf-8
from __future__ import absolute_import
import ipdb
import logging
import re
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

    def get(self, *args, **kwargs):
        self.folders = self.get_folder_list()

        if 'folder' not in self.kwargs and self.folders:
            return HttpResponseRedirect(reverse('email_list', args=(self.folders[0],)))
        return super(EmailList, self).get(*args, **kwargs)

    def get_queryset(self):
        if not self.folders:
            return []

        current_folder = self.kwargs.get('folder', None)
        if current_folder not in self.folders:
            raise Http404('No folder found')
        form = EmailQueryForm(self.folders, current_folder, self.request.GET)
        form.is_valid()  # We don't care, just clean it for us
        # The order doesn't matter, since we have user & folder indexed,
        # it will be used first
        if not form.cleaned_data.get('folder'):
            form.cleaned_data['folder'] = current_folder
        elif form.cleaned_data.get('folder') == '--':
            form.cleaned_data.pop('folder')
        return Email.find(form.cleaned_data).owned_by(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(EmailList, self).get_context_data(**kwargs)
        context['folders'] = self.folders
        context['current_folder'] = self.kwargs.get('folder', '')
        context['form'] = EmailQueryForm(self.folders, context['current_folder'])
        return context

    def get_folder_list(self):
        folders = Email.objects.owned_by(self.request.user).distinct('folder')
        # I trapped myself by setting nonexist values to None so mongoengine
        # won't save it, but now it comes back to bite me!
        return [f for f in folders if f is not None]

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
        #TODO, see http://blog.robotshell.org/2012/deal-with-http-header-encoding-for-file-download/
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
        # if Email.objects.owned_by(request.user).under(e.folder).count() == 1:
        #     request.user.update(pull__folders=e.folder)
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
        return Email.objects.owned_by(self.request.user).exec_js("""

                // Construct an adjacent list
                // For performance reason, you should only exec it using mongo 2.4 or higher
                function() { 
                    var nodes = [];
                    var links = [];
                    var email_patt = /\w+@\w+\.\w+/;
                    db[collection].find(query).forEach(function(doc) {
                        // Ensure array
                        var from = [].concat(doc.from_);
                        var to = [].concat(doc.to);

                        // Construct nodes
                        var from_id = [];
                        for(var i=0; i<from.length; ++i) {
                            var email = email_patt.exec(from[i]);
                            from_id.push(email? email[0]: from[i])
                            nodes.push({
                                'id': from_id[i],
                                'text': from[i]
                            });
                        }
                        var to_id = [];
                        for(var i=0; i<to.length; ++i) {
                            var email = email_patt.exec(to[i]);
                            to_id.push(email? email[0]: to[i])
                            nodes.push({
                                'id': to_id[i],
                                'text': to[i]
                            });
                        }
                        // Now links
                        for(var i=0; i<from_id.length; ++i) {
                            for(var j=0; j<to_id.length; ++j) {
                                links.push({
                                    'from': from_id[i],
                                    'to': to_id[j]
                                })
                            }
                        }
                    });
                    return {'nodes': nodes, 'links': links};
                }
                """)
