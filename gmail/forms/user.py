# coding: utf-8
from django import forms
from bson.objectid import ObjectId

from gmail.models import User, Group

class UserAddForm(forms.Form):
    username = forms.CharField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    is_superuser = forms.BooleanField(initial=False, required=False)
    group = forms.ChoiceField(choices=[('--', '--')]+[(g.id, g.name)
        for g in Group.objects], required=False)

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        # For dynamic choices
        self.fields['group'] = forms.ChoiceField(choices=[('--', '--')]+[(g.id, g.name)
            for g in Group.objects], required=False)

    def clean_username(self):
        if User.exist(username=self.cleaned_data['username']):
            raise forms.ValidationError("Username already exists")
        return self.cleaned_data['username']

    def clean_password2(self):
        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError('Your passwords do not match')
        return self.cleaned_data['password1']

    def clean_group(self):
        if self.cleaned_data['group'] == '--':
            return None
        if not ObjectId.is_valid(self.cleaned_data['group']):
            raise forms.ValidationError("Group %s is not found" % self.cleaned_data['group'])
        if not User.objects(id=self.cleaned_data['group']).first():
            raise forms.ValidationError("group %s is not found" % self.cleaned_data['group'])
        return ObjectId(self.cleaned_data['group'])

class PasswordResetForm(forms.Form):
    old_password = forms.CharField(label="当前密码", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="新密码", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="再次输入新密码",widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PasswordResetForm, self).__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise forms.ValidationError('password_incorrect')
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user
