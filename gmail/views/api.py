from __future__ import absolute_import
from django.views.generic.edit import FormView
import logging
import ipdb
from django.http import Http404

from .mixins import JsonViewMixin
from gmail.forms import UploadForm
from gmail.models import Email

logger = logging.getLogger(__name__)

class ApiUpload(JsonViewMixin, FormView):
    form_class = UploadForm

    def get(self, request):
        # Do something before formview kicks in
        raise Http404()

    def form_valid(self, form):
        ack_ids = []
        for ele in form.cleaned_data['data']:
            # try: except, what if only one email is invalid
            email = Email.from_string(ele['content'])
            email.owner = self.request.user
            email.path = ele['folder']
            email.save()
            ack_ids.append(ele['id'])

        return {'action': 111,
                'error': form.error_id,
                'errormsg': form.errors,
                'ack': ack_ids,}

    def form_invalid(self, form):
        return {'action': 111,
                'error': form.error_id,
                'errormsg': form.errors,
                'ack': [],}

