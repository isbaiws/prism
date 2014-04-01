# coding: utf-8
from django import forms
from bson.objectid import ObjectId
from django.utils.safestring import mark_safe

from gmail.models import User, Group

class CheckboxSelectMultipleP(forms.CheckboxSelectMultiple):
    def render(self, *args, **kwargs): 
        output = super(CheckboxSelectMultipleP, self).render(*args,**kwargs) 
        return mark_safe(output.replace(u'<ul>', u'').replace(u'</ul>', u'').replace(u'<li>', u'<p>').replace(u'</li>', u'</p>'))

class GroupAddForm(forms.Form):
    group_name = forms.CharField()
    manager = forms.MultipleChoiceField(choices=[(u.id, u.username)
        for u in User.objects(is_superuser=False)], required=False,
        widget=CheckboxSelectMultipleP)

    def __init__(self, *args, **kwargs):
        super(GroupAddForm, self).__init__(*args, **kwargs)
        # For dynamic choices
        self.fields['manager'] = forms.MultipleChoiceField(choices=[(u.id, u.username)
            for u in User.objects(is_superuser=False)], required=False,
            widget=CheckboxSelectMultipleP)

    def clean_group_name(self):
        if Group.objects(name=self.cleaned_data['group_name']).first():
            raise forms.ValidationError("Group with name %s already exist" %
                    self.cleaned_data['group_name'])
        return self.cleaned_data['group_name']

    def clean_manager(self):
        for uid in self.cleaned_data['manager']:
            if not User.get_by_id(uid):
                raise forms.ValidationError("User %s is not found" % uid)
        return map(ObjectId, self.cleaned_data['manager'])

class GroupEditForm(forms.Form):
    groupname = forms.CharField(label="组名", required=False)
    managers = forms.MultipleChoiceField(required=False, widget=CheckboxSelectMultipleP)

    def __init__(self, group, *args, **kwargs):
        self.group = group
        super(GroupEditForm, self).__init__(*args, **kwargs)
        self.fields['managers'] = forms.MultipleChoiceField(label='组长', choices=[(u.id, u.username)
            for u in User.objects if not u.is_superuser], required=False, widget=CheckboxSelectMultipleP)

    def clean_managers(self):
        for uid in self.cleaned_data.get('managers', []):
            if not User.get_by_id(uid):
                raise forms.ValidationError("User %s is not found" % uid)
        return map(ObjectId, self.cleaned_data['managers'])

    def save(self, commit=True):
        self.group.set_managers(self.cleaned_data['managers'])
        # if commit:
        #     self.user.save()

