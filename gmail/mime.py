#coding: utf-8
import re
from itertools import ifilter
from email import message_from_file, message_from_string
from email.header import decode_header

from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import Binary
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags

from exceptions import ObjectDoesNotExist

client = MongoClient(settings.DB_HOST, settings.DB_PORT)
db = client.prism
email_db = db.email

# Match encoded-word strings in the form =?charset?q?Hello_World?=
# Some will surrend it by " or end by , or by fucking \r
ecre = re.compile(r"""=\?([^?]*?)\?([qb])\?(.*?)\?=(?=\W|$)""",
        re.VERBOSE | re.IGNORECASE | re.MULTILINE)

def flatten_header(hdr):
    """Decode strings like =?charset?q?Hello_World?=
    and make keys lower case, 
    hdr must be a email.message type"""
    vanilla_hdr = {}
    def decode_match(field):
        dec_str, charset = decode_header(field.group(0))[0]
        if charset:
            dec_str = dec_str.decode(charset, 'replace')
        return dec_str

    for k, v in hdr.items():
        vanilla_hdr[k.lower()] = ecre.sub(decode_match, v)
    
    # Ensure there is a content-type key
    # if 'content-type' not in vanilla_hdr:
    # get_content_type() will return a default one, all in lower-case
    vanilla_hdr['content-type'] = hdr.get_content_type()
    
    if hdr.get_filename():
        vanilla_hdr['filename'] = hdr.get_filename()

    if 'content-disposition' not in vanilla_hdr and hdr.get_filename():
        vanilla_hdr['content-disposition'] = hdr.get_filename()
    return vanilla_hdr

class MessageMixin(object):

    # Some resources may need idx to identify themself
    def __init__(self, header, body, id=None, idx=0, body_html='', body_txt=''):
        self.header = header
        self.body = body
        # Fetch one if not exist
        self.id = ObjectId(id)
        if type(idx) is not int:
            raise RuntimeError('%s in %s receives an invalid idx: %s' % 
                    (self.__class__.__name__, self.id, idx))
        self.idx = idx
        # if not body_html:
        #     body_html = self.to_html()
        self.body_html = body_html
        # if not body_txt:
        #     body_txt = strip_tags(self.body_html)
        self.body_txt = body_txt

    def __unicode__(self):
        return unicode(self.header.get('subject', self.id))

    def to_html(self):
        raise NotImplementedError('%s doesnot need to_html' %
                self.__class__.__name__)

    def to_dict(self):
        return {'header': self.header, 'body': self.body}
    
    @classmethod
    def from_dict(cls, d, idx=0):
        header = d.get('header')
        body = d.get('body', '')
        id = d.get('_id')
        body_html = d.get('body_html', '')
        body_txt = d.get('body_txt', '')
        return cls(header, body, id, idx, body_html=body_html, body_txt=body_txt)

    def get_resource(self, idx=0):
        if idx != 0:
            raise ObjectDoesNotExist()
        return self

    def save(self):
        d = self.to_dict()
        # modify dict here, because we need to put extra info in the outer msg
        d['_id'] = self.id
        if not self.body_html:
            self.body_html = self.to_html()
        if not self.body_txt:
            self.body_txt = strip_tags(self.body_html)
        d['body_html'] = self.body_html
        d['body_txt'] = self.body_txt
        self.id = email_db.insert(d)  # An ObjectId
        return self.id

class TextMessage(MessageMixin):

    @classmethod
    def from_msg(cls, msg, id=None, idx=0):
        id = ObjectId(id)
        # assert msg.get_content_maintype() == 'text'
        charset = msg.get_content_charset('gbk')  # gbk will be the default one
        body = msg.get_payload(decode=True).decode(charset, 'replace')
        header = flatten_header(msg)
        return cls(header, body, id, idx=idx)

    def to_html(self):
        return self.body

    def get_resource(self, idx=0):
        rsc = super(TextMessage, self).get_resource()
        rsc.header['content-type'] = '%s; charset=utf-8' % \
                rsc.header['content-type']
        return rsc

class ImageMessage(MessageMixin):
    html_tmpl = '<img border="0" hspace="0" align="baseline" src="%s" />'

    @classmethod
    def from_msg(cls, msg, id=None, idx=0):
        id = ObjectId(id)
        header = flatten_header(msg)
        body = Binary(msg.get_payload(decode=True))
        return cls(header, body, id, idx=idx)

    def to_html(self):
        if getattr(self, 'id', None) is None:
            raise RuntimeError("You havn't set my id yet")
        return self.html_tmpl % reverse('resource', args=(self.id, self.idx))

class DefaultMessage(ImageMessage):
    html_tmpl = "<a href='%s'>%s</a>"

    def to_html(self):
        if getattr(self, 'id', None) is None:
            raise RuntimeError("You havn't set my id yet")
        return self.html_tmpl % (reverse('resource', args=(self.id, self.idx)),
            self.header.get('filename', u'未命名文件'))

class MultpartMessage(MessageMixin):
    alternatives = ['text/html', 'text/richtext', 'text/plain', 'message/rfc822']

    @classmethod
    def from_msg(cls, msg, id=None, idx=0):  # 0 for add operation
        id = ObjectId(id)  # fetch one if not exist
        children = []
        for i, sub_msg in enumerate(msg.get_payload()):
            children.append(from_msg(sub_msg, id, i+idx))  # no hieracy, just flatten them

        # Each of the parts is an "alternative" version of the same information.
        if msg.get_content_subtype() == 'alternative':
            for ct in cls.alternatives:
                # There must be a content-type, just in case
                best = next(ifilter(lambda m: m.header.get \
                    ('content-type', '').startswith(ct), children), None)
                if best:
                    break
            else:
                # the last one means the richest, but maybe I donnot know
                # how to interpret, so just get the first one
                best = children[0]
            # We still need your header, but donot overwrite headers I already have
            for k, v in flatten_header(msg).items():
                if k not in best.header:
                    best.header[k] = v
            return best
        else:
            header = flatten_header(msg)
            return cls(header, children, id=id, idx=idx)
    
    @classmethod
    def from_dict(cls, d, idx=0):
        id = d['_id']
        header = d.get('header')
        children = []
        for i, child in enumerate(d.get('body', [])):
            child['_id'] = id
            children.append(from_dict(child, i+idx))
        body_html = d.get('body_html', '')
        body_txt = d.get('body_txt', '')
        return cls(header, children, id, idx=idx, 
                body_html=body_html, body_txt=body_txt)

    def to_dict(self):
        d = super(MultpartMessage, self).to_dict()
        d['body'] = [b.to_dict() for b in self.body]
        return d
    
    def to_html(self, idx=None):
        child_html = []
        for child in self.body:
            child_html.append(child.to_html())
        return ''.join(child_html)

    def get_resource(self, idx):
        if idx is None:
            raise ObjectDoesNotExist()
        idx = int(idx)
        try:
            return self.body[idx]
        except IndexError:
            raise ObjectDoesNotExist()

parser = {'text': TextMessage,
        'image': ImageMessage,
        'multipart': MultpartMessage,}

def from_fp(fp):
    msg = message_from_file(fp)
    return from_msg(msg)

def from_string(fp):
    msg = message_from_string(fp)
    return from_msg(msg)

def from_msg(msg, id=None, idx=0):
    id = ObjectId(id)  # fetch one if not exist
    maintype = msg.get_content_maintype()
    return parser.get(maintype, DefaultMessage).from_msg(msg, id, idx)

def from_id(id_str):
    msg_dict = email_db.find_one({'_id': ObjectId(id_str)})
    if not msg_dict:
        raise ObjectDoesNotExist()
    return from_dict(msg_dict)

def from_dict(d, idx=0):
    ct = d['header']['content-type']
    maintype = ct.split('/')[0]
    return parser.get(maintype, DefaultMessage).from_dict(d, idx)

def all():
    return map(from_dict, email_db.find())

