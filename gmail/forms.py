# coding: utf-8
from django import forms
from gmail.models import User

class UserForm(forms.Form):
    username = forms.CharField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    is_superuser = forms.BooleanField(initial=False, required=False)

    def clean_username(self):
        if User.exist(username=self.cleaned_data['username']):
            raise forms.ValidationError("Username already exists")
        return self.cleaned_data['username']

    def clean_password2(self):
        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError('Your passwords do not match')
        return self.cleaned_data['password1']

class EmailQueryForm(forms.Form):
    from__1 = forms.CharField(required=False, label='发件人')
    to_1 = forms.CharField(required=False, label='收件人')
    subject_1 = forms.CharField(required=False, label='主题')
    body_txt_1 = forms.CharField(required=False, label='内容')
    attach_txt_1 = forms.CharField(required=False, label='附件')
    ip_1 = forms.IPAddressField(required=False, label='IP地址')
    start_1 = forms.DateTimeField(required=False, label='从')
    end_1 = forms.DateTimeField(required=False, label='至')
