import re
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView, View, TemplateView
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

import mime
from exceptions import HttpErrorHandler, MessageParseError

class Index(TemplateView):
    template_name = 'index.html'

class EmailList(HttpErrorHandler, ListView):
    template_name = 'email_list.html'
    context_object_name = 'emails'
    header_fields = {'subject', 'from', 'to'}

    def get_queryset(self):
        selector = {}
        for k, v in self.request.GET.items():
            if v:
                if k in self.header_fields:
                    k = 'header.' + k
                #TODO pretty unsafe to use user's input directly
                selector[k] = {'$regex': '.*%s.*' % re.escape(v)}
        return mime.find(**selector)

    def post(self, req):
        if not req.META['CONTENT_LENGTH']:
            raise MessageParseError('you cannot post an empty body')
        email = mime.from_fp(req)
        email.save()
        return HttpResponse('{ok: true, location: %s}' %
                # by http host
               req.build_absolute_uri(reverse('email_detail',
                   args=(email.id,))), status=201)

class EmailDetail(HttpErrorHandler, View):
    template_name = 'email_detail.html'

    def get(self, request, eid):
        e = mime.from_id(eid)
        context = {'header': e.header, 'body': e.body_html, 'attachment': e.attachment}
        # Fuck you django DetailView, you bind too much with model
        return render_to_response(self.template_name, context)

class Resource(HttpErrorHandler, View):

    def get(self, request, eid, idx=0):
        # idx can only have two possible values
        # an integer(in string) or None

        idx = int(idx)  # uninteger won't come here, hehe
        e = mime.from_id(eid)
        resource = e.get_resource(idx)
        hdr = resource.header
        response = HttpResponse(resource.body, content_type=hdr['content-type'])
        if 'content-disposition' in hdr:
            response['Content-Disposition'] = hdr['content-disposition']
        return response

class Search(HttpErrorHandler, TemplateView):
    template_name = 'search.html'

class Delete(HttpErrorHandler, View):

    def get(self, request, eid):
        mime.remove(eid)
        return HttpResponseRedirect(reverse('email_list'))

