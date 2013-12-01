import re
from itertools import ifilter
from email import message_from_file
from email.header import decode_header

from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import Binary
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags

client = MongoClient(settings.DB_HOST, settings.DB_PORT)
db = client.prism
email_db = db.email


# Match encoded-word strings in the form =?charset?q?Hello_World?=
# Some will surrend it by " or end by , or by fucking \r
ecre = re.compile(r"""=\?([^?]*?)\?([qb])\?(.*?)\?=(?=\W|$)""",
        re.VERBOSE | re.IGNORECASE | re.MULTILINE)

img_tag = '<img border="0" hspace="0" align="baseline" src="%s" />'

class MessageParser(object):
    """We describe MIME in json, but only store leafs"""

    def from_fp(self, fp):
        msg = message_from_file(fp)
        return self.parse(msg)[0]  # root of the tree

    def from_id(self, id_str):
        return email_db.find_one({'_id': ObjectId(id_str)})

    def flatten_header(self, hdr):
        """Decode strings like =?charset?q?Hello_World?=
        and make keys lower case"""
        vanilla_hdr = {}
        def decode_match(field):
            dec_str, charset = decode_header(field.group(0))[0]
            if charset:
                dec_str = dec_str.decode(charset, 'replace')
            return dec_str

        for k, v in hdr.items():
            vanilla_hdr[k.lower()] = ecre.sub(decode_match, v)
        return vanilla_hdr

    def parse(self, msg):
        handler = 'handle_' + msg.get_content_maintype()
        if hasattr(self, handler):
            return getattr(self, handler)(msg)
        else:
            return self.handle_default(msg)

    def handle_multipart(self, msg):
        assert msg.is_multipart(), "Who send you here while you ain't multipart?"
        # Look for text/html first and then text/plain, best comes first
        alternatives = ['text/html', 'text/richtext', 'text/plain', 'message/rfc822']

        sub_msg_dicts = []
        for sub_msg in msg.get_payload():
            sub_msg_dicts.extend(self.parse(sub_msg))

        # Each of the parts is an "alternative" version of the same information.
        if msg.get_content_subtype() == 'alternative':
            for ct in alternatives:
                best = next(ifilter(lambda d: 
                    d['header'].get('content-type') == ct, sub_msg_dicts), None)
                if best:
                    sub_msg_dicts = [best]
                    break
            else:
                # Choose the first one, must be a list
                sub_msg_dicts = sub_msg_dicts[0:1]

        return sub_msg_dicts
    
    def handle_text(self, msg):
        # assert msg.get_content_maintype() == 'text'
        charset = msg.get_content_charset('gbk')  # gbk will be the default one
        txt = msg.get_payload(decode=True).decode(charset, 'replace')
        header = self.flatten_header(dict(msg.items()))
        return [{'body': txt, 'header': header}]

    # In multipart/digest the default Content-Type value for a body part 
    # is changed from "text/plain" to "message/rfc822".
    handle_message = handle_text

    # def handle_image(self, msg):
    #     assert msg.get_content_maintype() == 'image'
    #     body =  Binary(msg.get_payload(decode=True))
    #     return [{'body': body, 'header': dict(msg.items())}]

    # Mostly default means binary
    def handle_default(self, msg):
        body =  Binary(msg.get_payload(decode=True))
        return [{'body': body, 'header': self.flatten_header(msg.items())}]

parser = MessageParser()

class Email(object):
    stored_fields = ['from', 'to', 'subject']
    
    def __init__(self, d):
        assert type(d) is dict
        print '='*20, d
        self.body = d.pop('body', [])
        self._body_html = d.pop('body_html', '')
        self._body_txt = d.pop('body_txt', '')
        self.id = d.pop('_id', None)
        # All keys in lower case
        self.header = {k: d['header'].get(k) for k in self.stored_fields}

    @classmethod
    def from_fp(cls, fp):
        return cls(parser.from_fp(fp))

    @classmethod
    def from_id(cls, id_str):
        return cls(parser.from_id(id_str))

    @classmethod
    def all(cls):
        """return a list"""
        return map(cls, email_db.find())

    @property
    def body_html(self):
        if self._body_html:
            return self._body_html

        html = []
        for i, part in enumerate(self.body):
            if part['header'].get('content-type', '').startswith('text'):
                html.append(part['body'])
            elif part['header'].get('content-type', '').startswith('image'):
                # reverse will transform args to str
                html.append(img_tag % reverse('resource', args=(self.id, i)))
        self._body_html = ''.join(html)

        # self.update({'body_html': self._body_html})
        return self._body_html

    @property
    def body_txt(self):
        if self._body_txt:
            return self._body_txt
        self._body_txt = strip_tags(self.body_html)
        return self._body_txt

    def __unicode__(self):
        return self.header.get('subject', '')

    __str__ = __unicode__

    def to_dict(self):
        ed = {}
        ed['header'] = self.header.copy()
        ed['body'] = self.body
        return ed

    def save(self):
        self.id = email_db.insert(self.to_dict())  # An ObjectId
        return self.id

    def update(self, doc):
        """A atomic operation"""
        return email_db.find_and_modify({'_id': self.id}, {'$set': doc})

    @classmethod
    def remove(self, id_str):
        return email_db.remove({'_id': ObjectId(id_str)})

