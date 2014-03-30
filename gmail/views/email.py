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

from .mixins import LoginRequiredMixin, JsonViewMixin, FolderMixin

logger = logging.getLogger(__name__)

class EmailList(LoginRequiredMixin, FolderMixin, ListView):
    template_name = 'email_list.html'
    context_object_name = 'emails'
    paginate_by = 20
    view_name = 'email_list'

    def get_queryset(self):
        if not self.folders:
            return []

        form = EmailQueryForm(self.folders, self.current_folder, self.request.GET)
        form.is_valid()  # We don't care, just clean it for us
        # The order doesn't matter, since we have user & folder indexed,
        # it will be used first
        if not form.cleaned_data.get('folder'):
            form.cleaned_data['folder'] = self.current_folder
        elif form.cleaned_data.get('folder') == '--':
            form.cleaned_data.pop('folder')
        return Email.find(form.cleaned_data).owned_by(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(EmailList, self).get_context_data(**kwargs)
        context['form'] = EmailQueryForm(self.folders, context['current_folder'])
        return context


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

class TimeLine(LoginRequiredMixin, FolderMixin, TemplateView):
    template_name = 'email_timeline.html'
    view_name = 'email_timeline'

    def get_context_data(self, **kwargs):
        context = super(TimeLine, self).get_context_data(**kwargs)
        context['current_folder'] = self.current_folder
        return context

class TimeLineJson(LoginRequiredMixin, FolderMixin, JsonViewMixin):
    view_name = 'email_timeline_json'

    def get(self, request, folder):
        return [{'date': e.date, 'url': reverse('email_detail', args=(e.id,)),
                'subject': e.subject} for e in 
                Email.objects.owned_by(request.user).under(folder)]

class Relation(LoginRequiredMixin, FolderMixin, TemplateView):
    template_name = 'email_relation.html'
    view_name = 'email_relation'

    def get_context_data(self, **kwargs):
        context = super(Relation, self).get_context_data(**kwargs)
        return context


class RelationJson(LoginRequiredMixin, FolderMixin, JsonViewMixin):
    view_name = 'email_relation_json'

    def get(self, request, folder):
        threshold = self.request.GET.get('threshold', 1)
        try:
            threshold = int(threshold)
        except ValueError:
            threshold = 1

        return Email.objects.owned_by(self.request.user). \
            under(folder).exec_js("""

                // Construct an adjacent list
                // For performance reason, you should only exec it using mongo 2.4 or higher

function() { 
    var node = {};
    var connection = {};
    var relation = {};
    // Email address is in the form of
    // "name <account@example.com>"
    var email_patt = /\w+@\w+\.\w+/;
    db[collection].find(query).forEach(function(doc) {
        // Ensure array
        var from = [].concat(doc.from_);
        var to = [].concat(doc.to);

        // Clean up data
        var from_id = [];
        for(var i=0; i<from.length; ++i) {
            var email = email_patt.exec(from[i]);
            from_id.push(email? email[0]: from[i]);
            node[from_id[i]] = from[i];
            connection[from_id[i]] = connection[from_id[i]] || {}
        }
        var to_id = [];
        for(var i=0; i<to.length; ++i) {
            var email = email_patt.exec(to[i]);
            to_id.push(email? email[0]: to[i]);
            node[to_id[i]] = to[i];
            connection[to_id[i]] = connection[to_id[i]] || {}
        }

        // Relations
        for(var i=0; i<from_id.length; ++i) {
            for(var j=0; j<to_id.length; ++j) {
                var f=from_id[i], t=to_id[j];
                if(connection[t][f]) {
                    connection[t][f] -= 1;
                    // Ensure key(f,t) is the same as key(t,f)
                    if(f>t){ f = [t, t=f][0]; }
                    relation[f] = relation[f] || {};
                    // I really miss defaultdict in python
                    relation[f][t] = (relation[f][t] || 0) + 1;
                } else {
                    connection[f][t] = (connection[f][t] || 0) + 1;
                }
            }
        }
    });
    var vertex=[], edge=[];
    for(var f in relation) {
        for(var t in relation[f]) {
            if(relation[f][t] >= options.threshold) {
                // TODO duplicated 
                vertex.push({
                    'id': f,
                    'text': node[f]
                });
                vertex.push({
                    'id': t,
                    'text': node[t]
                });
                edge.push({
                    'from': f,
                    'to': t,
                    'value': relation[f][t],
                    'title': relation[f][t]
                });
            }
        }
    }
    return {'nodes': vertex, 'links': edge};
}
                """, threshold=threshold)
