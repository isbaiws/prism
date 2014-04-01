import ipdb
import logging

from django.views.generic import ListView, View
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404

from gmail.forms import GroupAddForm, GroupEditForm
from gmail.models import Group, User
from .mixins import LoginRequiredMixin, AdminRequired

logger = logging.getLogger(__name__)

class GroupList(LoginRequiredMixin, AdminRequired, ListView):
    template_name = 'group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return Group.objects

class GroupAdd(LoginRequiredMixin, AdminRequired, FormView):
    template_name = 'group_add.html'
    form_class = GroupAddForm

    def form_valid(self, form):
        group_name, managers = form.cleaned_data['group_name'], form.cleaned_data['manager']
        g = Group(name=group_name, managers=managers)
        g.save()
        for m in managers:  # A team leader should belong to the team also
            User.objects(id=m).update(add_to_set__groups=g.id)
        logger.info('%s created a group: %s', self.request.user.username, group_name)
        return super(GroupAdd, self).form_valid(form)

    def get_success_url(self):
        return reverse('group_list')

class GroupEdit(LoginRequiredMixin, AdminRequired, FormView):
    template_name = 'group_edit.html'
    form_class = GroupEditForm

    def dispatch(self, *args, **kwargs):
        group = Group.get_by_id(self.kwargs.get('gid'))
        if not group:
            raise Http404('No group found')
        self.group = group
        return super(GroupEdit, self).dispatch(*args, **kwargs)

    def get_initial(self):
        return {
            'groupname': self.group.name,
            # MultipleChoiceField takes a list of IDs not choices
            'managers': [u.id for u in self.group.managers],
        }

    def get_form_kwargs(self):
        kwargs = super(GroupEdit, self).get_form_kwargs()
        kwargs['group'] = self.group
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(GroupEdit, self).form_valid(form)
    
    def get_success_url(self):
        return reverse('group_list')

class GroupDelete(LoginRequiredMixin, AdminRequired, View):
    def get(self, request, gid):
        g = Group.get_by_id(gid)
        if g:
            g.delete()
        return HttpResponseRedirect(reverse('group_list'))

