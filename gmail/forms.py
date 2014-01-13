# coding: utf-8
from django import forms

class UserForm(forms.Form):
    username = forms.CharField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_password2(self):
        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError('Your passwords do not match')
        return self.cleaned_data['password1']

class EmailQueryForm(forms.Form):
    from_ = forms.CharField(required=False, label='发件人')
    to = forms.CharField(required=False, label='收件人')
    subject = forms.CharField(required=False, label='主题')
    body_txt = forms.CharField(required=False, )
    attach_txt = forms.CharField(required=False, )
    ip = forms.IPAddressField(required=False, )
    start = forms.DateTimeField(required=False, )
    end = forms.DateTimeField(required=False, )
