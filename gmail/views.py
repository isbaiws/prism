import re
import pdb
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView, View, TemplateView
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from models import Email
from shortcuts import get_email_or_404, get_resource_or_404

logger = logging.getLogger(__name__)

class Index(TemplateView):
    template_name = 'index.html'

class EmailList(ListView):
    template_name = 'email_list.html'
    context_object_name = 'emails'
    header_fields = {'subject', 'from', 'to'}

    def get_queryset(self):
        selector = {}
        for k, v in self.request.GET.items():
            if v and k!='page':
                if k in self.header_fields:
                    k = 'header.' + k
                #TODO pretty unsafe to use user's input directly
                selector[k] = {'$regex': '.*%s.*' % re.escape(v)}
                # Try using the python regex objects instead. Pymongo will serialize them properly
                # selector[k] = {'$regex': '.*%s.*' % re.escape(v), '$options': 'i'}
        # We have a middleware to set remote_addr
        logger.info('Selector is %s', selector, extra=self.request.__dict__)
        cursor = Email.find(**selector)

        paginator = Paginator(cursor, 20) # Show 20 contacts per page
        # pdb.set_trace()
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
        length = request.META['CONTENT_LENGTH']
        if not length:
            logger.warn('Recved a request without content-length or content-length is 0'
                    , extra=request.__dict__)
            return HttpResponse(status=411)
        # Max 50M
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
        e = get_email_or_404(eid)
        context = {'header': e.header, 'body': e.body, 'attachments': e.attachments}
        # Fuck you django DetailView, you bind too much with model
        return render_to_response(self.template_name, context)

class Resource(View):

    def get(self, request, rid):
        resource = get_resource_or_404(rid)
        hdr = resource.header
        response = HttpResponse(resource.read(), content_type=hdr['content-type'])
        if 'content-disposition' in hdr:
            response['Content-Disposition'] = hdr['content-disposition']
        return response

class Search(TemplateView):
    template_name = 'search.html'

class Delete(View):

    def get(self, request, eid):
        Email.remove(eid)
        return HttpResponseRedirect(reverse('email_list'))

