from django.http import HttpResponse, Http404
from django.views.generic import ListView, View
from django.shortcuts import render_to_response

from models import Email

class EmailList(ListView):
    template_name = 'email_list.html'
    context_object_name = 'emails'

    def get_queryset(self):
        return Email.all()

    def post(self, req):
        email = Email.from_fp(req)
        email.save()
        return HttpResponse('{ok: true, id: %s}' % email.id, status=201)

class EmailDetail(View):
    template_name = 'email_detail.html'

    def get(self, request, eid):
        e = Email.from_id(eid)
        context = {'header': e.header, 'body': e.body_html}
        # Fuck you django DetailView, you bind too much with model
        return render_to_response(self.template_name, context)

    def delete(self, request, eid):
        id = Email.remove(eid)
        return HttpResponse('{ok: true, id: %s}' % id)

class Resource(View):

    def get(self, request, eid, idx):
        idx = int(idx)  # uninteger won't come here, hehe
        e = Email.from_id(eid)
        try:
            res = e.body[idx]
        except IndexError:
            raise Http404()
        return HttpResponse(res['content'], content_type=res['content-type'])

