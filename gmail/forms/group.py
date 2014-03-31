# coding: utf-8
from django import forms
from bson.objectid import ObjectId

from gmail.models import User, Group

class GroupAddForm(forms.Form):
    group_name = forms.CharField()
    manager = forms.ChoiceField(choices=[('--', '--')]+[(u.id, u.username) for u in User.objects
        if not u.is_superuser], required=False)

    def __init__(self, *args, **kwargs):
        super(GroupAddForm, self).__init__(*args, **kwargs)
        # For dynamic choices
        self.fields['manager'] = forms.ChoiceField(choices=[('--', '--')]+[(u.id, u.username)\
                for u in User.objects if not u.is_superuser], required=False)

    def clean_group_name(self):
        if Group.objects(name=self.cleaned_data['group_name']).first():
            raise forms.ValidationError("Group with name %s already exist" %
                    self.cleaned_data['group_name'])
        return self.cleaned_data['group_name']

    def clean_manager(self):
        if self.cleaned_data['manager'] == '--':
            return None
        if not ObjectId.is_valid(self.cleaned_data['manager']):
            raise forms.ValidationError("User %s is not found" % self.cleaned_data['manager'])
        m = User.objects(id=self.cleaned_data['manager']).first()
        if not m:
            raise forms.ValidationError("User %s is not found" % self.cleaned_data['manager'])
        return m
