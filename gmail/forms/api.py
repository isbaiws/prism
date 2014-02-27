# coding: utf-8
from __future__ import absolute_import
from collections import defaultdict
import ipdb
from uuid import UUID
from hashlib import md5

from django import forms
from django.conf import settings
from bson import BSON, InvalidBSON
from gmail.models import User

"""
Request, bson encoded
{
	devid:{guid},	//设备标识
	ver:{int},		//协议版本号
    source:{int},   //来源
	action:101,
	nonce:{int},
	sig:{string},	//根据上面五个字段生成的签名
    uid:{string}
}
Response, json encoded
{
	action:101,			//响应对应的请求类型
    error:{int},			//错误类型，0为成功
	errormsg:{string},		//可选，出错信息，调试用
}
"""

source_table = {
        11: 'iOS',
        12: 'Android',
        13: 'Windows Phone',
        21: 'Windos',
        22: 'Mac OSX',
        31: 'Email Account',
    }

action_table = {
        101: 'init',
        111: 'upload',
        121: 'comm',
        122: 'config',
        123: 'download',
        124: 'install',
    }

class ApiValidationError(Exception):
    def __init__(self, error_id, desc):
        self.error_id = error_id
        self.desc = desc
        super(ApiValidationError, self).__init__(error_id, desc)

class ApiForm(forms.Form):
    """Imitate django's standard form, except
    its data is bson encoded"""
    error_id = 0
    errors = ''

    def full_clean(self):
        try:
            # Will raise InvalidBSON
            # self.cleaned_data = BSON(self.data).decode(as_class=lambda : defaultdict(str))
            self.cleaned_data = BSON(self.data).decode()
            ipdb.set_trace()

            self.clean_devid()
            self.clean_ver()
            self.clean_source()
            self.clean_action()
            self.clean_nonce()

            if self.cleaned_data['sig'] != self.sign():
                raise ApiValidationError(1002,  'Invalid signature')

            self.clean_shit()

        except InvalidBSON as e:
            self.error_id = 3002
            self.errors = 'InvalidBSON: %s' % e
        except ApiValidationError as e:
            self.error_id = e.error_id
            self.errors = e.desc
        #TODO, define one
        except KeyError as e:  # Key missing
            self.error_id = 3002
            self.errors = 'Key missing %s' % e

    def clean_devid(self):
        if not isinstance(self.cleaned_data['devid'], UUID):
            try:
               self.cleaned_data['devid'] = UUID(str(self.cleaned_data['devid']))
            except ValueError as e:  # invalid_devid
                raise ApiValidationError(1001, 'Invalid device id: %s' % e)

    def clean_action(self):
        if self.cleaned_data['action'] not in action_table:
            raise ApiValidationError(2000, 'Action id is unknown')

    def clean_ver(self):
        if not isinstance(self.cleaned_data['ver'], int):
            raise ApiValidationError(3002, 'Ver should be an integer')

    def clean_source(self):
        if not isinstance(self.cleaned_data['source'], int):
            raise ApiValidationError(3002, 'Source should be an integer')
        #TODO define one
        if self.cleaned_data['source'] not in source_table:
            raise ApiValidationError(3002, 'Source id is unknown')
        #TODO Should I store string in db?
        self.cleaned_data['source'] = source_table[self.cleaned_data['source']]

    def clean_nonce(self):
        if not isinstance(self.cleaned_data['nonce'], int):
            raise ApiValidationError(3002, 'Nonce should be an integer')

    def sign(self):
        d = self.cleaned_data
        return md5('%s'*6 % (
            d['devid'], d['ver'], d['source'], d['action'], d['nonce'], 
            settings.API_SECRET_KEY)).hexdigest().lower()

    def is_valid(self):
        self.full_clean()
        return self.is_bound and not bool(self.errors)

class InitForm(ApiForm):

    def clean_shit(self):
        #TODO what if doesn't match
        if self.cleaned_data['action'] != 101: # register a new device
            raise ApiValidationError(2000, 'Invalid action id')
        if User.objects.find_one(self.cleaned_data['devid']):
            raise ApiValidationError(1000, 'Duplicated device id')

class UploadForm(ApiForm):

    def clean_shit(self):
        if self.cleaned_data['action'] != 111:
            raise ApiValidationError(2000, 'Invalid action id')
        self.clean_upload_data()

    def clean_upload_data(self):
        if not isinstance(self.cleaned_data['data'], (list, tuple)):
            raise ApiValidationError(3002, 'Uploaded data should be an array')
        for ele in self.cleaned_data['data']:
            # Try triger keyerror
            ele['id'], ele['typeid'], ele['data']
            ele['data']['folder'], ele['data']['content']
            # if not isinstance(ele['id'], int):
            #     raise ApiValidationError(3002, 'Id should be an integer')
            #TODO, correct docs
            if not isinstance(ele['typeid'], int):
                raise ApiValidationError(3002, 'Typeid should be an integer')

