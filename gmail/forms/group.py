# coding: utf-8
from django import forms
from bson.objectid import ObjectId

from gmail.models import User, Group

class GroupAddForm(forms.Form):
    group_name = forms.CharField()
    manager = forms.MultipleChoiceField(choices=[(u.id, u.username)
        for u in User.objects(is_superuser=False)], required=False,
        widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super(GroupAddForm, self).__init__(*args, **kwargs)
        # For dynamic choices
        self.fields['manager'] = forms.MultipleChoiceField(choices=[(u.id, u.username)
            for u in User.objects(is_superuser=False)], required=False,
            widget=forms.CheckboxSelectMultiple)

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
