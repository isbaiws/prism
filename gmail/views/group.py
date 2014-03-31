import ipdb
import logging

from django.views.generic import ListView, View
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from bson.objectid import ObjectId

from gmail.forms import GroupAddForm
from gmail.models import Group, User
from .mixins import LoginRequiredMixin, AdminRequired

logger = logging.getLogger(__name__)

class GroupList(LoginRequiredMixin, AdminRequired, ListView):
    template_name = 'group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return Group.objects
        groups = []
        for g in Group.objects:
            manager_names = []
            for uid in g.managers:
                u = User.objects(id=uid).only('username').first()
                if u:
                    manager_names.append(u.username)
                else:
                    manager_names.append(uid)
            groups.append({'name': g.name, 'manager_names': manager_names})
        return groups

class GroupAdd(LoginRequiredMixin, AdminRequired, FormView):
    template_name = 'group_add.html'
    form_class = GroupAddForm

    def form_valid(self, form):
        group_name, manager = form.cleaned_data['group_name'], form.cleaned_data['manager']
        managers = [manager.id] if manager else []
        g = Group(name=group_name, managers=managers)
        g.save()
        if manager:
            manager.update(add_to_set__groups=g.id)
        logger.info('%s created a group: %s', self.request.user.username, group_name)
        return super(GroupAdd, self).form_valid(form)

    def get_success_url(self):
        return reverse('group_list')

class GroupEdit(LoginRequiredMixin, AdminRequired, FormView):
    template_name = 'group_add.html'
    form_class = GroupAddForm

    def form_valid(self, form):
        group_name, manager = form.cleaned_data['group_name'], form.cleaned_data['manager']
        managers = [manager.id] if manager else []
        g = Group(name=group_name, managers=managers)
        g.save()
        if manager:
            manager.update(add_to_set__groups=g.id)
        logger.info('%s created a group: %s', self.request.user.username, group_name)
        return super(GroupAdd, self).form_valid(form)

    def get_success_url(self):
        return reverse('group_list')

class GroupDelete(LoginRequiredMixin, AdminRequired, View):
    def get(self, request, gid):
        if ObjectId.is_valid(gid):
            Group.objects(id=gid).delete()
        return HttpResponseRedirect(reverse('group_list'))

