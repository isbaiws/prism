from django.http import HttpResponse
from django.views.generic import ListView, View
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

import mime
from exceptions import HttpErrorHandler

class EmailList(HttpErrorHandler, ListView):
    template_name = 'email_list.html'
    context_object_name = 'emails'

    def get_queryset(self):
        return mime.all()

    def post(self, req):
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
        context = {'header': e.header, 'body': e.body_html}
        # Fuck you django DetailView, you bind too much with model
        return render_to_response(self.template_name, context)

    def delete(self, request, eid):
        id = mime.remove(eid)
        return HttpResponse('{ok: true, id: %s}' % id)

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

