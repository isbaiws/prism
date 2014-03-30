from json import dumps, JSONEncoder
import ipdb
import datetime
from time import mktime
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http.response import HttpResponse
from django.views.generic import View
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from bson.objectid import ObjectId

from gmail.models import Email

class LoginRequiredMixin(View):
    """ from http://stackoverflow.com/a/6455140 """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

class AdminRequired(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404('Only admin can view this page, remind me to remove it in production.')
        return super(AdminRequired, self).dispatch(request, *args, **kwargs)

class MyJsonEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))
        elif isinstance(obj, ObjectId):
            return str(obj)
        return super(MyJsonEncoder, self).default(obj)

class JsonViewMixin(View):
    content_type = 'application/json'

    def dispatch(self, request, *args, **kwargs):
        d = super(JsonViewMixin, self).dispatch(request, *args, **kwargs)
        return HttpResponse(dumps(d, cls=MyJsonEncoder), content_type=self.content_type)


class FolderMixin(object):

    def dispatch(self, *args, **kwargs):
        self.folders = self.get_folder_list()

        self.current_folder = kwargs.get('folder', None)
        if self.current_folder:
            if self.current_folder not in self.folders:
                raise Http404('No folder found')
        elif self.folders:
            return HttpResponseRedirect(reverse(self.view_name, args=(self.folders[0],)))
        else:
            self.get_queryset = lambda : []
        return super(FolderMixin, self).dispatch(*args, **kwargs)

    def get_folder_list(self):
        folders = Email.objects.owned_by(self.request.user).distinct('folder')
        # I trapped myself by setting nonexist values to None so mongoengine
        # won't save it, but now it comes back to bite me!
        return [f for f in folders if f is not None]

    def get_context_data(self, **kwargs):
        context = super(FolderMixin, self).get_context_data(**kwargs)
        context['folders'] = self.folders
        context['current_folder'] = self.current_folder
        return context


