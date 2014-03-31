import ipdb
import logging

from django.views.generic import ListView, TemplateView, View
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect, Http404

from gmail.forms import UserAddForm, PasswordResetForm, UserEditForm
from gmail.models import User
from .mixins import LoginRequiredMixin, AdminRequired

logger = logging.getLogger(__name__)

class EditingUser(object):
    def dispatch(self, request, *args, **kwargs):
        if not self.kwargs.get('uid'):
            self.editing_user = request.user
        else:
            u = User.get_by_id(self.kwargs.get('uid'))
            if not u:
                raise Http404('No user found')
            if not request.user.is_superuser and u.id != request.user.id:
                raise Http404('How dare you!')
            self.editing_user = u
        return super(EditingUser, self).dispatch(request, *args, **kwargs)

class AddUser(LoginRequiredMixin, AdminRequired, FormView):
    template_name = 'user_add.html'
    form_class = UserAddForm

    def form_valid(self, form):
        d = form.cleaned_data
        groups = [d['group']] if d['group'] else []
        User.create_user(d['username'], d['password1'], d['is_superuser'], groups)
        logger.info('%s created a %suser: %s', self.request.user.username, 
                ['', 'super '][form.cleaned_data['is_superuser']], form.cleaned_data['username'],
                extra=self.request.__dict__)
        return super(AddUser, self).form_valid(form)

    def get_success_url(self):
        referer = self.request.META.get('HTTP_REFERER') or reverse('user_list')
        return referer

class UserDetail(LoginRequiredMixin, TemplateView):
    template_name = 'user_detail.html'

class UserEdit(LoginRequiredMixin, EditingUser, FormView):
    template_name = 'user_edit.html'
    form_class = UserEditForm

    def get_initial(self):
        return {
            'username': self.editing_user.username,
            'is_superuser': self.editing_user.is_superuser,
            # 'group': self.editing_user.groups,
        }

    def get_form_kwargs(self):
        kwargs = super(UserEdit, self).get_form_kwargs()
        kwargs['user'] = self.editing_user
        return kwargs

    def get_success_url(self):
        return reverse('user_list')

class UserDelete(LoginRequiredMixin, EditingUser, AdminRequired, View):
    def get(self, *args, **kwargs):
        self.editing_user.delete()
        return HttpResponseRedirect(reverse('user_list'))

class PasswordEdit(LoginRequiredMixin, EditingUser, FormView):
    template_name = 'user_passwd_edit.html'
    form_class = PasswordResetForm

    def form_valid(self, form):
        form.save()
        return super(PasswordEdit, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(PasswordEdit, self).get_form_kwargs()
        self.editing_user = User.get_by_id(self.kwargs.get('uid')) or self.request.user
        kwargs['user'] = self.editing_user
        return kwargs

    def get_success_url(self):
        return reverse('user_edit', args=(self.editing_user.id,))


class UserList(LoginRequiredMixin, AdminRequired, ListView):
    template_name = 'user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects

class Login(FormView):
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
        return HttpResponseRedirect(reverse('login'))
