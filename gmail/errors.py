from email.errors import MessageParseError
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseBadRequest

class HttpErrorHandler(object):

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(HttpErrorHandler, self).dispatch(request, *args, **kwargs)
        except MessageParseError as e:
            resp_dict = {'status':'ERROR', 'message': str(e)}
            return HttpResponseBadRequest(str(resp_dict))
        except ObjectDoesNotExist:
            raise Http404()

