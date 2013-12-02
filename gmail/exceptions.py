from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

class HttpErrorHandler(object):

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(HttpErrorHandler, self).dispatch(request, *args, **kwargs)
        except ObjectDoesNotExist:
            raise Http404()

