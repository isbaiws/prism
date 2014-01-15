from datetime import datetime
from json import dumps
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.http.response import HttpResponse

from django.utils.formats import ISO_INPUT_FORMATS

def decode_str(s, encodings=('utf-8', 'gbk'), E=UnicodeDecodeError):
    """Try to decode a string in different ways(encodings), 
    raise a specific error(E) when decoding fails
    """
    if s is None:
        return u''
    if isinstance(s, unicode):
        return s
    # As test turns out, utf-8 is a stricter encoding than gbk
    # gbk can decode what is encoded by utf-8, versa not
    if isinstance(encodings, tuple):
        for encoding in encodings:
            try:
                return s.decode(encoding)
            except UnicodeDecodeError:
                pass
        raise E("'%s' cannot be decoded by any of %s" % (s, encodings))
    else:
        try:
            return s.decode(encodings)
        except UnicodeDecodeError:
            raise E("'%s' cannot be decoded by %s" % (s, encodings))

def parse_input_datetime(value):
    for format in ISO_INPUT_FORMATS['DATETIME_INPUT_FORMATS']:
        try:
            return datetime.strptime(value, format)
        except (ValueError, TypeError):
            continue
    return None

class LoginRequiredMixin(object):
    """ from http://stackoverflow.com/a/6455140 """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

class JsonView(View):
    def dispatch(self, request, *args, **kwargs):
        d = super(JsonView, self).dispatch(request, *args, **kwargs)
        return HttpResponse(dumps(d))
