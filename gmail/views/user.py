import ipdb
import logging

from django.views.generic import ListView, TemplateView, edit, View
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect

from gmail.forms import UserForm
from gmail.models import User
from gmail.utils import LoginRequiredMixin

logger = logging.getLogger(__name__)

class AddUser(LoginRequiredMixin, edit.FormView):
    template_name = 'user_add.html'
    form_class = UserForm

    def form_valid(self, form):
        User.create_user(form.cleaned_data['username'],
                form.cleaned_data['password1'], form.cleaned_data['is_superuser'])
        return super(AddUser, self).form_valid(form)

    def get_success_url(self):
        return reverse('user_detail')

class UserDetail(LoginRequiredMixin, TemplateView):
    template_name = 'user_detail.html'

class UserList(LoginRequiredMixin, ListView):
    template_name = 'user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects

class Login(edit.FormView):
    template_name = 'login.html'
    form_class = AuthenticationForm

    def form_valid(self, form):
        # NOTE form is an instance of AuthenticationForm
        login(self.request, form.get_user())
        logger.info('%s logged in', form.get_user().username, extra=self.request.__dict__)
        return super(Login, self).form_valid(form)

    def get_success_url(self):
        return reverse('email_list')

class Logout(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('index'))
