# coding: utf-8
from django import forms

class EmailQueryForm(forms.Form):
    q = forms.CharField(required=False, label="查询")

    from_ = forms.BooleanField(required=False, label='发件人')
    to = forms.BooleanField(required=False, label='收件人')
    subject = forms.BooleanField(required=False, label='主题')
    body_txt = forms.BooleanField(required=False, label='正文')
    attach_filename = forms.BooleanField(required=False, label='附件名')
    attach_txt = forms.BooleanField(required=False, label='附件内容')
    ip = forms.BooleanField(required=False, label='IP地址')
    bcc = forms.BooleanField(required=False, label='密送')
    cc = forms.BooleanField(required=False, label='抄送')

    start = forms.DateTimeField(required=False, label='从')
    end = forms.DateTimeField(required=False, label='至')

